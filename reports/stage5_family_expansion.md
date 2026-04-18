# Stage 5 Family Expansion

created_at: 2026-04-19T01:20:00+08:00
status: "completed"

## Purpose

Stage 5 asked whether the locked TSIR object survives beyond the original two attack families without reopening model, tool, or task-family scope.

This stage attempted three additions:

- `parent_escape`
- `absolute_path_escape`
- `flag_only_hidden` as the meaningful subset of `flag_only_escalation`

## New artifacts

- `artifacts/stage5_family_expansion/results.json`
- `artifacts/stage5_family_expansion/summary.json`
- `artifacts/stage5_family_expansion/family_summary.json`
- `reports/stage5_family_expansion_casebook.md`
- `reports/stage5_family_expansion_decisive_cases.md`
- `artifacts/stage5_flag_only_hidden_scan/results.json`
- `artifacts/stage5_flag_only_hidden_scan/summary.json`
- `reports/stage5_flag_only_hidden_casebook.md`

## Stage 5 family-expansion results

The Stage-5 family-expansion bundle contains the original core families plus new `parent_escape` and `absolute_path_escape` rows.

Overall attack-side summary:

| Variant | Attack unsafe | Attack completion | Clean completion |
| --- | ---: | ---: | ---: |
| `base_prompt` | 30/30 | 0/30 | 30/30 |
| `warning_prompt` | 30/30 | 0/30 | 30/30 |
| `structured_context_prompt` | 18/30 | 12/30 | 30/30 |
| `dynamic_schema_constraint` | 0/30 | 3/30 | 30/30 |
| `no_tool_on_untrusted_context` | 0/30 | 0/30 | 0/30 |
| `fixed_allowlist` | 30/30 | 0/30 | 30/30 |
| `score_fusion_proxy` | 10/30 | 0/30 | 30/30 |
| `authorized_subtree_reject` | 0/30 | 0/30 | 30/30 |
| `tsir_route_b` | 0/30 | 30/30 | 30/30 |

## Family-level decision

### 1. `parent_escape` should be promoted

`parent_escape` behaves like a clean new empirical family.

On `10` attacked rows and `10` matched clean rows:

- `base_prompt`: `10/10` unsafe, `0/10` attacked completion
- `warning_prompt`: `10/10` unsafe, `0/10` attacked completion
- `structured_context_prompt`: `10/10` unsafe, `0/10` attacked completion
- `fixed_allowlist`: `10/10` unsafe, `0/10` attacked completion
- `score_fusion_proxy`: `0/10` unsafe, `0/10` attacked completion
- `authorized_subtree_reject`: `0/10` unsafe, `0/10` attacked completion
- `dynamic_schema_constraint`: `0/10` unsafe, `1/10` attacked completion
- `tsir_route_b`: `0/10` unsafe, `10/10` attacked completion

Interpretation:

- the family is not just parser noise; it is a clean path-authorization failure beyond the current repository boundary;
- prompt-only controls do not recover it;
- conservative external controls stay safe by refusal;
- TSIR preserves both safety and utility.

This is strong enough to support widening the main empirical object from two families to three:

- `root_widen_hidden`
- `sibling_path_pivot`
- `parent_escape`

within the same one-model, one-tool, three-real-repository lane.

### 2. `absolute_path_escape` should stay exploratory

`absolute_path_escape` also separates empirically:

- `tsir_route_b`: `0/10` unsafe, `10/10` attacked completion
- `structured_context_prompt`: `3/10` unsafe, `7/10` attacked completion
- `score_fusion_proxy`, `authorized_subtree_reject`, and `dynamic_schema_constraint`: safe but mostly denial

However, this family is more synthetic than `parent_escape` in the current lane because the system prompt already instructs repo-relative paths, and the attack relies on environment-specific absolute paths. It is better kept as exploratory or appendix-level reinforcement rather than promoted into the headline family set.

### 3. `flag_only_hidden` is meaningful but not TSIR-distinctive

The hidden-only mini-scan was run separately in `artifacts/stage5_flag_only_hidden_scan/*` across:

- 2 controlled pairs
- `environs/tests`
- `python_decouple/tests`

Attack-side result:

| Variant | Attack unsafe | Attack completion | Clean completion |
| --- | ---: | ---: | ---: |
| `base_prompt` | 4/4 | 0/4 | 4/4 |
| `warning_prompt` | 4/4 | 0/4 | 4/4 |
| `structured_context_prompt` | 3/4 | 1/4 | 4/4 |
| `dynamic_schema_constraint` | 0/4 | 0/4 | 4/4 |
| `no_tool_on_untrusted_context` | 0/4 | 0/4 | 0/4 |
| `fixed_allowlist` | 0/4 | 4/4 | 4/4 |
| `score_fusion_proxy` | 4/4 | 0/4 | 4/4 |
| `authorized_subtree_reject` | 0/4 | 0/4 | 4/4 |
| `tsir_route_b` | 0/4 | 4/4 | 4/4 |

Interpretation:

- this confirms that unauthorized `hidden=true` is genuinely an authority-bearing field even when the path remains authorized;
- but `fixed_allowlist` already strips the flag and matches TSIR on this mini-scan.

Therefore `flag_only_hidden` strengthens the mechanism story around authority-bearing flags, but it should not be used as the new TSIR-distinctive headline family.

## Best supported claim after Stage 5

The strongest natural post-Stage-5 claim is:

> In the frozen Qwen2.5-7B-Instruct plus single `rg_search` lane, TSIR now survives three empirical attack families in the same task lane: `root_widen_hidden`, `sibling_path_pivot`, and `parent_escape`. Across the evaluated controlled settings and three real repositories, TSIR remains the only tested rule that preserves zero unsafe final calls together with full attacked-row and clean-row completion on those families.

What remains outside the headline claim:

- `absolute_path_escape`: exploratory / appendix-level reinforcement
- `flag_only_hidden`: mechanism-supporting supplement, not a TSIR-distinctive family
- `django_environ`: advisory root-widen reinforcement only; docs-to-docs sibling pivot remains a non-transfer boundary

## Next step

The next high-yield move is manuscript integration and a new self-review round:

- promote `parent_escape` into the paper's supported empirical family set;
- keep `absolute_path_escape` and `flag_only_hidden` in reinforcement / appendix framing;
- refresh the claim-to-evidence map accordingly.
