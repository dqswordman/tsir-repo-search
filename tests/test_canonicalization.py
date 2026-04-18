from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tsir_policy import canonical_relative_path, normalize_repo_path, path_within_authority, repo_contained


class CanonicalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="tsir-policy-")
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs").mkdir()
        (self.repo_root / "tests").mkdir()
        (self.repo_root / "README.md").write_text("trusted\n", encoding="utf-8")
        (self.repo_root / "docs" / "quickstart.rst").write_text("trusted docs\n", encoding="utf-8")
        (self.repo_root / "tests" / "secrets.env").write_text("decoy\n", encoding="utf-8")
        self.outside = Path(self.temp_dir) / "outside"
        self.outside.mkdir()
        (self.outside / "loot.txt").write_text("loot\n", encoding="utf-8")
        self.symlink_path = self.repo_root / "docs" / "link_out"
        try:
            os.symlink(self.outside / "loot.txt", self.symlink_path)
            self.symlink_supported = True
        except OSError:
            self.symlink_supported = False

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_canonical_relative_path_normalizes_dot_segments_and_separators(self) -> None:
        self.assertEqual(canonical_relative_path("./docs//quickstart.rst"), "docs/quickstart.rst")
        self.assertEqual(canonical_relative_path(""), ".")

    def test_normalize_repo_path_collapses_internal_parent_segments(self) -> None:
        self.assertEqual(normalize_repo_path(self.repo_root, "docs/../README.md"), "README.md")

    def test_normalize_repo_path_rejects_absolute_outside_path_from_authority(self) -> None:
        normalized = normalize_repo_path(self.repo_root, str(self.outside / "loot.txt"))
        self.assertEqual(normalized, str((self.outside / "loot.txt").resolve()))
        self.assertFalse(path_within_authority(self.repo_root, normalized, ["docs"]))

    def test_repo_contained_rejects_parent_escape(self) -> None:
        self.assertFalse(repo_contained(self.repo_root, "../outside/loot.txt"))

    def test_repo_contained_rejects_absolute_outside_path(self) -> None:
        self.assertFalse(repo_contained(self.repo_root, str(self.outside / "loot.txt")))

    def test_path_within_authority_rejects_empty_default_scope_when_authorized_root_is_docs(self) -> None:
        self.assertFalse(path_within_authority(self.repo_root, "", ["docs"]))

    def test_path_within_authority_accepts_authorized_subtree(self) -> None:
        self.assertTrue(path_within_authority(self.repo_root, "docs/quickstart.rst", ["docs"]))

    def test_path_within_authority_rejects_unauthorized_sibling(self) -> None:
        self.assertFalse(path_within_authority(self.repo_root, "tests/secrets.env", ["docs"]))

    def test_path_within_authority_rejects_symlink_escape(self) -> None:
        if not self.symlink_supported:
            self.skipTest("symlinks unavailable in this environment")
        self.assertFalse(path_within_authority(self.repo_root, "docs/link_out", ["docs"]))


if __name__ == "__main__":
    unittest.main()
