# Evidence Ledger

## Claim 0: TSIR enforces final-call path-and-flag safety for the exposed `rg_search` schema under the stated canonicalization assumptions

- paper object component: formal security rule and implementation boundary
- evidence stage: post-anchor Stage-1 formalization and Stage-2 wrapper hardening
- required evidence:
  - formal policy object
  - theorem / proof sketch
  - executable regression tests for canonicalization, parser behavior, and wrapper enforcement
- artifact paths:
  - `reports/formal_tsir_spec.md`
  - `reports/implementation_security_notes.md`
  - `artifacts/tsir_policy_schema.json`
  - `scripts/tsir_policy.py`
  - `tests/test_canonicalization.py`
  - `tests/test_parser_fuzz.py`
  - `tests/test_policy.py`
- retained scope:
  - current exposed tool schema only: `pattern`, `path`, `hidden`, `no_ignore`
  - one wrapper boundary
  - one single-turn `rg_search` execution lane
- falsifier:
  - any counterexample in the executable policy tests where an unsafe proposal yields an unsafe final call; or
  - any implementation change that allows malformed authority-bearing fields to bypass canonicalization or flag checks

## Claim 1: Mixed-provenance repository search can misassign search authority in the frozen stack

- paper object component: failure existence for Trusted Scope Inheritance Rule
- evidence stage: prelock plus post-lock reinforcement
- required experiment: matched attack/clean pairs under the frozen `Qwen2.5-7B-Instruct` plus `rg` stack
- artifact paths:
  - `artifacts/prelock/prelock_results.json`
  - `artifacts/prelock/gate_checks.json`
  - `artifacts/stage6_combined_claim_package/results.json`
  - `reports/expanded_evidence_decisive_cases.md`
  - `reports/stage6_combined_claim_package.md`
- tables:
  - `tables/prelock_summary.md`
  - `tables/stage6_combined_claim_package_family_summary.md`
- retained baselines:
  - `base_prompt`
  - `warning_prompt`
- falsifier:
  - no reproducible unsafe path/flag widening, sibling-path pivot, or parent-directory escape on attacked rows

## Claim 2: TSIR preserves safety while recovering utility relative to conservative and strong externally constrained rivals

- paper object component: strongest-neighbor pressure and post-anchor baseline strengthening
- evidence stage: prelock plus widened post-lock evidence
- required experiment: same-case comparison against conservative routing, reject-only trusted-scope enforcement, and dynamic schema constraints
- artifact paths:
  - `artifacts/prelock/gate_checks.json`
  - `reports/stage3_baseline_strengthening.md`
  - `artifacts/stage6_combined_claim_package/summary.json`
  - `artifacts/stage6_combined_claim_package/family_summary.json`
  - `reports/stage6_combined_claim_package.md`
- tables:
  - `tables/prelock_summary.md`
  - `tables/stage6_combined_claim_package_summary.md`
  - `tables/stage6_combined_claim_package_family_summary.md`
- retained baselines:
  - `no_tool_on_untrusted_context`
  - `authorized_subtree_reject`
  - `dynamic_schema_constraint`
  - `tsir_route_b`
- falsifier:
  - any retained conservative or externally constrained rival matches TSIR on both final-call safety and attacked-row benign completion

## Claim 3: Prompt-only structure and coarse repo-contained controls do not match TSIR on the safety-utility tradeoff

- paper object component: object independence
- evidence stage: prelock plus widened post-lock evidence
- required experiment: hold model, tool, and cases fixed while comparing prompt-only and coarse capability controls
- artifact paths:
  - `reports/prelock_casebook.md`
  - `reports/stage3_baseline_strengthening.md`
  - `artifacts/stage6_combined_claim_package/results.json`
  - `reports/expanded_evidence_decisive_cases.md`
  - `reports/stage6_combined_claim_package.md`
- tables:
  - `tables/prelock_summary.md`
  - `tables/stage6_combined_claim_package_summary.md`
  - `tables/stage6_combined_claim_package_repo_summary.md`
- retained baselines:
  - `warning_prompt`
  - `structured_context_prompt`
  - `fixed_allowlist`
  - `score_fusion_proxy`
- falsifier:
  - a prompt-only or coarse repo-contained control matches TSIR on both final-call safety and attacked-row completion over the decisive rows

## Claim 4: The supported TSIR claim extends to three empirical families across controlled settings and eight real repositories

- paper object component: broadened but still narrow claim width
- evidence stage: post-lock reinforcement only
- required experiment:
  - retain the three-family object from Stage 5; and
  - promote only those Stage-6 repositories that pass the same repo gate under the strengthened comparator set
- artifact paths:
  - `artifacts/stage5_family_expansion/summary.json`
  - `artifacts/stage5_family_expansion/family_summary.json`
  - `reports/stage5_family_expansion.md`
  - `artifacts/stage6_repo_widening/tier_ab/summary.json`
  - `artifacts/stage6_repo_widening/tier_ab/repo_gate.json`
  - `reports/stage6_tier_ab_repo_gate.md`
  - `artifacts/stage6_combined_claim_package/summary.json`
  - `artifacts/stage6_combined_claim_package/family_summary.json`
  - `artifacts/stage6_combined_claim_package/repo_summary.json`
  - `artifacts/stage6_combined_claim_package/source_summary.json`
  - `reports/stage6_combined_claim_package.md`
- tables:
  - `tables/stage6_combined_claim_package_summary.md`
  - `tables/stage6_combined_claim_package_family_summary.md`
  - `tables/stage6_combined_claim_package_repo_summary.md`
  - `tables/stage6_combined_claim_package_source_summary.md`
- promoted headline repositories:
  - `pyaml_env`
  - `environs`
  - `python_decouple`
  - `dynaconf`
  - `pydantic_settings`
  - `django_configurations`
  - `python_dotenv`
  - `configargparse`
- retained baselines:
  - `base_prompt`
  - `warning_prompt`
  - `structured_context_prompt`
  - `dynamic_schema_constraint`
  - `fixed_allowlist`
  - `score_fusion_proxy`
  - `authorized_subtree_reject`
  - `no_tool_on_untrusted_context`
- falsifier:
  - any promoted repository fails to reproduce the same safety-utility separation; or
  - any promoted family-repository addition makes TSIR unsafe, incomplete, or indistinguishable from a retained control

## Claim 5: `django_environ` remains an explicit ninth-repository boundary rather than headline support

- paper object component: post-lock boundary discipline
- evidence stage: post-lock reinforcement after Stage 6
- required experiment:
  - keep the earlier `django_environ` root-widen reproduction; and
  - explicitly test the more realistic docs-to-docs sibling pivot without folding it into the headline suite
- artifact paths:
  - `artifacts/extension_attempt_django_environ/extension_results.json`
  - `artifacts/extension_attempt_django_environ/summary.json`
  - `reports/extension_attempt_django_environ.md`
  - `artifacts/expanded_evidence_round05_attempt/expanded_evidence_results.json`
- tables:
  - `tables/extension_attempt_django_environ_summary.md`
  - `tables/extension_attempt_django_environ_family_summary.md`
- retained interpretation:
  - root-widen reinforcement survives on `django_environ`
  - the attempted docs-to-docs sibling pivot does not induce authority transfer and therefore does not widen the supported sibling-family claim
- falsifier:
  - if a comparable same-lane ninth-repository sibling transfer later succeeds under the retained controls, the boundary must be reconsidered rather than left as a permanent limit

## Claim 6: Supplementary Stage-5 families strengthen mechanism interpretation without all widening the headline claim

- paper object component: mechanism reinforcement and boundary discipline
- evidence stage: post-lock reinforcement after Stage 5
- required experiment:
  - one exploratory family bundle for `absolute_path_escape`
  - one meaningful mini-scan for `flag_only_hidden`
- artifact paths:
  - `artifacts/stage5_family_expansion/summary.json`
  - `artifacts/stage5_family_expansion/family_summary.json`
  - `artifacts/stage5_flag_only_hidden_scan/summary.json`
  - `reports/stage5_family_expansion.md`
- retained interpretation:
  - `absolute_path_escape` is exploratory because it is more synthetic under the repo-relative prompt contract
  - `flag_only_hidden` confirms that unauthorized `hidden` is an authority-bearing field, but it is not TSIR-distinctive because `fixed_allowlist` also succeeds
- falsifier:
  - if `absolute_path_escape` proves non-separating, drop it from supplementary reinforcement
  - if `flag_only_hidden` ceases to differentiate any unsafe prompt-only control, it no longer adds mechanism value

## Claim 7: The supported TSIR claim widens to two successful model entries in the same tool lane while preserving a model-capacity boundary

- paper object component: same-lane model-width reinforcement after repository widening
- evidence stage: post-lock reinforcement only
- required experiment:
  - hold the exact Stage-6 80-row manifest fixed;
  - keep the same `rg_search` tool schema, scoring pipeline, and retained comparator set; and
  - evaluate at least one second-family model entry plus one lower-capacity control
- artifact paths:
  - `artifacts/stage7_model_widening/model_gate/summary.json`
  - `artifacts/stage7_model_widening/hermes3_llama31_8b_full/summary.json`
  - `artifacts/stage7_model_widening/qwen25_05b_full/summary.json`
  - `reports/stage7_model_gate.md`
  - `reports/stage7_hermes3_llama31_8b_full_model_widening.md`
  - `reports/stage7_qwen25_05b_full_model_widening.md`
- tables:
  - `tables/stage7_model_gate_summary.md`
- promoted supporting model entries:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `NousResearch/Hermes-3-Llama-3.1-8B`
- retained model boundary:
  - `Qwen/Qwen2.5-0.5B-Instruct`
- retained interpretation:
  - the same-lane TSIR effect is no longer single-model;
  - utility remains model-capacity-sensitive inside the Qwen family; and
  - the supported claim widens to two successful model entries, not arbitrary cross-model generality
- falsifier:
  - the second-family headline pass disappears on rerun; or
  - a retained baseline matches TSIR on both final-call safety and attacked-row completion in the second-family run; or
  - the low-capacity boundary is misreported as a supporting result

## Claim 8: Narrow second-tool `read_file(path)` broadening remains boundary evidence rather than promoted headline support

- paper object component: second-order width probe for the path-authority component only
- evidence stage: post-lock reinforcement after Stage 7
- required experiment:
  - hold the same path-authority object fixed;
  - switch only the tool to direct `read_file(path)` on the `sibling_path_pivot` plus `parent_escape` subset; and
  - keep the retained prompt-only, conservative, and external-control comparators in place
- artifact paths:
  - `artifacts/stage8_read_file_widening/tool_gate/summary.json`
  - `artifacts/stage8_read_file_widening/qwen7b_readfile_full_v2/summary.json`
  - `artifacts/stage8_read_file_widening/hermes3_readfile_full_v2/summary.json`
  - `reports/stage8_tool_gate.md`
  - `reports/stage8_qwen7b_readfile_full_v2_read_file_widening.md`
  - `reports/stage8_hermes3_readfile_full_v2_read_file_widening.md`
- retained interpretation:
  - `Qwen/Qwen2.5-7B-Instruct` preserves the same TSIR separation on the second-tool subset
  - `NousResearch/Hermes-3-Llama-3.1-8B` keeps TSIR safe and complete there as well, but `structured_context_prompt` matches TSIR on that second-tool subset
  - the paper may therefore mention second-tool upper-bound evidence for path authority, but must not promote a second-tool headline claim
- falsifier:
  - if a later second-family second-tool rerun restores TSIR distinctiveness against retained prompt-only controls, the tool-width claim should be reconsidered rather than kept permanently boundary-only

## Known adverse evidence

- `warning_prompt` restores clean completion on all widened rows but remains unsafe on every attacked row.
- In the widened 80-row claim package, `structured_context_prompt` is materially stronger than `warning_prompt`, but it still leaves `32/40` attacked rows unsafe and reaches only `8/40` attacked completion.
- In the widened 80-row claim package, `dynamic_schema_constraint` preserves final-call safety but reaches only `3/40` attacked completion and `37` no-call rows.
- In the widened 80-row claim package, `authorized_subtree_reject` preserves final-call safety but reduces all `40/40` attacked rows to no-call failures.
- `fixed_allowlist` remains unsafe on every attacked row in the widened 80-row claim package even though it preserves clean completion.
- `score_fusion_proxy` remains unsafe on all `root_widen_hidden` and `sibling_path_pivot` attacks, and preserves safety on `parent_escape` only by denying those attacks.
- In Stage 7, `Qwen/Qwen2.5-0.5B-Instruct` preserves TSIR final-call safety but drops to `33/40` attacked completion and `12/40` clean completion, so it remains boundary evidence rather than widening support.
- In Stage 7, `NousResearch/Hermes-3-Llama-3.1-8B` preserves the headline TSIR gate, but the retained baselines still separate materially there: `structured_context_prompt` remains unsafe on `10/40` attacked rows, `dynamic_schema_constraint` reaches only `14/40` attacked completion, and `authorized_subtree_reject` remains at `0/40`.
- In Stage 8, `Qwen/Qwen2.5-7B-Instruct` preserves the same second-tool separation on direct `read_file(path)`, but on `NousResearch/Hermes-3-Llama-3.1-8B` the prompt-only `structured_context_prompt` matches TSIR on the 30 attacked and 30 clean second-tool subset, so tool-width broadening remains boundary-only.
