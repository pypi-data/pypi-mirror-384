// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::sync::Arc;

use tonic::{Request, Response, Status};
use tracing::{info, instrument};

use crate::gitaly::server_service_client::ServerServiceClient;
use crate::gitaly::server_service_server::{ServerService, ServerServiceServer};
use crate::gitaly::{
    ServerInfoRequest, ServerInfoResponse, ServerSignatureRequest, ServerSignatureResponse,
};
use crate::sidecar;
use crate::util::tracing_span_id;

build_const!("constants");

#[derive(Debug)]
pub struct ServerServiceImpl {
    sidecar_servers: Arc<sidecar::Servers>,
}

#[tonic::async_trait]
impl ServerService for ServerServiceImpl {
    #[instrument(name = "server_info", skip(self, request))]
    async fn server_info(
        &self,
        request: Request<ServerInfoRequest>,
    ) -> Result<Response<ServerInfoResponse>, Status> {
        tracing_span_id!();
        info!("Processing request=ServerInfoRequest");
        sidecar::unary!(self, request, ServerServiceClient, server_info)
    }

    /// Gitaly's signing key path configuration is optional (defaults to
    /// empty string, see  `gitaly.toml.example`). We return the same value
    /// as Gitaly does in that case, since Mercurial signing is currently
    /// not implemented.
    #[instrument(name = "server_signature", skip(self, _request))]
    async fn server_signature(
        &self,
        _request: Request<ServerSignatureRequest>,
    ) -> Result<Response<ServerSignatureResponse>, Status> {
        tracing_span_id!();
        info!("Processing");
        Ok(Response::new(ServerSignatureResponse::default()))
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn server_server(
    sidecar_servers: &Arc<sidecar::Servers>,
) -> ServerServiceServer<ServerServiceImpl> {
    ServerServiceServer::new(ServerServiceImpl {
        sidecar_servers: sidecar_servers.clone(),
    })
}
