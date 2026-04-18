#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE8_ROOT = ROOT / "artifacts" / "stage8_read_file_widening"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def family_name(model_id: str) -> str:
    lowered = model_id.lower()
    if "qwen" in lowered:
        return "qwen"
    if "llama" in lowered or "hermes" in lowered:
        return "llama-family"
    if "mistral" in lowered:
        return "mistral"
    return "other"


def build_report(entries: list[dict[str, Any]], second_family_pass: bool) -> str:
    lines = [
        "# Stage 8 read_file Tool Gate",
        "",
        "- tool: `read_file(path)`",
        "- family scope: `sibling_path_pivot` plus `parent_escape` only",
        "- interpretation rule: this gate measures second-tool support for the path-authority component; it does not by itself widen the main path-and-flag headline claim",
        "",
        f"- total evaluated model entries: `{len(entries)}`",
        f"- second-family headline pass present: `{second_family_pass}`",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"## {entry['model_id']}",
                "",
                f"- family: `{entry['model_family']}`",
                f"- source: `{entry['source']}`",
                f"- TSIR final unsafe: `{entry['tsir_attack_final_unsafe_rows']}/{entry['attack_rows']}`",
                f"- TSIR attacked completion: `{entry['tsir_attack_completion_rows']}/{entry['attack_rows']}`",
                f"- TSIR clean completion: `{entry['tsir_clean_completion_rows']}/{entry['clean_rows']}`",
                f"- structured_context attack-side final unsafe: `{entry['structured_context_attack_final_unsafe_rows']}/{entry['attack_rows']}`",
                f"- fixed_allowlist attack-side final unsafe: `{entry['fixed_allowlist_attack_final_unsafe_rows']}/{entry['attack_rows']}`",
                f"- dynamic_schema attacked completion: `{entry['dynamic_schema_attack_completion_rows']}/{entry['attack_rows']}`",
                f"- authorized_subtree_reject attacked completion: `{entry['authorized_reject_attack_completion_rows']}/{entry['attack_rows']}`",
                f"- headline_tool_candidate: `{entry['headline_tool_candidate']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Stage 8 read_file tool-gate results.")
    parser.add_argument("--run-label", action="append", required=True, help="Stage 8 run label to include.")
    args = parser.parse_args()

    entries: list[dict[str, Any]] = []
    for run_label in args.run_label:
        run_root = STAGE8_ROOT / run_label
        stack_snapshot = load_json(run_root / "stack_snapshot.json")
        summary = load_json(run_root / "summary.json")
        gate = load_json(run_root / "tool_gate.json")
        entries.append(
            {
                "model_id": stack_snapshot["model_id"],
                "model_family": family_name(stack_snapshot["model_id"]),
                "source": run_label,
                "attack_rows": gate["attack_rows"],
                "clean_rows": gate["clean_rows"],
                "tsir_attack_final_unsafe_rows": summary["tsir_route_b"]["final_unsafe_rows"],
                "tsir_attack_completion_rows": summary["tsir_route_b"]["attack_completion_rows"],
                "tsir_clean_completion_rows": summary["tsir_route_b"]["clean_completion_rows"],
                "structured_context_attack_final_unsafe_rows": summary["structured_context_prompt"]["final_unsafe_rows"],
                "fixed_allowlist_attack_final_unsafe_rows": summary["fixed_allowlist"]["final_unsafe_rows"],
                "dynamic_schema_attack_completion_rows": summary["dynamic_schema_constraint"]["attack_completion_rows"],
                "authorized_reject_attack_completion_rows": summary["authorized_subtree_reject"]["attack_completion_rows"],
                "headline_tool_candidate": gate["headline_tool_candidate"],
            }
        )

    ordered = OrderedDict((entry["source"], entry) for entry in entries)
    second_family_pass = any(
        entry["model_family"] != "qwen" and entry["headline_tool_candidate"] for entry in ordered.values()
    )

    out_root = STAGE8_ROOT / "tool_gate"
    out_root.mkdir(parents=True, exist_ok=True)
    tables_dir = ROOT / "tables"
    reports_dir = ROOT / "reports"
    tables_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (out_root / "summary.json").write_text(
        json.dumps(
            {
                "entries": list(ordered.values()),
                "second_family_headline_pass": second_family_pass,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "| Source | Model | Family | TSIR unsafe | TSIR atk. comp. | TSIR clean comp. | Struct. atk. unsafe | Fixed allowlist atk. unsafe | Schema atk. comp. | Reject atk. comp. | Headline pass |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in ordered.values():
        lines.append(
            f"| {entry['source']} | {entry['model_id']} | {entry['model_family']} | "
            f"{entry['tsir_attack_final_unsafe_rows']}/{entry['attack_rows']} | "
            f"{entry['tsir_attack_completion_rows']}/{entry['attack_rows']} | "
            f"{entry['tsir_clean_completion_rows']}/{entry['clean_rows']} | "
            f"{entry['structured_context_attack_final_unsafe_rows']}/{entry['attack_rows']} | "
            f"{entry['fixed_allowlist_attack_final_unsafe_rows']}/{entry['attack_rows']} | "
            f"{entry['dynamic_schema_attack_completion_rows']}/{entry['attack_rows']} | "
            f"{entry['authorized_reject_attack_completion_rows']}/{entry['attack_rows']} | "
            f"`{entry['headline_tool_candidate']}` |"
        )
    (tables_dir / "stage8_tool_gate_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (reports_dir / "stage8_tool_gate.md").write_text(build_report(list(ordered.values()), second_family_pass) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
