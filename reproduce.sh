#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"${PYTHON_BIN}" - <<'PY'
missing = []
for module_name, package_name in [
    ("yaml", "PyYAML"),
    ("PIL", "Pillow"),
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("huggingface_hub", "huggingface_hub"),
]:
    try:
        __import__(module_name)
    except ImportError:
        missing.append(package_name)
if missing:
    raise SystemExit(
        "Missing Python packages: "
        + ", ".join(missing)
        + ". Run 'python -m pip install -r requirements.txt' first."
    )
PY

"${PYTHON_BIN}" -m unittest discover -s tests -p 'test_*.py'
"${PYTHON_BIN}" scripts/render_stage6_main_tables.py
"${PYTHON_BIN}" scripts/render_stage7_model_gate_table.py
"${PYTHON_BIN}" scripts/render_stage6_combined_latex_appendix.py
"${PYTHON_BIN}" scripts/render_submission_figures.py

(
  cd paper/latex
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
)

echo "Reproduction checks completed."
