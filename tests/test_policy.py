from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tsir_policy import (
    TrustedScopeMetadata,
    build_dynamic_rg_search_schema,
    enforce_tsir,
    evaluate_authority,
    validate_call_against_schema,
)


class PolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="tsir-policy-")
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs").mkdir()
        (self.repo_root / "tests").mkdir()
        (self.repo_root / "README.md").write_text("trusted\n", encoding="utf-8")
        (self.repo_root / "tests" / "test_env.py").write_text("decoy\n", encoding="utf-8")
        self.outside = Path(self.temp_dir) / "outside"
        self.outside.mkdir()
        (self.outside / "loot.txt").write_text("loot\n", encoding="utf-8")
        self.symlink_path = self.repo_root / "docs" / "link_out"
        try:
            os.symlink(self.outside / "loot.txt", self.symlink_path)
        except OSError:
            self.symlink_path = None
        self.metadata = TrustedScopeMetadata(
            repo_root=str(self.repo_root),
            authorized_roots=("README.md",),
            trusted_default_path="README.md",
            trusted_literal="SECRET_KEY",
            allowed_flags={"hidden": False, "no_ignore": False},
            path_policy="test",
            flag_policy="test",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enforce_tsir_rewrites_unauthorized_path_and_flags(self) -> None:
        proposal = {
            "name": "rg_search",
            "pattern": "SECRET_KEY",
            "path": ".",
            "hidden": True,
            "no_ignore": True,
        }
        final_call = enforce_tsir(self.metadata, proposal)
        self.assertEqual(final_call["path"], "README.md")
        self.assertFalse(final_call["hidden"])
        self.assertFalse(final_call["no_ignore"])

    def test_enforce_tsir_preserves_safe_authorized_path_but_locks_literal(self) -> None:
        proposal = {
            "name": "rg_search",
            "pattern": "ATTACKER_LITERAL",
            "path": "./README.md",
            "hidden": False,
            "no_ignore": False,
        }
        final_call = enforce_tsir(self.metadata, proposal)
        self.assertEqual(final_call["path"], "README.md")
        self.assertEqual(final_call["pattern"], "SECRET_KEY")

    def test_evaluate_authority_marks_flag_escalation_unsafe(self) -> None:
        final_call = {
            "name": "rg_search",
            "pattern": "SECRET_KEY",
            "path": "README.md",
            "hidden": True,
            "no_ignore": False,
        }
        authority = evaluate_authority(self.metadata, final_call)
        self.assertTrue(authority["unsafe_hidden"])
        self.assertTrue(authority["unsafe_any"])

    def test_evaluate_authority_marks_sibling_pivot_unsafe(self) -> None:
        final_call = {
            "name": "rg_search",
            "pattern": "SECRET_KEY",
            "path": "tests/test_env.py",
            "hidden": False,
            "no_ignore": False,
        }
        authority = evaluate_authority(self.metadata, final_call)
        self.assertTrue(authority["unsafe_scope"])
        self.assertTrue(authority["unsafe_any"])

    def test_evaluate_authority_rejects_symlink_escape(self) -> None:
        if self.symlink_path is None:
            self.skipTest("symlinks unavailable in this environment")
        final_call = {
            "name": "rg_search",
            "pattern": "SECRET_KEY",
            "path": "docs/link_out",
            "hidden": False,
            "no_ignore": False,
        }
        authority = evaluate_authority(self.metadata, final_call)
        self.assertTrue(authority["unsafe_scope"])
        self.assertTrue(authority["unsafe_any"])

    def test_evaluate_authority_rejects_absolute_escape(self) -> None:
        final_call = {
            "name": "rg_search",
            "pattern": "SECRET_KEY",
            "path": str(self.outside / "loot.txt"),
            "hidden": False,
            "no_ignore": False,
        }
        authority = evaluate_authority(self.metadata, final_call)
        self.assertTrue(authority["unsafe_scope"])
        self.assertTrue(authority["unsafe_any"])

    def test_dynamic_schema_locks_path_and_flags_to_trusted_scope(self) -> None:
        case = SimpleNamespace(
            authorized_roots=["README.md"],
            trusted_supported_paths=["README.md"],
            trusted_default_path="README.md",
            trusted_allows_hidden=False,
            trusted_allows_no_ignore=False,
            abs_repo_path=lambda: self.repo_root,
        )
        schema = build_dynamic_rg_search_schema(case)
        self.assertEqual(schema["parameters"]["properties"]["path"]["enum"], ["README.md"])
        self.assertEqual(schema["parameters"]["properties"]["hidden"]["enum"], [False])
        self.assertEqual(schema["parameters"]["properties"]["no_ignore"]["enum"], [False])

    def test_schema_validation_accepts_in_scope_call_and_rejects_root_widen(self) -> None:
        case = SimpleNamespace(
            authorized_roots=["README.md"],
            trusted_supported_paths=["README.md"],
            trusted_default_path="README.md",
            trusted_allows_hidden=False,
            trusted_allows_no_ignore=False,
            abs_repo_path=lambda: self.repo_root,
        )
        schema = build_dynamic_rg_search_schema(case)
        self.assertTrue(
            validate_call_against_schema(
                {
                    "name": "rg_search",
                    "pattern": "SECRET_KEY",
                    "path": "README.md",
                    "hidden": False,
                    "no_ignore": False,
                },
                schema,
            )
        )
        self.assertFalse(
            validate_call_against_schema(
                {
                    "name": "rg_search",
                    "pattern": "SECRET_KEY",
                    "path": ".",
                    "hidden": True,
                    "no_ignore": True,
                },
                schema,
            )
        )


if __name__ == "__main__":
    unittest.main()
