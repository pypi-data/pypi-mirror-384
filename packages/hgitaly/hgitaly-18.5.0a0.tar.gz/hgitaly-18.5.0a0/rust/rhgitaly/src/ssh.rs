use std::ffi::OsString;
use std::fs::Permissions;
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;

use tempfile::{self, TempDir};
use tokio::fs::OpenOptions;
use tokio::io::AsyncWriteExt;

use crate::hgitaly::MercurialPeer;

pub struct SSHOptions {
    tmpdir: Option<TempDir>,
    ssh_key_file: Option<PathBuf>,
    ssh_known_hosts_file: Option<PathBuf>,
}

impl SSHOptions {
    /// Create from the gRPC message.
    pub async fn hg_new(grpc: &MercurialPeer) -> std::io::Result<Self> {
        Self::new(&grpc.ssh_key, &grpc.ssh_known_hosts).await
    }

    /// Create from key and known hosts string slices.
    pub async fn new(ssh_key: &str, ssh_known_hosts: &str) -> std::io::Result<Self> {
        let tmpdir = if !ssh_key.is_empty() || !ssh_known_hosts.is_empty() {
            let res: std::io::Result<_> = tokio::task::spawn_blocking(move || {
                let tmpdir = TempDir::new()?;
                std::fs::set_permissions(tmpdir.path(), Permissions::from_mode(0o700))?;
                Ok(tmpdir)
            })
            .await?;
            Some(res?)
        } else {
            None
        };

        let ssh_key_file = if ssh_key.is_empty() {
            None
        } else {
            Some(Self::create_secure_file(&tmpdir, "id", ssh_key).await?)
        };

        let ssh_known_hosts_file = if ssh_known_hosts.is_empty() {
            None
        } else {
            Some(Self::create_secure_file(&tmpdir, "known_hosts", ssh_known_hosts).await?)
        };

        Ok(Self {
            tmpdir,
            ssh_key_file,
            ssh_known_hosts_file,
        })
    }

    async fn create_secure_file(
        tmpdir: &Option<TempDir>,
        name: &str,
        content: &str,
    ) -> std::io::Result<PathBuf> {
        let path = tmpdir
            .as_ref()
            .expect("tmpdir should have been created")
            .path()
            .join(name);
        OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(0o600)
            .open(&path)
            .await?
            .write_all(content.as_bytes())
            .await?;
        Ok(path)
    }

    pub fn ssh_command(&self) -> OsString {
        let mut cmd: OsString = "ssh -o StrictHostKeyChecking=yes".into();
        if let Some(keyf) = &self.ssh_key_file {
            cmd.push(" -o IdentitiesOnly=yes -i ");
            cmd.push(keyf);
        }
        if let Some(knownf) = &self.ssh_known_hosts_file {
            cmd.push(" -o UserKnownHostsFile=");
            cmd.push(knownf);
        }
        cmd
    }

    /// Remove any temporary files and destroy self (blocking).
    ///
    /// As the inner closing is blocking, it is best to control it ourselves that to let it
    /// happen on drop.
    pub async fn close(self) -> std::io::Result<()> {
        if let Some(tmpdir) = self.tmpdir {
            tokio::task::spawn_blocking(move || tmpdir.close()).await??;
        }
        Ok(())
    }
}
