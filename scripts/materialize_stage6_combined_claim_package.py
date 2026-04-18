#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from run_prelock_suite import Case, ROOT
from tsir_policy import build_trusted_scope_metadata, evaluate_authority


STAGE5_ROOT = ROOT / "artifacts" / "stage5_claim_package"
STAGE6_ROOT = ROOT / "artifacts" / "stage6_repo_widening"
TABLES_ROOT = ROOT / "tables"
REPORTS_ROOT = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stage5_row_to_case(row: dict[str, Any]) -> Case:
    payload = dict(row)
    payload.pop("family", None)
    return Case(**payload)


def stage6_row_to_case(row: dict[str, Any]) -> Case:
    payload = dict(row)
    for key in (
        "family",
        "tier",
        "task_id",
        "origin_family",
        "repo_url",
        "authorized_path",
        "literal",
        "unauthorized_path",
        "attack_rationale",
    ):
        payload.pop(key, None)
    return Case(**payload)


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
    group_key: str | None,
) -> OrderedDict[str, Any]:
    variant_order: list[str] = []
    if group_key is None:
        summary: OrderedDict[str, dict[str, int]] = OrderedDict()
        for row in results:
            variant = row["variant"]
            if variant not in variant_order:
                variant_order.append(variant)
                summary[variant] = new_bucket()
            case = case_by_id[row["case_id"]]
            proposal = row.get("proposal")
            proposal_unsafe = False
            if proposal is not None and row["is_attack"]:
                proposal_unsafe = bool(evaluate_authority(build_trusted_scope_metadata(case), proposal)["unsafe_any"])
            update_bucket(summary[variant], row, proposal_unsafe)
        return OrderedDict((variant, summary[variant]) for variant in variant_order)

    grouped: OrderedDict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()
    for row in results:
        variant = row["variant"]
        if variant not in variant_order:
            variant_order.append(variant)
        outer_key = row[group_key]
        bucket = grouped.setdefault(outer_key, OrderedDict())
        bucket.setdefault(variant, new_bucket())
        case = case_by_id[row["case_id"]]
        proposal = row.get("proposal")
        proposal_unsafe = False
        if proposal is not None and row["is_attack"]:
            proposal_unsafe = bool(evaluate_authority(build_trusted_scope_metadata(case), proposal)["unsafe_any"])
        update_bucket(bucket[variant], row, proposal_unsafe)

    ordered: OrderedDict[str, OrderedDict[str, dict[str, int]]] = OrderedDict()
    for outer_key, variants in grouped.items():
        ordered[outer_key] = OrderedDict((variant, variants[variant]) for variant in variant_order)
    return ordered


def write_summary_table(destination: Path, summary: OrderedDict[str, dict[str, int]]) -> None:
    lines = [
        "| Variant | Rows | Attack Rows | Clean Rows | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion | No-call Rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant, bucket in summary.items():
        lines.append(
            f"| {variant} | {bucket['rows']} | {bucket['attack_rows']} | {bucket['clean_rows']} | "
            f"{bucket['proposal_unsafe_rows']} | {bucket['final_unsafe_rows']} | "
            f"{bucket['attack_completion_rows']} | {bucket['clean_completion_rows']} | {bucket['no_call_rows']} |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_nested_summary_table(destination: Path, title_key: str, summary: OrderedDict[str, OrderedDict[str, dict[str, int]]]) -> None:
    lines = [
        f"| {title_key} | Variant | Rows | Attack Rows | Clean Rows | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion | No-call Rows |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for outer_key, variants in summary.items():
        for variant, bucket in variants.items():
            lines.append(
                f"| {outer_key} | {variant} | {bucket['rows']} | {bucket['attack_rows']} | {bucket['clean_rows']} | "
                f"{bucket['proposal_unsafe_rows']} | {bucket['final_unsafe_rows']} | "
                f"{bucket['attack_completion_rows']} | {bucket['clean_completion_rows']} | {bucket['no_call_rows']} |"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine Stage 5 claim package with widened Stage 6 repos.")
    parser.add_argument("--run-label", default="tier_a")
    parser.add_argument("--dest-name", default="stage6_combined_claim_package")
    args = parser.parse_args()

    stage5_manifest = load_json(STAGE5_ROOT / "case_manifest.json")
    stage5_results = load_json(STAGE5_ROOT / "results.json")
    stage5_stack = load_json(STAGE5_ROOT / "stack_snapshot.json")
    stage6_root = STAGE6_ROOT / args.run_label
    stage6_manifest = load_json(stage6_root / "case_manifest.json")
    stage6_results = load_json(stage6_root / "results.json")
    stage6_gate = load_json(stage6_root / "repo_gate.json")
    promoted_repos = {row["repo_name"] for row in stage6_gate if row["headline_repo_candidate"]}
    stage5_family_by_case = {row["case_id"]: row["family"] for row in stage5_results}
    stage6_family_by_case = {row["case_id"]: row["family"] for row in stage6_results}

    combined_manifest = []
    case_by_id: dict[str, Case] = {}
    for row in stage5_manifest:
        enriched = dict(row)
        enriched["family"] = stage5_family_by_case.get(row["case_id"], row["family"])
        enriched["source_suite"] = "stage5_claim_package"
        combined_manifest.append(enriched)
        case_by_id[row["case_id"]] = stage5_row_to_case(row)
    for row in stage6_manifest:
        if row["repo_name"] not in promoted_repos:
            continue
        enriched = dict(row)
        enriched["family"] = stage6_family_by_case.get(row["case_id"], row["family"])
        enriched["source_suite"] = f"stage6_{args.run_label}"
        combined_manifest.append(enriched)
        case_by_id[row["case_id"]] = stage6_row_to_case(row)

    combined_results = []
    for row in stage5_results:
        enriched = dict(row)
        enriched["source_suite"] = "stage5_claim_package"
        combined_results.append(enriched)
    for row in stage6_results:
        if row["repo_name"] not in promoted_repos:
            continue
        enriched = dict(row)
        enriched["source_suite"] = f"stage6_{args.run_label}"
        combined_results.append(enriched)

    summary = summarize_rows(combined_results, case_by_id, None)
    family_summary = summarize_rows(combined_results, case_by_id, "family")
    repo_summary = summarize_rows(combined_results, case_by_id, "repo_name")
    source_summary = summarize_rows(combined_results, case_by_id, "source_suite")

    dest_root = ROOT / "artifacts" / args.dest_name
    dest_root.mkdir(parents=True, exist_ok=True)
    TABLES_ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)

    stack_snapshot = {
        "stage5_stack_snapshot": stage5_stack,
        "stage6_run_label": args.run_label,
        "promoted_stage6_repos": sorted(promoted_repos),
        "source_suites": ["stage5_claim_package", f"stage6_{args.run_label}"],
    }
    (dest_root / "case_manifest.json").write_text(json.dumps(combined_manifest, indent=2), encoding="utf-8")
    (dest_root / "results.json").write_text(json.dumps(combined_results, indent=2), encoding="utf-8")
    (dest_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (dest_root / "family_summary.json").write_text(json.dumps(family_summary, indent=2), encoding="utf-8")
    (dest_root / "repo_summary.json").write_text(json.dumps(repo_summary, indent=2), encoding="utf-8")
    (dest_root / "source_summary.json").write_text(json.dumps(source_summary, indent=2), encoding="utf-8")
    (dest_root / "stack_snapshot.json").write_text(json.dumps(stack_snapshot, indent=2), encoding="utf-8")

    prefix = args.dest_name
    write_summary_table(TABLES_ROOT / f"{prefix}_summary.md", summary)
    write_nested_summary_table(TABLES_ROOT / f"{prefix}_family_summary.md", "Family", family_summary)
    write_nested_summary_table(TABLES_ROOT / f"{prefix}_repo_summary.md", "Repo", repo_summary)
    write_nested_summary_table(TABLES_ROOT / f"{prefix}_source_summary.md", "Source", source_summary)

    base_prompt_by_case = {row["case_id"]: row["proposal"] for row in combined_results if row["variant"] == "base_prompt"}
    tsir_by_case = {row["case_id"]: row["final_call"] for row in combined_results if row["variant"] == "tsir_route_b"}
    call_lines = [
        f"# {args.dest_name} Call-Diff Appendix",
        "",
        "| Case | Family | Repo | Source | Unsafe proposal | TSIR final call | Expected hit |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    scope_lines = [
        f"# {args.dest_name} Authorized-Scope Appendix",
        "",
        "| Case pair | Family | Repo | Source | Authorized roots | Trusted default path | Expected authorized hit |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    seen_pairs: set[str] = set()
    for row in combined_manifest:
        if row["is_attack"]:
            call_lines.append(
                f"| `{row['case_id']}` | `{row['family']}` | `{row['repo_name']}` | `{row['source_suite']}` | "
                f"{format_call(base_prompt_by_case.get(row['case_id']))} | {format_call(tsir_by_case.get(row['case_id']))} | "
                f"`{row['expected_hit_path']}` |"
            )
        if row["pair_id"] not in seen_pairs:
            seen_pairs.add(row["pair_id"])
            roots = ", ".join(f"`{root}`" for root in row["authorized_roots"])
            scope_lines.append(
                f"| `{row['pair_id']}` | `{row['family']}` | `{row['repo_name']}` | `{row['source_suite']}` | "
                f"{roots} | `{row['trusted_default_path']}` | `{row['expected_hit_path']}` |"
            )

    (TABLES_ROOT / f"{prefix}_call_diff_appendix.md").write_text("\n".join(call_lines) + "\n", encoding="utf-8")
    (TABLES_ROOT / f"{prefix}_scope_appendix.md").write_text("\n".join(scope_lines) + "\n", encoding="utf-8")

    tsir = summary["tsir_route_b"]
    report = "\n".join(
        [
            f"# {args.dest_name}",
            "",
            f"Promoted Stage 6 repos from `{args.run_label}`:",
            "",
            *[f"- `{repo}`" for repo in sorted(promoted_repos)],
            "",
            "Combined headline-package totals:",
            "",
            f"- attacked rows: `{tsir['attack_rows']}`",
            f"- clean rows: `{tsir['clean_rows']}`",
            f"- TSIR proposal unsafe: `{tsir['proposal_unsafe_rows']}/{tsir['attack_rows']}`",
            f"- TSIR final unsafe: `{tsir['final_unsafe_rows']}/{tsir['attack_rows']}`",
            f"- TSIR attacked completion: `{tsir['attack_completion_rows']}/{tsir['attack_rows']}`",
            f"- TSIR clean completion: `{tsir['clean_completion_rows']}/{tsir['clean_rows']}`",
            "",
        ]
    )
    (REPORTS_ROOT / f"{prefix}.md").write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
