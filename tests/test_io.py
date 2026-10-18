import json
import tempfile
import unittest
from pathlib import Path

from robot_release_check.io import load_project


class IoTests(unittest.TestCase):
    def _write_project(self, root: Path, verifications):
        (root / "release.json").write_text(json.dumps({
            "release_id": "v2",
            "delivered_at": "2026-10-10T16:00:00Z",
        }), encoding="utf-8")
        (root / "tests.json").write_text("[]", encoding="utf-8")
        (root / "changes.json").write_text("[]", encoding="utf-8")
        (root / "closures.json").write_text("[]", encoding="utf-8")
        (root / "verifications.json").write_text(json.dumps(verifications), encoding="utf-8")

    def test_loads_verifications_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_project(root, [{"verification_id": "V1", "release_id": "v2"}])
            _, _, _, _, verifications = load_project(root)
            self.assertEqual(verifications[0].verification_id, "V1")
            self.assertEqual(verifications[0].release_id, "v2")

    def test_duplicate_verification_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_project(root, [
                {"verification_id": "V1", "release_id": "v1"},
                {"verification_id": "V1", "release_id": "v2"},
            ])
            with self.assertRaisesRegex(ValueError, "duplicate verification_id"):
                load_project(root)


if __name__ == "__main__":
    unittest.main()
