# Termux remote control (Android aarch64)

Based on Codex CLI 0.169.0. Android cannot write `/tmp`; this fork uses
`/data/data/com.termux/files/home/.codex-s` as the fixed daemon socket root.
The directory retains upstream's UID, symlink and mode-0700 checks. Its short
name accommodates the transport's full SHA-256 filename within sun_path.
This path targets the standard com.termux package on Android user 0.

Use Rust 1.99.1 or later for Android file-lock support.
Install the native build tools in Termux:

```sh
pkg install rust clang make pkg-config protobuf cmake
```

Build in a dedicated checkout:

```sh
cd codex-rs
OPENSSL_NO_VENDOR=1 OPENSSL_DIR="$PREFIX" CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 sh ../scripts/termux/cargo.sh build -p codex-cli --bin codex --profile dev-small
sh ../scripts/termux/cargo.sh test -p codex-uds --profile dev-small
sh ../scripts/termux/install.sh
~/.local/bin/codex-termux remote-control --no-daemon --pair --name "My Phone"
```

Keep the foreground process running and enter its printed pairing code in the
remote app. The `--pair` flag uses the foreground socket directly; upstream
`remote-control pair` only discovers a daemon socket. Foreground mode avoids
the requirement for
a complete managed runtime package. The hosted model and pairing services
still require your existing account and remote-control access.

A manually dispatched `Termux Android build` GitHub Actions workflow also
cross-compiles the CLI and device test binaries. Download the artifact and
run its test executable on Android, then test remote control on the device.

The build wrapper temporarily excludes the separate V8 host/runtime workspace
members and their Git patch, then restores Cargo.toml and Cargo.lock on exit.
This avoids downloading Chromium for the CLI, which does not link that host.
The separate V8 code-mode host is not rebuilt in this Android artifact.
The installer locates an existing native `codex-code-mode-host` (beside the
installed CLI, on PATH, or in `$PREFIX/bin`) and installs an adjacent symlink.
It refuses to install the CLI if no executable helper is available. An explicit
helper can be supplied with `--helper /path/to/codex-code-mode-host`.
For a downloaded CLI use `--binary /path/to/codex` with the same installer.

`--name "My Phone"` changes the name advertised to the remote app for this
foreground server. Omit it to use the hostname. It requires `--no-daemon`;
blank names and control characters are rejected. Restart the foreground server
to change its name. Reconnect or refresh the remote app to see the new name.

## Validation on the Android device (2026-11-16)

- Native aarch64 Android CLI built successfully with Rust 1.99.1.
- All 8 `codex-uds` tests passed, including private-directory checks, a full
  SHA-256 socket pathname bind, and client/server data exchange.
- Installed CLI startup succeeded with `remote-control --no-daemon --pair`:
  the relay reported the machine available and returned a manual pairing code.
- `--pair` without `--no-daemon` correctly fails argument validation.
- Account connectivity and database checks passed in `codex doctor`.

The validated native executable is installed beside the original CLI at
`~/.local/bin/codex-termux`. Start it in your own Termux terminal:

```sh
~/.local/bin/codex-termux remote-control --no-daemon --pair --name "My Phone"
```

Enter the printed short-lived code in the remote app and keep this process
running. Press Ctrl-C to stop it. Completing the connection in the remote app
requires the user to enter the code; that UI step was not automated.
