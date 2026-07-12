import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixture-app")
SCRIPT = os.path.join(ROOT, "publish.py")


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

    def test_dry_run_never_touches_the_network(self):
        # An unresolvable host would fail immediately on any real request,
        # so this only passes if dry-run truly never attempts one.
        result = self._run({"BADGEHUB_API_BASE": "https://this-host-does-not-exist.invalid/api/v3"})
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
