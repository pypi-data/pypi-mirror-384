// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
//
// SPDX-License-Identifier: GPL-2.0-or-later
//! This module provides utilities for fallbacks to the Python implementation of HGitaly.
//!
//! In other words, this module makes Pyhton HGitaly a sidecar of RHGitaly
use crate::config::{Config, ServerAddress};
use tokio::net::UnixStream;
use tokio::sync::Mutex;
use tonic::transport::{Channel, Endpoint, Error, Uri};
use tonic::Status;
use tower::service_fn;
use tracing::info;

// All necessary state
//
// At this stage, the sidecar uses a full (prefork etc) HGitaly server so the
// state is made of a single channel.
#[derive(Debug)]
pub struct Servers {
    address: ServerAddress,
    channel: Mutex<Option<Channel>>,
}

impl Servers {
    pub fn new(config: &Config) -> Self {
        Servers {
            address: config.hgitaly_sidecar_address.clone(),
            channel: None.into(),
        }
    }

    async fn open_channel(&self) -> Result<Channel, Error> {
        Ok(match &self.address {
            ServerAddress::URI(uri) => {
                info!("Connecting to sidecar URI {}", uri);

                Endpoint::try_from(uri.clone())?.connect().await?
            }
            ServerAddress::Unix(path) => {
                info!(
                    "Connecting to sidecar Unix Domain socket at {}",
                    path.display()
                );

                // we need to give the path to the closure, which itself will need
                // to clone it to avoid giving it away to `connect` (and hence being only
                // `FnOnce`)
                let p = path.clone();
                // TODO fake URL from example in tonic, we should get rid of it
                // if this code persists when `Servers` becomes a pool of managed processes.
                Endpoint::try_from("http://[::]:50051")?
                    .connect_with_connector(service_fn(move |_: Uri| {
                        UnixStream::connect(p.clone())
                    }))
                    .await?
            }
        })
    }

    pub async fn available_channel(&self) -> Result<Channel, Status> {
        let mut lock = self.channel.lock().await;
        let chan = match &*lock {
            None => {
                let chan = self.open_channel().await.map_err(|e| {
                    Status::internal(format!(
                        "Could not connect to HGitaly (Python) sidecar: {}",
                        e
                    ))
                })?;

                // Cloning channel is cheap and encouraged (see doc-comment for `Channel` struct)
                *lock = Some(chan.clone());
                chan
            }
            Some(chan) => chan.clone(),
        };
        Ok(chan)
    }
}

macro_rules! unary {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        let channel = $self
            .sidecar_servers
            .available_channel()
            .await
            .map_err(|e| {
                Status::internal(format!("Could not initiate the sidecar channel: {}", e))
            })?;
        let mut client = $client_class::new(channel);
        client.$meth($request).await
    }};
}

macro_rules! server_streaming {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        let channel = $self.sidecar_servers.available_channel().await?;
        let mut stream = $client_class::new(channel)
            .$meth($request)
            .await?
            .into_inner();
        let (tx, rx) = tokio::sync::mpsc::channel(1);
        let current_span = tracing::Span::current();

        tokio::task::spawn(async move {
            let _entered = current_span.enter();
            loop {
                match stream.message().await {
                    Ok(None) => {
                        break;
                    }
                    Err(e) => {
                        tracing::info!("Sending back error {}", &e);
                        if tx.send(Err(e)).await.is_err() {
                            // We have no other choice
                            tracing::warn!(
                                "mpsc receiver already dropped \
                                           when sending back a sidecar error "
                            );
                        }
                        break;
                    }
                    Ok(Some(resp)) => {
                        tracing::debug!("Sending back a response message");
                        if tx.send(Ok(resp)).await.is_err() {
                            // The Receiver has been dropped, which means that the request
                            // is cancelled our the client side. We have to propagate ASAP.
                            tracing::warn!(
                                "Request cancelled by our client. Finishing streaming \
                                  in order to cancel our own request to the sidecar server."
                            );
                            break;
                        }
                    }
                }
            }
        });
        Ok(Response::new(Box::pin(
            tokio_stream::wrappers::ReceiverStream::new(rx),
        )))
    }};
}

macro_rules! client_streaming {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        let channel = $self.sidecar_servers.available_channel().await.unwrap();
        let mut client = $client_class::new(channel);

        let (metadata, extensions, inner) = $request.into_parts();
        let (tx, mut rx) = tokio::sync::mpsc::channel(1);
        let _keeping_open = tx.clone();

        let transmit = inner
            .filter(move |req| match req {
                Err(e) => {
                    let tx = tx.clone();
                    let e = e.clone();
                    tracing::info!("Got client stream error {}", e);
                    tokio::task::spawn(async move {
                        if tx.send(e).await.is_err() {
                            // We have no other choice
                            tracing::warn!(
                                "mpsc receiver already dropped when sending back \
                                  an error streaming client request"
                            );
                        }
                    });
                    false
                }
                _ => true,
            })
            .map(|res| res.expect("Error cases should already have been filtered out"));

        tokio::select! {
          err = rx.recv() => {
             Err(err.unwrap_or_else(
               || Status::internal("Unexpected closing of inner channel for errors")))
          },
          resp = client.$meth(tonic::Request::from_parts(metadata, extensions, transmit)) => {
             resp
          }
        }
    }};
}

macro_rules! fallback {
    ($fallback_macro:ident, $self:ident, $inner_meth:ident,
     $request:ident, $client_class:ident, $meth:ident) => {{
        let (metadata, extensions, inner) = $request.into_parts();

        let corr_id = correlation_id(&metadata);
        let result = $self.$inner_meth(&inner, corr_id, &metadata).await;
        if let Err(status) = result {
            if status.code() != tonic::Code::Unimplemented {
                return Err(status);
            } else {
                let mut details = status.message();
                if details.is_empty() {
                    details = "no details";
                }
                tracing::info!(
                    "Falling back to sidecar, correlation_id={:?}, method={}, \
                     reason: not implemented in Rust ({})",
                    corr_id,
                    stringify!($meth),
                    details,
                );
                let request = Request::from_parts(metadata, extensions, inner);
                crate::sidecar::$fallback_macro!($self, request, $client_class, $meth)
            }
        } else {
            result
        }
    }};
}

macro_rules! fallback_unary {
    ($($args:ident),*) => { crate::sidecar::fallback!(unary $(,$args)*) };
}

macro_rules! fallback_server_streaming {
    ($($args:ident),*) => { crate::sidecar::fallback!(server_streaming $(,$args)*) };
}

// TODO fallback_client_streaming

// make visible to other modules
pub(crate) use {
    client_streaming, fallback, fallback_server_streaming, fallback_unary, server_streaming, unary,
};
