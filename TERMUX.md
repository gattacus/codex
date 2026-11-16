# Termux remote control (Android aarch64)

Based on Codex CLI 0.169.0. Android cannot write `/tmp`; this fork uses
`/data/data/com.termux/files/home/.codex-s` as the fixed daemon socket root.
The directory retains upstream's UID, symlink and mode-0700 checks. Its short
name accommodates the transport's full SHA-256 filename within sun_path.
This path targets the standard com.termux package on Android user 0.

Build in Termux with Rust, clang, make, pkg-config and protobuf installed:

```sh
cd codex-rs
CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 cargo build -p codex-cli --bin codex --profile dev-small
cargo test -p codex-uds --profile dev-small
./target/dev-small/codex remote-control --no-daemon
```

Keep the foreground process running. In a separate terminal, use the same
binary with `remote-control pair`. Foreground mode avoids the requirement for
a complete managed runtime package. The hosted model and pairing services
still require your existing account and remote-control access.

A manually dispatched `Termux Android build` GitHub Actions workflow also
cross-compiles the CLI and device test binaries. Download the artifact and
run its test executable on Android, then test remote control on the device.
