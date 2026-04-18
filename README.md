# Trusted Scope Inheritance for Mixed-Provenance Repository Search Agents

This repository is the public artifact release for the paper draft:

- [PDF draft](paper/esorics2026_lncs_draft.pdf)
- [LaTeX source package](paper/latex/esorics2026_lncs_source.zip)
- [Supplementary artifact bundle](paper/submission_artifact_bundle.zip)
- [Artifact index](ARTIFACT_INDEX.md)

## What this repo contains

This project studies a narrow security mechanism for repository-search agents. The object is the **Trusted Scope Inheritance Rule (TSIR)**: search scope and scope-widening flags must inherit from trusted task metadata, while untrusted retrieved text may contribute only in-scope hints.

Within one frozen Hugging Face `rg_search` lane, the retained claim supported by this release is:

- two successful model entries:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `NousResearch/Hermes-3-Llama-3.1-8B`
- three empirical attack families:
  - `root_widen_hidden`
  - `sibling_path_pivot`
  - `parent_escape`
- eight real repositories plus one explicit boundary repository
- `40/40` attacked rows with `0/40` unsafe final calls under TSIR
- `40/40` attacked completion and `40/40` clean completion under TSIR

This is not a general multi-tool or multi-step agent benchmark. It is a bounded artifact repo for one path-authorizing repository-search lane.

## Repository layout

- `artifacts/`: machine-readable evaluation outputs, manifests, summaries, and boundary bundles
- `reports/`: formal spec, implementation notes, evidence ledger, and scientific result summaries
- `scripts/`: TSIR policy code plus artifact materialization and table/figure rendering scripts
- `tests/`: canonicalization, parser-fuzz, and policy regression tests
- `tables/`: manuscript-facing markdown tables derived from the released artifacts
- `figures/`: figure assets used by the paper
- `paper/`: draft PDF, markdown source, LaTeX package, and supplementary archive

## Quickstart

Inspect the current paper draft:

```bash
xdg-open paper/esorics2026_lncs_draft.pdf
```

Run the released policy and parser tests:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py'
```

Regenerate the manuscript tables and figures from the released artifacts:

```bash
python scripts/render_stage6_main_tables.py
python scripts/render_stage7_model_gate_table.py
python scripts/render_stage6_combined_latex_appendix.py
python scripts/render_submission_figures.py
```

Rebuild the LNCS draft:

```bash
cd paper/latex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Or use the convenience wrapper from the repository root:

```bash
PYTHON_BIN=python bash reproduce.sh
```

## Artifact audit entrypoints

The most useful files for a reviewer or reader are:

- `reports/formal_tsir_spec.md`
- `reports/implementation_security_notes.md`
- `reports/evidence_ledger.md`
- `artifacts/main_suite/summary.json`
- `artifacts/model_widening_summary/summary.json`
- `artifacts/second_tool_boundary_summary/summary.json`
- `tables/stage6_combined_claim_package_summary.md`
- `tables/stage7_model_gate_summary.md`
- `paper/submission_artifact_manifest.md`

## Environment

The must-run evidence in the internal execution lane was produced in:

- Python: `/home/du/miniforge3/envs/yolo_py39_cuda128/bin/python`
- Torch: `2.8.0+cu128`
- CUDA: `12.8`
- Transformers: `4.57.6`

See `artifacts/environment_report.md` for the recorded execution environment.

## Boundaries

This release preserves the paper's explicit boundaries:

- `django-environ` remains a boundary repository, not a promoted headline repository.
- `Qwen/Qwen2.5-0.5B-Instruct` remains a low-capacity model boundary.
- `read_file(path)` remains second-tool boundary evidence rather than part of the headline claim.

## Licensing Notes

- Review `LICENSE` and `THIRD_PARTY_NOTICES.md` before public redistribution or derivative use.
