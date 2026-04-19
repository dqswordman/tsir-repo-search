#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "artifacts" / "stage6_combined_claim_package"
DEST_DIFF = ROOT / "paper" / "latex" / "stage6_diff_rows.tex"
DEST_SCOPE = ROOT / "paper" / "latex" / "stage6_scope_rows.tex"


REPO_CODE = {
    "controlled_repo": "ctrl",
    "pyaml_env": "pyaml",
    "environs": "envns",
    "python_decouple": "decpl",
    "dynaconf": "dynac",
    "pydantic_settings": "pydst",
    "django_configurations": "djcfg",
    "python_dotenv": "pydot",
    "configargparse": "cfgap",
}

FAMILY_CODE = {
    "root_widen_hidden": "root+flags",
    "sibling_path_pivot": "sib. pivot",
    "parent_escape": "parent esc.",
}


def family_for_row(row: dict[str, Any]) -> str:
    case_id = row.get("case_id", "")
    pair_id = row.get("pair_id", "")
    if "_parent_escape_" in case_id or pair_id.endswith("_parent_escape"):
        return "parent_escape"
    return row["family"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def shorten_path(path_value: str) -> str:
    if path_value == ".":
        return "."
    if path_value.startswith("tests_functional/"):
        return "tests_functional/..."
    if path_value.startswith("tests/"):
        return "tests/..."
    if path_value.startswith("docs/"):
        return path_value
    if path_value.startswith("README"):
        return path_value
    if path_value.startswith("../"):
        return "../escape..."
    if len(path_value) > 24:
        head = path_value.split("/")[0]
        tail = path_value.split("/")[-1]
        return f"{head}/.../{tail}"
    return path_value


def compact_call(call: dict[str, Any] | None) -> str:
    if call is None:
        return r"\textit{no call}"
    path = shorten_path(str(call["path"]))
    flags: list[str] = []
    if bool(call.get("hidden")):
        flags.append("hid")
    if bool(call.get("no_ignore")):
        flags.append("ign")
    if flags:
        return rf"\fpath{{{path}}}; {'+'.join(flags)}"
    return rf"\fpath{{{path}}}; flags off"


def render() -> None:
    manifest = load_json(SOURCE_ROOT / "case_manifest.json")
    results = load_json(SOURCE_ROOT / "results.json")
    base_prompt_by_case = {row["case_id"]: row["proposal"] for row in results if row["variant"] == "base_prompt"}
    tsir_by_case = {row["case_id"]: row["final_call"] for row in results if row["variant"] == "tsir_route_b"}

    attack_rows = [row for row in manifest if row["is_attack"]]
    diff_lines = []
    for idx, row in enumerate(attack_rows, start=1):
        case_code = f"A{idx:02d}"
        repo = REPO_CODE[row["repo_name"]]
        family = FAMILY_CODE[family_for_row(row)]
        proposal = compact_call(base_prompt_by_case.get(row["case_id"]))
        final_call = compact_call(tsir_by_case.get(row["case_id"]))
        expected_hit = rf"\fpath{{{shorten_path(row['expected_hit_path'])}}}"
        diff_lines.append(
            f"{case_code} & {family} & {repo} & {proposal} & {final_call} & {expected_hit} \\tabularnewline"
        )

    seen_pairs: set[str] = set()
    scope_lines = []
    pair_index = 1
    for row in manifest:
        if row["pair_id"] in seen_pairs:
            continue
        seen_pairs.add(row["pair_id"])
        pair_code = f"P{pair_index:02d}"
        pair_index += 1
        repo = REPO_CODE[row["repo_name"]]
        family = FAMILY_CODE[family_for_row(row)]
        roots = ", ".join(rf"\fpath{{{shorten_path(root)}}}" for root in row["authorized_roots"])
        default_path = rf"\fpath{{{shorten_path(row['trusted_default_path'])}}}"
        expected_hit = rf"\fpath{{{shorten_path(row['expected_hit_path'])}}}"
        scope_lines.append(
            f"{pair_code} & {family} & {repo} & {roots} & {default_path} & {expected_hit} \\tabularnewline"
        )

    DEST_DIFF.write_text("\n".join(diff_lines + [r"\bottomrule"]) + "\n", encoding="utf-8")
    DEST_SCOPE.write_text("\n".join(scope_lines + [r"\bottomrule"]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    render()
