"""Verify registration names against a loopback mock; requires CLI sign-in.

The existing remote server is left running. Authentication headers are never
logged, and registration requests are only sent to the loopback mock.
"""
import argparse
import http.server
import json
from pathlib import Path
import signal
import socket
import subprocess
import threading


def check_name(binary, arguments, expected):
    received = []
    event = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(503)
            self.end_headers()

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                payload = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                payload = {}
            if isinstance(payload, dict) and "name" in payload:
                received.append(payload["name"])
                event.set()
            self.send_response(503)
            self.end_headers()

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    override = f'chatgpt_base_url="http://127.0.0.1:{server.server_port}/backend-api/"'
    process = subprocess.Popen(
        ["sh", "-c", 'exec "$@"', "test", binary, "remote-control",
         "--no-daemon", "-c", override, *arguments],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert event.wait(30), "No enrollment request received"
        assert received[0] == expected, (received[0], expected)
        print(f"Enrollment name verified: {received[0]}")
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary", type=Path,
        default=Path(__file__).resolve().parents[2] / "codex-rs/target/dev-small/codex",
    )
    binary = str(parser.parse_args().binary.resolve())
    check_name(binary, ["--name", "  My Phone  "], "My Phone")
    check_name(binary, [], socket.gethostname().strip())
    for value in ["   ", "Phone\nOther", "Phone\n"]:
        result = subprocess.run(
            ["sh", "-c", 'exec "$@"', "test", binary, "remote-control",
             "--no-daemon", "--name", value],
            capture_output=True, text=True,
        )
        assert result.returncode == 2, (value, result.returncode)
    result = subprocess.run(
        ["sh", "-c", 'exec "$@"', "test", binary, "remote-control", "--name", "Phone"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2, "--name must require foreground mode"
    print("Invalid names and unsupported daemon naming rejected before startup")


if __name__ == "__main__":
    main()
