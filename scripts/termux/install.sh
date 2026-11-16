#!/data/data/com.termux/files/usr/bin/sh
# Install a CLI together with the native code-mode helper it needs at runtime.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -x "$script_dir/codex" ]; then
    binary="$script_dir/codex"
else
    binary="$script_dir/../../codex-rs/target/dev-small/codex"
fi
bin_dir="${HOME:?}/.local/bin"
helper=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --binary|--bin-dir|--helper)
            [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
            case "$1" in
                --binary) binary=$2 ;;
                --bin-dir) bin_dir=$2 ;;
                --helper) helper=$2 ;;
            esac
            shift 2 ;;
        *) echo "Usage: sh install.sh [--binary FILE] [--helper FILE] [--bin-dir DIR]" >&2; exit 2 ;;
    esac
done
[ -x "$binary" ] || { echo "CLI binary is missing or not executable: $binary" >&2; exit 1; }
if [ -z "$helper" ]; then
    if [ -x "$bin_dir/codex-code-mode-host" ]; then
        helper="$bin_dir/codex-code-mode-host"
    elif command -v codex-code-mode-host >/dev/null 2>&1; then
        helper=$(command -v codex-code-mode-host)
    elif [ -x "${PREFIX:-/data/data/com.termux/files/usr}/bin/codex-code-mode-host" ]; then
        helper="${PREFIX:-/data/data/com.termux/files/usr}/bin/codex-code-mode-host"
    fi
fi
[ -n "$helper" ] && [ -f "$helper" ] && [ -x "$helper" ] || {
    echo "Native codex-code-mode-host is required. Pass --helper /path/to/codex-code-mode-host; CLI was not installed." >&2
    exit 1
}
helper=$(realpath "$helper")
mkdir -p "$bin_dir"
# Preserve an existing working helper. Refuse to overwrite a regular file.
if [ -e "$bin_dir/codex-code-mode-host" ] && [ ! -L "$bin_dir/codex-code-mode-host" ]; then
    [ "$(realpath "$bin_dir/codex-code-mode-host")" = "$helper" ] || {
        echo "Refusing to overwrite an existing helper file" >&2; exit 1;
    }
else
    ln -s "$helper" "$bin_dir/.codex-code-mode-host.$$"
    mv -f "$bin_dir/.codex-code-mode-host.$$" "$bin_dir/codex-code-mode-host"
fi
staged=$(mktemp "$bin_dir/.codex-termux.XXXXXX")
trap 'rm -f "$staged"' EXIT HUP INT TERM
cp "$binary" "$staged"
chmod 700 "$staged"
mv -f "$staged" "$bin_dir/codex-termux"
printf 'Installed %s with helper %s\n' "$bin_dir/codex-termux" "$helper"
