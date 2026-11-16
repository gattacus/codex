"""Exercise installer behavior with executable fixtures, without a real install."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("install.sh")

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.executable("build/codex", "cli")
        self.dest = self.root / "install with spaces"

    def executable(self, name, output):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'#!/bin/sh\nprintf "%s\\n" "{output}"\n')
        path.chmod(0o700)
        return path

    def run_install(self, *args, env=None):
        return subprocess.run(["sh", str(SCRIPT), "--binary", str(self.binary),
                               "--bin-dir", str(self.dest), *map(str, args)],
                              env=env, capture_output=True, text=True)

    def test_installs_binary_and_adjacent_helper_with_spaces(self):
        helper = self.executable("native helper/codex-code-mode-host", "host")
        result = self.run_install("--helper", helper)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / "codex-termux").read_bytes(), self.binary.read_bytes())
        self.assertEqual((self.dest / "codex-code-mode-host").resolve(), helper)
        self.assertTrue(os.access(self.dest / "codex-code-mode-host", os.X_OK))

    def test_missing_helper_does_not_install_or_replace_cli(self):
        self.dest.mkdir()
        original = self.dest / "codex-termux"
        original.write_text("existing CLI")
        result = self.run_install("--helper", self.root / "missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLI was not installed", result.stderr)
        self.assertEqual(original.read_text(), "existing CLI")

    def test_discovers_native_helper_on_path(self):
        helper = self.executable("path/codex-code-mode-host", "host")
        env = dict(os.environ, PATH=f'{helper.parent}:{os.environ["PATH"]}')
        result = self.run_install(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / "codex-code-mode-host").resolve(), helper)

    def test_repeated_install_preserves_working_helper(self):
        helper = self.executable("native/codex-code-mode-host", "host")
        self.assertEqual(self.run_install("--helper", helper).returncode, 0)
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / "codex-code-mode-host").resolve(), helper)

    def test_packaged_installer_finds_adjacent_cli(self):
        package = self.root / "package"
        package.mkdir()
        installer = package / "install.sh"
        installer.write_text(SCRIPT.read_text())
        binary = self.executable("package/codex", "packaged cli")
        helper = self.executable("native/helper", "host")
        result = subprocess.run(["sh", str(installer), "--bin-dir", str(self.dest),
                                 "--helper", str(helper)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / "codex-termux").read_bytes(), binary.read_bytes())

    def test_regular_helper_is_not_overwritten(self):
        original = self.executable("install with spaces/codex-code-mode-host", "original")
        other = self.executable("other/helper", "other")
        result = self.run_install("--helper", other)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(original.is_symlink())
        self.assertIn("original", original.read_text())

if __name__ == "__main__":
    unittest.main()
