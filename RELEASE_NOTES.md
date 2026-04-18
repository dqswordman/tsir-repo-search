# Release Notes

## ESORICS 2026 submission artifact

Release tag: `esorics2026-submission`

This release packages the submission-state artifact for the paper:
`Trusted Scope Inheritance for Mixed-Provenance Repository Search Agents`.

Included assets:

- paper PDF: `paper/esorics2026_lncs_draft.pdf`
- LaTeX source package: `paper/latex/esorics2026_lncs_source.zip`
- supplementary artifact bundle: `paper/submission_artifact_bundle.zip`
- artifact index: `ARTIFACT_INDEX.md`

Retained supported scope:

- one frozen `rg_search` tool lane
- two successful model entries:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `NousResearch/Hermes-3-Llama-3.1-8B`
- three empirical attack families:
  - `root_widen_hidden`
  - `sibling_path_pivot`
  - `parent_escape`
- eight promoted real repositories plus documented boundary bundles

Headline result under TSIR in the retained lane:

- `0/40` attacked-row unsafe final calls
- `40/40` attacked-row completion
- `40/40` clean-row completion

Boundary evidence kept in the release:

- `django-environ` repository boundary
- `Qwen/Qwen2.5-0.5B-Instruct` utility boundary
- `read_file(path)` second-tool boundary

Reproduction entrypoint:

```bash
PYTHON_BIN=python bash reproduce.sh
```
