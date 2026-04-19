#!/usr/bin/env python3
"""Render main-text LaTeX tables for the widened 80-row evaluation suite."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "stage6_combined_claim_package"
OUT_DIR = ROOT / "paper" / "latex"

SUMMARY_PATH = ARTIFACT_DIR / "summary.json"
FAMILY_PATH = ARTIFACT_DIR / "family_summary.json"
REPO_PATH = ARTIFACT_DIR / "repo_summary.json"

VARIANT_ORDER = [
    "base_prompt",
    "warning_prompt",
    "structured_context_prompt",
    "dynamic_schema_constraint",
    "no_tool_on_untrusted_context",
    "fixed_allowlist",
    "score_fusion_proxy",
    "authorized_subtree_reject",
    "tsir_route_b",
]

VARIANT_LABELS = {
    "base_prompt": "Base prompt",
    "warning_prompt": "Warning",
    "structured_context_prompt": "Struct. ctx.",
    "dynamic_schema_constraint": "Dyn. schema",
    "no_tool_on_untrusted_context": "No-tool deny",
    "fixed_allowlist": "Fixed allowlist",
    "score_fusion_proxy": "Score fusion",
    "authorized_subtree_reject": "Subtree reject",
    "tsir_route_b": "TSIR",
}

FAMILY_ORDER = [
    ("root_widen_hidden", "root\\_widen\\_hidden", "tab:rootfamily"),
    ("sibling_path_pivot", "sibling\\_path\\_pivot", "tab:siblingfamily"),
    ("parent_escape", "parent\\_escape", "tab:parentfamily"),
]

REPO_ORDER = [
    "pyaml_env",
    "environs",
    "python_decouple",
    "dynaconf",
    "pydantic_settings",
    "django_configurations",
    "python_dotenv",
    "configargparse",
]

REPO_LABELS = {
    "pyaml_env": "\\emph{pyaml\\_env}",
    "environs": "\\emph{environs}",
    "python_decouple": "\\emph{python-decouple}",
    "dynaconf": "\\emph{dynaconf}",
    "pydantic_settings": "\\emph{pydantic-settings}",
    "django_configurations": "\\emph{django-configurations}",
    "python_dotenv": "\\emph{python-dotenv}",
    "configargparse": "\\emph{ConfigArgParse}",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frac(num: int, den: int) -> str:
    return f"{num}/{den}"


def render_table_begin(caption: str, label: str, colspec: str) -> list[str]:
    return [
        "\\begin{table}[t]",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        f"\\begin{{tabular}}{{@{{}}{colspec}@{{}}}}",
        "\\toprule",
    ]


def render_table_end() -> list[str]:
    return [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]


def render_overall_table(summary: dict) -> str:
    lines = render_table_begin(
        "Overall results on 40 attacked rows and 40 matched clean rows.",
        "tab:overall",
        "lcccc",
    )
    lines.append("Variant & Prop. unsafe & Final unsafe & Atk. comp. & Clean comp. \\\\")
    lines.append("\\midrule")
    for variant in VARIANT_ORDER:
        row = summary[variant]
        lines.append(
            " & ".join(
                [
                    VARIANT_LABELS[variant],
                    frac(row["proposal_unsafe_rows"], row["attack_rows"]),
                    frac(row["final_unsafe_rows"], row["attack_rows"]),
                    frac(row["attack_completion_rows"], row["attack_rows"]),
                    frac(row["clean_completion_rows"], row["clean_rows"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(render_table_end())
    return "\n".join(lines) + "\n"


def render_family_table(family_name: str, family_label: str, table_label: str, families: dict) -> str:
    lines = render_table_begin(
        f"Family breakdown for \\texttt{{{family_label}}}.",
        table_label,
        "lcccc",
    )
    lines.append("Variant & Prop. unsafe & Final unsafe & Atk. comp. & Clean comp. \\\\")
    lines.append("\\midrule")
    family = families[family_name]
    for variant in VARIANT_ORDER:
        row = family[variant]
        lines.append(
            " & ".join(
                [
                    VARIANT_LABELS[variant],
                    frac(row["proposal_unsafe_rows"], row["attack_rows"]),
                    frac(row["final_unsafe_rows"], row["attack_rows"]),
                    frac(row["attack_completion_rows"], row["attack_rows"]),
                    frac(row["clean_completion_rows"], row["clean_rows"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(render_table_end())
    return "\n".join(lines) + "\n"


def render_repo_table(repos: dict) -> str:
    lines = render_table_begin(
        "Compact real-repository view of the promoted real-repository widening set. Each repository contributes four attacked rows and four clean rows.",
        "tab:repoview",
        "lccccc",
    )
    lines[5] = "\\setlength{\\tabcolsep}{2pt}"
    lines.insert(6, "\\resizebox{\\textwidth}{!}{%")
    lines.append("Repository & Struct. final unsafe & Schema attacked completion & TSIR final unsafe & TSIR attacked completion & TSIR clean completion \\\\")
    lines.append("\\midrule")
    for repo in REPO_ORDER:
        structured = repos[repo]["structured_context_prompt"]
        schema = repos[repo]["dynamic_schema_constraint"]
        tsir = repos[repo]["tsir_route_b"]
        lines.append(
            " & ".join(
                [
                    REPO_LABELS[repo],
                    frac(structured["final_unsafe_rows"], structured["attack_rows"]),
                    frac(schema["attack_completion_rows"], schema["attack_rows"]),
                    frac(tsir["final_unsafe_rows"], tsir["attack_rows"]),
                    frac(tsir["attack_completion_rows"], tsir["attack_rows"]),
                    frac(tsir["clean_completion_rows"], tsir["clean_rows"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "}", "\\end{table}"])
    return "\n".join(lines) + "\n"


def main() -> None:
    summary = load_json(SUMMARY_PATH)
    families = load_json(FAMILY_PATH)
    repos = load_json(REPO_PATH)

    (OUT_DIR / "stage6_overall_table.tex").write_text(
        render_overall_table(summary), encoding="utf-8"
    )
    for family_name, family_label, table_label in FAMILY_ORDER:
        filename = f"stage6_{family_name}_table.tex"
        (OUT_DIR / filename).write_text(
            render_family_table(family_name, family_label, table_label, families),
            encoding="utf-8",
        )
    (OUT_DIR / "stage6_repo_table.tex").write_text(
        render_repo_table(repos), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
