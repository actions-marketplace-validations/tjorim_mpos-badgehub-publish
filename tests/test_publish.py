import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixture-app")
SCRIPT = os.path.join(ROOT, "publish.py")

sys.path.insert(0, ROOT)
import publish  # noqa: E402


class QuotePathTests(unittest.TestCase):
    def test_subdirectory_slash_is_percent_encoded(self):
        # A raw "/" in the URL splits BadgeHub's single-segment {filePath}
        # route param into an extra unmatched segment (404 "Cannot POST") --
        # this is what actually broke the first real (non-dry-run) publish.
        self.assertEqual(publish.quote_path("sounds/BombDrop.wav"), "sounds%2FBombDrop.wav")

    def test_flat_filename_is_unchanged(self):
        self.assertEqual(publish.quote_path("MANIFEST.JSON"), "MANIFEST.JSON")


class PublishDryRunTests(unittest.TestCase):
    def _run(self, extra_env=None):
        env = os.environ.copy()
        env.update(
            {
                "BADGEHUB_API_BASE": "https://badgehub.eu/api/v3",
                "BADGEHUB_SLUG": "fixture-app",
                "BADGEHUB_API_TOKEN": "test-token",
                "BADGEHUB_APP_DIR": FIXTURE,
                "BADGEHUB_DRY_RUN": "true",
            }
        )
        if extra_env:
            env.update(extra_env)
        return subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True, env=env)

    def test_dry_run_succeeds_and_uploads_expected_files(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MANIFEST.JSON", result.stdout)
        self.assertIn("fixture_app.py", result.stdout)
        self.assertIn("Published 'fixture-app'", result.stdout)

    def test_dry_run_logs_subdirectory_files_percent_encoded(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uploaded sounds/beep.txt", result.stdout)
        self.assertIn("draft/files/sounds%2Fbeep.txt", result.stdout)

    def test_dry_run_never_touches_the_network(self):
        # An unresolvable host would fail immediately on any real request,
        # so this only passes if dry-run truly never attempts one.
        result = self._run({"BADGEHUB_API_BASE": "https://this-host-does-not-exist.invalid/api/v3"})
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
