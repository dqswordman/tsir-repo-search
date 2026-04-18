#!/usr/bin/env python3
"""Render a LaTeX table for the Stage-7 model gate summary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "artifacts" / "stage7_model_widening" / "model_gate" / "summary.json"
OUT_PATH = ROOT / "paper" / "latex" / "generated_stage7_model_gate_table.tex"


MODEL_LABELS = {
    "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B",
    "Qwen/Qwen2.5-0.5B-Instruct": "Qwen2.5-0.5B",
    "NousResearch/Hermes-3-Llama-3.1-8B": "Hermes-3-8B",
}


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    lines = [
        "\\begin{table}[t]",
        "\\caption{Stage-7 model gate on the same 80-row manifest. Two model entries preserve the full TSIR safety-utility separation in the same tool lane, while the low-capacity Qwen control remains a utility boundary.}",
        "\\label{tab:modelgate}",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{1pt}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{@{}llcccccc@{}}",
        "\\toprule",
        "Model & Family & TSIR final unsafe & TSIR attacked completion & TSIR clean completion & Struct. final unsafe & Schema attacked completion & Pass \\\\",
        "\\midrule",
    ]
    for entry in summary["entries"]:
        model = MODEL_LABELS.get(entry["model_id"], entry["model_id"])
        lines.append(
            " & ".join(
                [
                    model,
                    entry["model_family"],
                    f"{entry['tsir_attack_final_unsafe_rows']}/{entry['attack_rows']}",
                    f"{entry['tsir_attack_completion_rows']}/{entry['attack_rows']}",
                    f"{entry['tsir_clean_completion_rows']}/{entry['clean_rows']}",
                    f"{entry['structured_context_attack_final_unsafe_rows']}/{entry['attack_rows']}",
                    f"{entry['dynamic_schema_attack_completion_rows']}/{entry['attack_rows']}",
                    "yes" if entry["headline_model_candidate"] else "no",
                ]
            )
            + " \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "}",
            "\\end{table}",
        ]
    )
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
