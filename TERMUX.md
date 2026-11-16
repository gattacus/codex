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
./target/dev-small/codex remote-control --no-daemon --pair
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
The optional V8 code-mode host is not included in this Android artifact.
