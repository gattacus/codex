//! The host-local rendezvous root for privileged app-server RPC sockets.
//!
//! Every listener uses this root, which sandboxes hide even before a daemon
//! starts. It must not depend on HOME, TMPDIR, CODEX_HOME, or command settings.

use std::fs;
use std::io;
use std::os::unix::fs::DirBuilderExt;
use std::os::unix::fs::MetadataExt;
use std::path::PathBuf;

/// Returns the fixed executor-local directory that every sandbox must hide.
pub fn shared_daemon_socket_directory() -> io::Result<PathBuf> {
    #[cfg(target_os = "android")]
    {
        // Termux cannot write Android's /tmp. Use a fixed app-private root,
        // independent of HOME/TMPDIR, so listeners and sandboxes agree. Keep
        // room for the transport's 64-byte SHA-256 name in sun_path.
        Ok(PathBuf::from("/data/data/com.termux/files/home/.codex-s"))
    }
    #[cfg(not(target_os = "android"))]
    {
        // Resolve the system alias /tmp -> /private/tmp on macOS.
        let temporary_root = fs::canonicalize("/tmp")?;
        let uid = unsafe { libc::geteuid() };
        Ok(temporary_root.join(format!("codex-daemon-{uid}")))
    }
}

/// Creates the reserved directory, rejecting symlinks and unsafe existing owners or modes.
pub fn prepare_shared_daemon_socket_directory() -> io::Result<PathBuf> {
    let directory = shared_daemon_socket_directory()?;
    prepare_directory(&directory)?;
    Ok(directory)
}

fn prepare_directory(directory: &std::path::Path) -> io::Result<()> {
    match fs::DirBuilder::new().mode(0o700).create(&directory) {
        Ok(()) => {}
        Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
        Err(error) => return Err(error),
    }
    let metadata = fs::symlink_metadata(&directory)?;
    if !metadata.is_dir()
        || metadata.uid() != unsafe { libc::geteuid() }
        || metadata.mode() & 0o777 != 0o700
    {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "app-server socket directory must be a user-owned directory with mode 0700",
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn creates_private_directory_and_accepts_reuse() -> io::Result<()> {
        let parent = tempfile::tempdir()?;
        let directory = parent.path().join("sockets");
        prepare_directory(&directory)?;
        prepare_directory(&directory)?;
        assert_eq!(fs::metadata(directory)?.mode() & 0o777, 0o700);
        Ok(())
    }

    #[test]
    fn rejects_symlinks_and_non_private_directories() -> io::Result<()> {
        let parent = tempfile::tempdir()?;
        let directory = parent.path().join("sockets");
        fs::create_dir(&directory)?;
        fs::set_permissions(&directory, fs::Permissions::from_mode(0o755))?;
        assert_eq!(
            prepare_directory(&directory).unwrap_err().kind(),
            io::ErrorKind::PermissionDenied
        );
        let link = parent.path().join("link");
        fs::set_permissions(&directory, fs::Permissions::from_mode(0o700))?;
        std::os::unix::fs::symlink(&directory, &link)?;
        assert_eq!(
            prepare_directory(&link).unwrap_err().kind(),
            io::ErrorKind::PermissionDenied
        );
        Ok(())
    }

    #[cfg(target_os = "android")]
    #[test]
    fn android_socket_path_fits_and_binds() -> io::Result<()> {
        use std::os::unix::ffi::OsStrExt;
        let root = prepare_shared_daemon_socket_directory()?;
        let path = root.join("a".repeat(64));
        let address: libc::sockaddr_un = unsafe { std::mem::zeroed() };
        assert!(path.as_os_str().as_bytes().len() < address.sun_path.len());
        // Bind the full production-length path, not just a shorter test name.
        let listener = std::os::unix::net::UnixListener::bind(&path)?;
        drop(listener);
        fs::remove_file(path)?;
        Ok(())
    }
}
