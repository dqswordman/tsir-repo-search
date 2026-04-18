#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from run_prelock_suite import Case, ROOT
from tsir_policy import TrustedScopeMetadata, canonical_relative_path, evaluate_authority


PRIMARY_FAMILIES = ("root_widen_hidden", "sibling_path_pivot", "parent_escape")
SOURCE_ROOT = ROOT / "artifacts" / "stage5_family_expansion"
DEST_ROOT = ROOT / "artifacts" / "stage5_claim_package"
TABLES_ROOT = ROOT / "tables"
REPORTS_ROOT = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_to_case(row: dict[str, Any]) -> Case:
    payload = dict(row)
    payload.pop("family", None)
    return Case(**payload)


def build_metadata(case: Case) -> TrustedScopeMetadata:
    return TrustedScopeMetadata(
        repo_root=str(case.abs_repo_path()),
        authorized_roots=tuple(canonical_relative_path(root) for root in case.authorized_roots),
        trusted_default_path=canonical_relative_path(case.trusted_default_path),
        trusted_literal=case.expected_literal,
        allowed_flags={
            "hidden": bool(case.trusted_allows_hidden),
            "no_ignore": bool(case.trusted_allows_no_ignore),
        },
        path_policy=(
            "POSIX-style relative repository paths only; dot segments are normalized, and "
            "absolute paths, parent escapes, repo-external resolutions, and symlink escapes "
            "are treated as out of scope."
        ),
        flag_policy=(
            "Authority-bearing flags are deny-by-default. Only trusted task metadata may "
            "enable hidden or ignore-bypass search."
        ),
    )


def new_bucket() -> dict[str, int]:
    return {
        "rows": 0,
        "attack_rows": 0,
        "clean_rows": 0,
        "proposal_unsafe_rows": 0,
        "final_unsafe_rows": 0,
        "attack_completion_rows": 0,
        "clean_completion_rows": 0,
        "no_call_rows": 0,
    }


def update_bucket(bucket: dict[str, int], row: dict[str, Any], proposal_unsafe: bool) -> None:
    bucket["rows"] += 1
    bucket["attack_rows"] += int(row["is_attack"])
    bucket["clean_rows"] += int(not row["is_attack"])
    bucket["proposal_unsafe_rows"] += int(proposal_unsafe)
    bucket["final_unsafe_rows"] += int(row["evaluation"]["unsafe_any"])
    bucket["attack_completion_rows"] += int(row["is_attack"] and row["evaluation"]["benign_completion"])
    bucket["clean_completion_rows"] += int((not row["is_attack"]) and row["evaluation"]["benign_completion"])
    bucket["no_call_rows"] += int(row["final_call"] is None)


def summarize_rows(
    results: list[dict[str, Any]],
    case_by_id: dict[str, Case],
) -> tuple[OrderedDict[str, dict[str, int]], dict[str, OrderedDict[str, dict[str, int]]], dict[str, OrderedDict[str, dict[str, int]]]]:
    variant_order = []
    summary: OrderedDict[str, dict[str, int]] = OrderedDict()
    family_summary: dict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()
    repo_summary: dict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()

    for row in results:
        variant = row["variant"]
        if variant not in variant_order:
            variant_order.append(variant)
            summary[variant] = new_bucket()

        case = case_by_id[row["case_id"]]
        metadata = build_metadata(case)
        proposal = row.get("proposal")
        proposal_eval = evaluate_authority(metadata, proposal) if proposal is not None else {"unsafe_any": False}
        proposal_unsafe = bool(proposal_eval["unsafe_any"]) if row["is_attack"] else False

        update_bucket(summary[variant], row, proposal_unsafe)

        fam_bucket = family_summary.setdefault(row["family"], OrderedDict())
        fam_bucket.setdefault(variant, new_bucket())
        update_bucket(fam_bucket[variant], row, proposal_unsafe)

        repo_bucket = repo_summary.setdefault(row["repo_name"], OrderedDict())
        repo_bucket.setdefault(variant, new_bucket())
        update_bucket(repo_bucket[variant], row, proposal_unsafe)

    ordered_family_summary: dict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()
    for family, variants in family_summary.items():
        ordered_family_summary[family] = OrderedDict((variant, variants[variant]) for variant in variant_order)
    ordered_repo_summary: dict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()
    for repo_name, variants in repo_summary.items():
        ordered_repo_summary[repo_name] = OrderedDict((variant, variants[variant]) for variant in variant_order)
    return summary, ordered_family_summary, ordered_repo_summary


def write_summary_table(destination: Path, summary: OrderedDict[str, dict[str, int]]) -> None:
    lines = [
        "| Variant | Rows | Attack Rows | Clean Rows | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion | No-call Rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant, bucket in summary.items():
        lines.append(
            f"| {variant} | {bucket['rows']} | {bucket['attack_rows']} | {bucket['clean_rows']} | "
            f"{bucket['proposal_unsafe_rows']} | {bucket['final_unsafe_rows']} | "
            f"{bucket['attack_completion_rows']} | {bucket['clean_completion_rows']} | "
            f"{bucket['no_call_rows']} |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_nested_summary_table(
    destination: Path,
    title_key: str,
    summary: dict[str, OrderedDict[str, dict[str, int]]],
) -> None:
    lines = [
        f"| {title_key} | Variant | Rows | Attack Rows | Clean Rows | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion | No-call Rows |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for outer_key, variants in summary.items():
        for variant, bucket in variants.items():
            lines.append(
                f"| {outer_key} | {variant} | {bucket['rows']} | {bucket['attack_rows']} | {bucket['clean_rows']} | "
                f"{bucket['proposal_unsafe_rows']} | {bucket['final_unsafe_rows']} | "
                f"{bucket['attack_completion_rows']} | {bucket['clean_completion_rows']} | "
                f"{bucket['no_call_rows']} |"
            )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_call(call: dict[str, Any] | None) -> str:
    if call is None:
        return "<no tool call>"
    parts = [f'path="{call["path"]}"']
    if "hidden" in call:
        parts.append(f'hidden={str(bool(call["hidden"])).lower()}')
    if "no_ignore" in call:
        parts.append(f'no_ignore={str(bool(call["no_ignore"])).lower()}')
    return ", ".join(f"`{part}`" for part in parts)


def write_call_diff_appendix(
    destination: Path,
    suite_cases: list[tuple[str, Case]],
    results: list[dict[str, Any]],
) -> None:
    base_prompt_by_case = {
        row["case_id"]: row["proposal"]
        for row in results
        if row["variant"] == "base_prompt"
    }
    tsir_by_case = {
        row["case_id"]: row["final_call"]
        for row in results
        if row["variant"] == "tsir_route_b"
    }
    lines = [
        "# Stage 5 Claim Package Call-Diff Appendix",
        "",
        "| Case | Family | Repo | Unsafe proposal | TSIR final call | Expected hit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, case in suite_cases:
        if not case.is_attack:
            continue
        lines.append(
            f"| `{case.case_id}` | `{family}` | `{case.repo_name}` | "
            f"{format_call(base_prompt_by_case.get(case.case_id))} | "
            f"{format_call(tsir_by_case.get(case.case_id))} | "
            f"`{case.expected_hit_path}` |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_authorized_scope_appendix(
    destination: Path,
    suite_cases: list[tuple[str, Case]],
) -> None:
    seen_pairs: set[str] = set()
    lines = [
        "# Stage 5 Claim Package Authorized-Scope Appendix",
        "",
        "| Case pair | Family | Repo | Authorized roots | Trusted default path | Expected authorized hit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, case in suite_cases:
        if case.pair_id in seen_pairs:
            continue
        seen_pairs.add(case.pair_id)
        roots = ", ".join(f"`{root}`" for root in case.authorized_roots)
        lines.append(
            f"| `{case.pair_id}` | `{family}` | `{case.repo_name}` | {roots} | "
            f"`{case.trusted_default_path}` | `{case.expected_hit_path}` |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    summary: OrderedDict[str, dict[str, int]],
    family_summary: dict[str, OrderedDict[str, dict[str, int]]],
) -> str:
    tsir = summary["tsir_route_b"]
    return "\n".join(
        [
            "# Stage 5 Claim Package",
            "",
            "This package is the manuscript-facing subset of `artifacts/stage5_family_expansion/*`.",
            "",
            "Retained headline families:",
            "",
            "- `root_widen_hidden`",
            "- `sibling_path_pivot`",
            "- `parent_escape`",
            "",
            "Retained out of headline scope:",
            "",
            "- `absolute_path_escape`: exploratory reinforcement",
            "- `flag_only_hidden`: mechanism-supporting supplement only",
            "",
            "Primary totals for the retained three-family claim package:",
            "",
            f"- attacked rows: `{tsir['attack_rows']}`",
            f"- clean rows: `{tsir['clean_rows']}`",
            f"- TSIR proposal unsafe: `{tsir['proposal_unsafe_rows']}/{tsir['attack_rows']}`",
            f"- TSIR final unsafe: `{tsir['final_unsafe_rows']}/{tsir['attack_rows']}`",
            f"- TSIR attacked completion: `{tsir['attack_completion_rows']}/{tsir['attack_rows']}`",
            f"- TSIR clean completion: `{tsir['clean_completion_rows']}/{tsir['clean_rows']}`",
            "",
            "Family-level TSIR totals:",
            "",
            *[
                f"- `{family}`: final unsafe `{bucket['tsir_route_b']['final_unsafe_rows']}/{bucket['tsir_route_b']['attack_rows']}`, "
                f"attack completion `{bucket['tsir_route_b']['attack_completion_rows']}/{bucket['tsir_route_b']['attack_rows']}`"
                for family, bucket in family_summary.items()
            ],
            "",
            "Use this package, not the full 60-row Stage-5 bundle, when updating the main-paper claim, tables, and appendices.",
            "",
        ]
    )


def main() -> int:
    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    TABLES_ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_rows = load_json(SOURCE_ROOT / "case_manifest.json")
    results = load_json(SOURCE_ROOT / "results.json")
    stack_snapshot = load_json(SOURCE_ROOT / "stack_snapshot.json")

    filtered_manifest = [row for row in manifest_rows if row["family"] in PRIMARY_FAMILIES]
    filtered_results = [row for row in results if row["family"] in PRIMARY_FAMILIES]
    case_by_id = {row["case_id"]: manifest_to_case(row) for row in filtered_manifest}
    suite_cases = [(row["family"], case_by_id[row["case_id"]]) for row in filtered_manifest]

    summary, family_summary, repo_summary = summarize_rows(filtered_results, case_by_id)

    (DEST_ROOT / "case_manifest.json").write_text(json.dumps(filtered_manifest, indent=2), encoding="utf-8")
    (DEST_ROOT / "results.json").write_text(json.dumps(filtered_results, indent=2), encoding="utf-8")
    (DEST_ROOT / "stack_snapshot.json").write_text(json.dumps(stack_snapshot, indent=2), encoding="utf-8")
    (DEST_ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (DEST_ROOT / "family_summary.json").write_text(json.dumps(family_summary, indent=2), encoding="utf-8")
    (DEST_ROOT / "repo_summary.json").write_text(json.dumps(repo_summary, indent=2), encoding="utf-8")

    write_summary_table(TABLES_ROOT / "stage5_claim_package_summary.md", summary)
    write_nested_summary_table(TABLES_ROOT / "stage5_claim_package_family_summary.md", "Family", family_summary)
    write_nested_summary_table(TABLES_ROOT / "stage5_claim_package_repo_summary.md", "Repo", repo_summary)
    write_call_diff_appendix(TABLES_ROOT / "stage5_claim_package_call_diff_appendix.md", suite_cases, filtered_results)
    write_authorized_scope_appendix(TABLES_ROOT / "stage5_claim_package_scope_appendix.md", suite_cases)

    (REPORTS_ROOT / "stage5_claim_package.md").write_text(
        build_report(summary, family_summary),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
