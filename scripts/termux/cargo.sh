#!/data/data/com.termux/files/usr/bin/sh
# Run from codex-rs in a dedicated build checkout; restore both manifests on exit.
set -eu
backup=$(mktemp -d)
cp Cargo.toml "$backup/Cargo.toml"
cp Cargo.lock "$backup/Cargo.lock"
trap 'cp "$backup/Cargo.toml" Cargo.toml; cp "$backup/Cargo.lock" Cargo.lock; rm -rf "$backup"' EXIT HUP INT TERM
python3 - <<'PY'
from pathlib import Path
p = Path('Cargo.toml')
s = p.read_text()
# The CLI talks to the V8 host out of process; it does not link V8. Avoid
# fetching the entire Chromium tree merely to resolve unrelated workspace members.
for member in ('code-mode-host', 'code-mode-runtime', 'v8-poc'):
    s = s.replace(f'    "{member}",\n', '')
s = '\n'.join(line for line in s.split('\n') if not line.startswith('v8 = { git ='))
p.write_text(s)
PY
if [ "$(uname -o)" = Android ] && command -v protoc >/dev/null 2>&1; then
    export PROTOC="$(command -v protoc)"
fi
cargo "$@"
