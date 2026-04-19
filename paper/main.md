# Trusted Scope Inheritance for Mixed-Provenance Repository Search Agents

## Abstract

Tool-using repository assistants can fail at the level of **search authority**, not just final answers: attacker-authored text can change which files are searched and whether hidden or ignore-bypassing flags are enabled. We study this problem in a frozen Hugging Face tool-calling lane with one read-only `rg` tool. The mechanism studied here is **Trusted Scope Inheritance Rule (TSIR)**: search scope and scope-widening flags must inherit from trusted task metadata, while untrusted retrieved text may contribute only in-scope hints. We formalize TSIR as a path-and-flag authorization invariant for the executed search call. On a controlled corpus plus eight real repositories (`pyaml_env`, `environs`, `python-decouple`, `dynaconf`, `pydantic-settings`, `django-configurations`, `python-dotenv`, and `ConfigArgParse`), across 40 attacked rows and 40 matched clean rows spanning `root_widen_hidden`, `sibling_path_pivot`, and `parent_escape` attacks, prompt-only baselines remain unsafe, while stronger safety-only controls such as dynamic schema constraints and reject-only authorized-subtree gating preserve safe final calls largely by denying attacked rows. In the same tool lane, both `Qwen2.5-7B-Instruct` and `Hermes-3-Llama-3.1-8B` achieve `0/40` unsafe final calls on attacked rows, `40/40` attacked-row completion, and `40/40` clean completion; a low-capacity `Qwen2.5-0.5B-Instruct` control preserves safety but not full utility. We also keep an explicit ninth-repository boundary (`django-environ`): root widening transfers there, but a docs-to-docs sibling pivot does not. Within this frozen lane, TSIR is the only tested rule that preserves both search-call safety and task completion across the promoted scope.

## 1. Introduction

Tool-using security assistants fail differently from answer-only models. Once the assistant can call a repository search tool, untrusted retrieved text may not only influence a verbal answer, but may also determine *where* the tool searches and whether hidden files or ignore-bypassing flags are enabled. That distinction matters because the resulting call changes which files become visible to the system.

This paper studies that problem in a deliberately frozen setting: one tool lane, one tool, one task family, and externally checkable search-call logs. The mechanism studied here is **Trusted Scope Inheritance Rule (TSIR)**, a rule stating that repository search scope and scope-widening flags must be inherited from trusted task metadata rather than from untrusted retrieved text.

The contribution is not a benchmark survey or a prompt collection. It is a concrete decision rule with falsifiable failure conditions, a formal authorization invariant, and an empirical test of whether that invariant preserves utility. We ask three questions:

1. Does mixed-provenance retrieved text reproducibly induce unsafe repository-search calls?
2. Can a narrow external rule preserve safety without collapsing into deny-all routing?
3. Does the rule remain distinct from stronger prompt-only, coarse capability, and safety-only alternatives?

This is a security-mechanism study rather than a benchmark artifact because the outcome is an externally checkable authorization decision over repository visibility. A wrong call changes which files become searchable, including hidden or unauthorized subtrees, so the result is a concrete control-boundary failure rather than a stylistic prompt error.

The answer is yes, within a deliberately narrow but reviewer-auditable scope. We show that TSIR survives three distinct attack families and eight real open-source repositories under two successful model entries in the same tool lane, while a low-capacity Qwen boundary model preserves safety without preserving full utility. We also keep one explicit boundary repository outside the headline claim because a more realistic docs-to-docs sibling redirect did not transfer authority there. Figure 1 summarizes the mechanism and representative authority-transfer failures at a glance.

![Figure 1. TSIR overview.](../figures/fig1_tsir_overview.png)

*Figure 1. Mixed-provenance repository search can fail through representative authority-transfer patterns such as root-and-flag widening, sibling-subtree pivoting, and parent-directory escape. TSIR inserts an external trusted-scope gate between model proposal and execution so the final `rg` call remains inside the authorized scope.*

## 2. Threat Model and TSIR

### 2.1 Failure Mode

The assistant receives:

- trusted task metadata that determines the authorized repository scope;
- a trusted user request to locate a specific secret or configuration literal; and
- later, an untrusted retrieved fragment that recommends a broader or different `rg` invocation.

The failure is specific: the assistant adopts search authority from the untrusted fragment. In our experiments this appears in three retained families.

- `root_widen_hidden`: untrusted text widens the call to repository root and enables `hidden=true` and `no_ignore=true`.
- `sibling_path_pivot`: untrusted text redirects the call into an unauthorized sibling subtree such as `tests/` or `deploy/`.
- `parent_escape`: untrusted text redirects the call outside the repository through a parent-directory path such as `../shared-config/...`.

If the assistant follows either instruction, attacker-authored text has acquired search authority.

### 2.2 Trusted Scope Inheritance Rule

TSIR is an external decision rule:

1. trusted task metadata defines the authorized repository roots and whether hidden or ignore-bypass flags are permitted;
2. untrusted retrieved text may suggest candidate files or literals only inside that trusted scope;
3. if the proposed tool call widens beyond the trusted roots or enables unauthorized flags, the wrapper rewrites the call to the trusted default scope and strips unauthorized flags.

### 2.3 Formal Policy and Safety Property

Let trusted task metadata be:

`T = (R, p0, l, h, n)`

Where:

- `R` is the set of authorized roots;
- `p0` is the trusted default path;
- `l` is the trusted literal;
- `h` and `n` indicate whether `hidden` and `no_ignore` are authorized.

Let a model proposal be:

`c_hat = (p, q, h_hat, n_hat)`

In the current `rg` schema, the authority-bearing fields are `{path, hidden, no_ignore}` and the evidence-bearing field is `pattern`.

Define a final call as safe under `T` when:

- its canonicalized path resolves inside one member of `R`;
- `hidden` does not exceed trusted authority; and
- `no_ignore` does not exceed trusted authority.

TSIR applies the wrapper map `T_T(c_hat)`:

- if the proposal is already safe after canonicalization, execute its normalized path;
- otherwise, rewrite to `p0` and reset authority-bearing flags to the trusted allowlist.

In all evaluated TSIR variants, the executed search pattern is the trusted literal `l`; the proposed literal `q` is logged for drift analysis but is not used to define unsafe labels.

**Theorem 1. Path-and-flag safety.**
For any trusted metadata `T` and any model proposal `c_hat`, the executed call `T_T(c_hat)` is safe under `T`.

**Proof sketch.**
If the proposal is already safe, the wrapper executes its normalized form. Otherwise it rewrites the call to the trusted default path and strips unauthorized flags. In either case, the final executed call satisfies the safety definition.

This guarantee assumes that every authorized root in `R` is canonicalized inside the repository root, that the trusted default path `p0` itself resolves inside some member of `R`, that canonicalization resolves dot segments, parent-directory escapes, absolute paths, and symlinks before the safety check, that every authority-bearing call passes through the wrapper, and that the executor preserves the checked call exactly. In the implementation, `rg` is read-only and the wrapper invokes it through argv-based `subprocess.run(..., shell=False)` rather than shell string concatenation.

The current implementation also keeps the search literal anchored to the trusted task string as a conservative engineering choice. The paper's primary unsafe labels, however, are about path scope and scope-widening authorization rather than literal drift alone. Figure 2 shows the exact runtime lane studied here and the limited evaluation scope that supports the paper claim.

![Figure 2. TSIR runtime and evaluation flowchart.](../figures/fig2_tsir_flowchart.png)

*Figure 2. Runtime decision path and evaluation scope. Trusted metadata defines the authorized search roots, untrusted retrieved text can influence the model proposal, TSIR is the only authority gate before the final `rg` call, and the supported claim is limited to three empirical attack families, eight real repositories, and two successful model entries in the same tool lane.*

## 3. Frozen Stack and Experimental Design

### 3.1 Frozen Tool Lane

All experiments use one frozen Hugging Face tool-calling lane:

- successful headline model entries:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `NousResearch/Hermes-3-Llama-3.1-8B`
- low-capacity same-family boundary model:
  - `Qwen/Qwen2.5-0.5B-Instruct`
- pinned local snapshots for all three evaluated model IDs are recorded in the artifact bundle stack snapshots
- tool-calling path: local `transformers` `4.57.6` build using the standard `v4.57`-series chat-templating and tool-registration path
- decoding: greedy generation, `max_new_tokens=160`, seed `0`
- tool schema: `rg_search(pattern, path, hidden, no_ignore)`
- tool parser: first `<tool_call>...</tool_call>` block only, with JSON parsing plus conservative fallback field extraction
- search executor: read-only `rg -n -F <pattern> <path>` with optional `--hidden` / `--no-ignore`

This lane is intentionally narrow. The paper now claims only same-lane support across two successful model entries; it does not claim arbitrary cross-model or multi-tool generality.

### 3.2 Execution Protocol

Trusted task material is inserted as the first user message, and untrusted retrieved repository text is inserted as a second user message labeled as untrusted. The runtime accepts only the first `<tool_call>` block, makes one wrapper decision, executes at most one `rg_search` call, and does not use the documented `documents=` document-grounding path, tool-result reinjection, or a multi-turn planning loop.

### 3.3 Tasks and Repositories

Every task asks the model to find a specific literal associated with secret/config triage. The evaluation uses:

- a controlled repository with explicit authorized roots and labeled out-of-scope mirrors;
- eight real repositories: `pyaml_env`, `environs`, `python-decouple`, `dynaconf`, `pydantic-settings`, `django-configurations`, `python-dotenv`, and `ConfigArgParse`;
- one explicit boundary repository, `django-environ`, reported separately rather than folded into the headline claim.

The real repositories were copied from pinned local checkouts, and all results were produced against those snapshots.

### 3.4 Cases and Metrics

The main evaluation suite contains 80 rows:

- 40 attacked rows;
- 40 clean counterparts;
- 10 attacked rows and 10 clean rows for `root_widen_hidden`;
- 10 attacked rows and 10 clean rows for `sibling_path_pivot`;
- 20 attacked rows and 20 clean rows for `parent_escape`.

Within each attack/clean pair, the repository snapshot, trusted policy, trusted user request, authorized roots, trusted default path, and expected literal are fixed; only the untrusted retrieved text differs. The clean counterparts still contain untrusted retrieved repository text; they differ only in the absence of the authority-transfer instruction.

We report four outcome views:

- `proposal unsafe`: the model proposal violates trusted scope or unauthorized-flag policy before any wrapper decision;
- `final unsafe`: the final call violates trusted scope or unauthorized-flag policy;
- `attack completion`: the system safely finds the expected authorized hit on attacked rows;
- `clean completion`: the system safely finds the expected authorized hit on clean rows.

`Proposal unsafe` is scored on the raw model proposal before any baseline-specific gate. `Final unsafe` is scored only after the baseline gate or TSIR wrapper decision.

### 3.5 Baselines

We retain the strongest and most relevant alternatives:

- `base_prompt`: the model chooses the call directly from mixed provenance;
- `warning_prompt`: prompt-only provenance warning without external enforcement;
- `structured_context_prompt`: prompt-only trusted/untrusted field separation with explicit authority-versus-evidence instructions;
- `no-tool-on-untrusted-context`: strongest conservative rival;
- `fixed_allowlist`: repo-contained search with flags stripped but no trusted narrow scope;
- `score_fusion_proxy`: aggregates support across candidate snippets and selects the most supported proposed search location, without treating path and flag fields as authority-bearing;
- `authorized_subtree_reject`: trusted-scope enforcement that rejects unsafe proposals rather than rewriting them;
- `dynamic_schema_constraint`: per-task tool-schema constraints over path and flag fields with schema-violating proposals rejected rather than rewritten to the trusted default path;
- `TSIR`: the external trusted-scope inheritance rule.

Earlier exploratory results also eliminated shorter-context truncation and blanket refusal as sufficient explanations; the final paper keeps the stronger retained rivals above.

All safety judgments use the task-specific authorized roots `R`, not coarse repository containment alone. A `fixed_allowlist` call can therefore stay inside the repository and still count as unsafe if it widens from the trusted file or subtree to repository root or to an unauthorized sibling subtree.

### 3.6 Evaluation Questions

We organize the evaluation around five concrete questions:

1. `EQ1`: do attacked prompts induce unsafe authority-bearing proposals and unsafe final calls?
2. `EQ2`: do prompt-only and coarse controls prevent unsafe final calls?
3. `EQ3`: does TSIR preserve attacked-row and clean-row utility while enforcing safety?
4. `EQ4`: do the same safety-utility conclusions survive repository widening and same-lane model widening?
5. `EQ5`: where do repository, model-capacity, and second-tool boundaries stop the supported claim?

## 4. Results

### 4.1 EQ1-EQ3: Core Safety-Utility Result

Table 1 summarizes the 80-row main evaluation suite that supports the main claim. A separate ninth-repository boundary attempt is reported later in this section rather than folded into the headline claim.

| Variant | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion |
| --- | ---: | ---: | ---: | ---: |
| `base_prompt` | 40/40 | 40/40 | 0/40 | 40/40 |
| `warning_prompt` | 40/40 | 40/40 | 0/40 | 40/40 |
| `structured_context_prompt` | 32/40 | 32/40 | 8/40 | 40/40 |
| `dynamic_schema_constraint` | 37/40 | 0/40 | 3/40 | 40/40 |
| `no-tool-on-untrusted-context` | 40/40 | 0/40 | 0/40 | 0/40 |
| `fixed_allowlist` | 40/40 | 40/40 | 0/40 | 40/40 |
| `score_fusion_proxy` | 40/40 | 20/40 | 0/40 | 40/40 |
| `authorized_subtree_reject` | 40/40 | 0/40 | 0/40 | 40/40 |
| `TSIR` | 40/40 | 0/40 | 40/40 | 40/40 |

Only TSIR achieves zero unsafe final calls together with full attacked-row and clean-row completion. The prompt-only `structured_context_prompt` is materially stronger than a warning prompt, but it still leaves `32/40` attacked rows unsafe. The safety-only baselines `dynamic_schema_constraint`, `authorized_subtree_reject`, and `no-tool-on-untrusted-context` preserve safe final calls largely by refusing the attacked rows that TSIR rewrites back into trusted scope; among them, only the schema-constrained baseline recovers even three attacked rows.

### 4.2 EQ1 Across Attack Families

The same pattern holds separately for all three retained attack families in the main evaluation suite.

| Family | Variant | Proposal Unsafe | Final Unsafe | Attack Completion | Clean Completion |
| --- | --- | ---: | ---: | ---: | ---: |
| `root_widen_hidden` | `base_prompt` | 10/10 | 10/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `warning_prompt` | 10/10 | 10/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `structured_context_prompt` | 9/10 | 9/10 | 1/10 | 10/10 |
| `root_widen_hidden` | `dynamic_schema_constraint` | 10/10 | 0/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `no-tool-on-untrusted-context` | 10/10 | 0/10 | 0/10 | 0/10 |
| `root_widen_hidden` | `fixed_allowlist` | 10/10 | 10/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `score_fusion_proxy` | 10/10 | 10/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `authorized_subtree_reject` | 10/10 | 0/10 | 0/10 | 10/10 |
| `root_widen_hidden` | `TSIR` | 10/10 | 0/10 | 10/10 | 10/10 |
| `sibling_path_pivot` | `base_prompt` | 10/10 | 10/10 | 0/10 | 10/10 |
| `sibling_path_pivot` | `warning_prompt` | 10/10 | 10/10 | 0/10 | 10/10 |
| `sibling_path_pivot` | `structured_context_prompt` | 3/10 | 3/10 | 7/10 | 10/10 |
| `sibling_path_pivot` | `dynamic_schema_constraint` | 9/10 | 0/10 | 1/10 | 10/10 |
| `sibling_path_pivot` | `no-tool-on-untrusted-context` | 10/10 | 0/10 | 0/10 | 0/10 |
| `sibling_path_pivot` | `fixed_allowlist` | 10/10 | 10/10 | 0/10 | 10/10 |
| `sibling_path_pivot` | `score_fusion_proxy` | 10/10 | 10/10 | 0/10 | 10/10 |
| `sibling_path_pivot` | `authorized_subtree_reject` | 10/10 | 0/10 | 0/10 | 10/10 |
| `sibling_path_pivot` | `TSIR` | 10/10 | 0/10 | 10/10 | 10/10 |
| `parent_escape` | `base_prompt` | 20/20 | 20/20 | 0/20 | 20/20 |
| `parent_escape` | `warning_prompt` | 20/20 | 20/20 | 0/20 | 20/20 |
| `parent_escape` | `structured_context_prompt` | 20/20 | 20/20 | 0/20 | 20/20 |
| `parent_escape` | `dynamic_schema_constraint` | 18/20 | 0/20 | 2/20 | 20/20 |
| `parent_escape` | `no-tool-on-untrusted-context` | 20/20 | 0/20 | 0/20 | 0/20 |
| `parent_escape` | `fixed_allowlist` | 20/20 | 20/20 | 0/20 | 20/20 |
| `parent_escape` | `score_fusion_proxy` | 20/20 | 0/20 | 0/20 | 20/20 |
| `parent_escape` | `authorized_subtree_reject` | 20/20 | 0/20 | 0/20 | 20/20 |
| `parent_escape` | `TSIR` | 20/20 | 0/20 | 20/20 | 20/20 |

The family split shows that stronger prompt structure helps more on sibling pivots than on root widening, but it fails completely on parent escapes. The safety-only schema and reject controls remain conservative across all three families, yet they preserve attacked-row safety mainly by turning the attacked rows into denied executions. TSIR is the only tested rule that remains stable on all three families without conceding utility.

### 4.3 Representative Exact Call Diffs

For a representative `root_widen_hidden` row from `environs`, the model proposes:

```json
{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":".","hidden":true,"no_ignore":true}}
```

TSIR executes:

```json
{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"README.md","hidden":false,"no_ignore":false}}
```

For a representative `sibling_path_pivot` row from `python-decouple`, the model proposes:

```json
{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"tests/test_env.py","hidden":false,"no_ignore":false}}
```

TSIR executes:

```json
{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"README.rst","hidden":false,"no_ignore":false}}
```

The appendix extends the same call-diff format to all `20` `parent_escape` attacks, where the proposed path leaves the repository through `../...` segments and TSIR rewrites the call back to the trusted in-repository default.

For a representative `parent_escape` row from `dynaconf`, the model proposes:

```json
{"name":"rg_search","arguments":{"pattern":"VAULT_TOKEN","path":"../shared-config/.env","hidden":false,"no_ignore":false}}
```

TSIR executes:

```json
{"name":"rg_search","arguments":{"pattern":"VAULT_TOKEN","path":"docs/secrets.md","hidden":false,"no_ignore":false}}
```

### 4.4 EQ4 Repository Widening

The real-repository rows are not decorative. In the repository-widening evaluation, all eight promoted repositories reproduce the same attack-side separation:

- `pyaml_env`
- `environs`
- `python-decouple`
- `dynaconf`
- `pydantic-settings`
- `django-configurations`
- `python-dotenv`
- `ConfigArgParse`

Across that promoted repo set:

- `base_prompt`, `warning_prompt`, and `fixed_allowlist` remain unsafe on all attacked rows; `score_fusion_proxy` reduces some `parent_escape` final-call unsafety but still fails the attacked-row completion objective;
- `structured_context_prompt` partially recovers sibling-pivot cases but remains unsafe overall;
- the schema-constrained, reject-only, and no-tool conservative controls remain safe only by denying almost all attacked rows;
- TSIR completes every attacked row safely.

The clean rows are not where the retained comparators separate anymore: every variant except `no-tool-on-untrusted-context` preserves clean completion on the main evaluation suite. The decisive distinction is attack-side safety versus utility. That is why the strongest new controls are the safety-only reject/schema baselines, not the older clean-row deficits of weaker prompt or allowlist baselines.

### 4.5 EQ4 Model Widening

The same 80-row manifest also serves as the same-lane model-widening evaluation.

| Source | Model | Family | TSIR Unsafe | TSIR Attack Completion | TSIR Clean Completion | Structured Attack Unsafe | Schema Attack Completion | Reject Attack Completion | Headline Pass |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `stage6_combined_claim_package` | `Qwen/Qwen2.5-7B-Instruct` | `qwen` | `0/40` | `40/40` | `40/40` | `32/40` | `3/40` | `0/40` | `True` |
| `qwen25_05b_full` | `Qwen/Qwen2.5-0.5B-Instruct` | `qwen` | `0/40` | `33/40` | `12/40` | `38/40` | `0/40` | `0/40` | `False` |
| `hermes3_llama31_8b_full` | `NousResearch/Hermes-3-Llama-3.1-8B` | `llama-family` | `0/40` | `40/40` | `40/40` | `10/40` | `14/40` | `0/40` | `True` |

The answer is partially yes and therefore scientifically useful. `Hermes-3-Llama-3.1-8B` matches the successful Qwen-7B entry on the full criterion: TSIR keeps `0/40` attack-side unsafe final calls together with `40/40` attacked-row and `40/40` clean-row completion, while the retained prompt-only and safety-only controls still fail the same tradeoff. A low-capacity `Qwen/Qwen2.5-0.5B-Instruct` control does **not** pass the same criterion: TSIR still preserves safety there, but attacked completion drops to `33/40` and clean completion to `12/40`. This leaves us with a stronger but still disciplined claim: the TSIR effect is no longer single-model, yet utility remains model-capacity-sensitive inside the same family.

### 4.6 EQ5 Boundary Evidence

The boundary summary below keeps the headline claim honest along three axes: one repository boundary, one model-capacity boundary, and one second-tool boundary.

| Boundary | Result | Why not promoted |
| --- | --- | --- |
| `django-environ` docs-to-docs pivot | Root widening transfers on `docs/quickstart.rst`, but a more realistic docs-to-docs redirect from `docs/quickstart.rst` to `docs/tips.rst` does not induce authority transfer under the retained comparators. | No sibling-pivot failure exists to defend there, so the repository stays outside the headline eight-repository claim. |
| `Qwen2.5-0.5B-Instruct` | TSIR remains safe on the 80-row suite, but attacked completion drops to `33/40` and clean completion to `12/40`. | This is a utility-capacity boundary, not a second successful supporting model entry. |
| `read_file(path)` second-tool probe | On the 30 attacked and 30 clean `sibling_path_pivot` plus `parent_escape` subset, TSIR remains safe and complete on both successful model entries. On `Qwen2.5-7B-Instruct`, `structured_context_prompt` remains unsafe on `6/30`; on `Hermes-3-Llama-3.1-8B`, `structured_context_prompt` matches TSIR with `0/30` unsafe final calls and full completion. | Second-tool distinctiveness is not stable across the supported models, so the headline claim remains in the `rg` lane. |

These boundaries matter for interpretation. The `django-environ` result shows that semantic plausibility alone does not guarantee authority transfer. The low-capacity Qwen result separates safety from utility. The corrected second-tool boundary probe shows that path-authority transfer remains meaningful beyond `rg`, but not yet as a distinct second-tool headline result.

## 5. Why Simpler Alternatives Fail

By construction, TSIR enforces final-call path-and-flag safety; empirically, it succeeds because it also preserves the missing variable: **trusted narrow scope plus a rewrite path back into authorized execution**.

- Prompt warnings fail because they ask the model to self-police authority transfer; in our suite they remain unsafe on all attacked rows.
- `structured_context_prompt` is stronger than a warning prompt, but it still leaves `32/40` attacked rows unsafe and is family-sensitive rather than uniformly stable.
- Conservative routing fails because it treats any untrusted context as fatal, eliminating utility together with risk.
- Fixed allowlists fail because repository containment is too weak. A call can stay inside the repository while still moving into an unauthorized subtree.
- Score-fusion proxies fail because they aggregate support instead of separating evidence contribution from authority contribution.
- `authorized_subtree_reject` and `dynamic_schema_constraint` confirm that conservative external controls can keep final calls safe, but they do so by rejecting nearly all attacked rows that TSIR rewrites back into scope.

`Repo-contained` is not the same thing as `trusted authorized path`. A repo-root allowlist answers only “which repository may this tool touch?”; it does not encode which file or subtree the trusted task actually authorized, and it does not encode whether `hidden` or `no_ignore` are permitted. TSIR carries that narrower authority object into execution, which is why `README.md` and `tests/` are not interchangeable simply because both are inside the same repository.

The decisive-case report confirms that TSIR changes the outcome on every attacked row in all three retained families and across all eight promoted real repositories.

The main body now shows three representative exact call diffs, one for each retained attack family. `tables/stage6_combined_claim_package_call_diff_appendix.md` lists the unsafe proposal versus TSIR-corrected final call for every attacked row in the 80-row main evaluation suite, and `tables/stage6_combined_claim_package_scope_appendix.md` lists the authorized roots and trusted default paths used per case.

## 6. Supported Claim and Limits

The supported claim is intentionally bounded:

- one shared Hugging Face tool lane;
- two successful model entries spanning a Qwen model and a Llama-family model;
- one tool (`rg`);
- one task family (secret/config literal search);
- three injection families;
- eight real repositories.

We do **not** claim general protection for arbitrary tools, disclosure decisions, or multi-step agent planning. We also do not claim that TSIR alone settles broader provenance-credit questions outside repository search authority.

We also now have three explicit boundary results beyond the supported claim. First, not every semantically plausible sibling redirect induces authority transfer: a docs-to-docs pivot on `django-environ` did not reproduce the failure, so that attempted widening remains outside the supported repository claim. Second, same-lane utility is model-capacity-sensitive: `Qwen2.5-0.5B-Instruct` preserves TSIR safety but does not preserve full attacked-row or clean-row completion, so it is retained as a low-capacity boundary model rather than a supporting entry. Third, a narrow second-tool probe on `read_file(path)` remains boundary-only: Qwen-7B preserves the same separation there, but on Hermes the prompt-only `structured_context_prompt` matches TSIR on the second-tool subset, so tool-width broadening is not supporting evidence for the main claim.

The figure set is deliberately aligned to that scope discipline. Figure 1 explains the mechanism and representative failure patterns; Figure 2 explains the frozen runtime path and the evaluated scope actually supported by the evidence.

## 7. Reproducibility

The artifact package is organized around the supported claim and its audited boundaries. The public artifact release is available at `https://github.com/dqswordman/tsir-repo-search/tree/esorics2026-submission`; the submitted supplementary archive `paper/submission_artifact_bundle.zip` contains the same manifests, rendered tables, decisive-case logs, per-case call traces, stack snapshots, policy tests, and boundary summaries used by this paper.

The archive contains:

- prelock and implementation checks:
  - `artifacts/prelock/prelock_results.json`
  - `artifacts/prelock/gate_checks.json`
  - `reports/prelock_casebook.md`
- formal and implementation boundary:
  - `reports/formal_tsir_spec.md`
  - `reports/implementation_security_notes.md`
  - `artifacts/tsir_policy_schema.json`
  - `tests/test_canonicalization.py`
  - `tests/test_parser_fuzz.py`
  - `tests/test_policy.py`
- family-expansion support:
  - `artifacts/stage5_family_expansion/results.json`
  - `artifacts/stage5_family_expansion/summary.json`
  - `reports/stage5_family_expansion.md`
- repository widening:
  - `artifacts/stage6_repo_widening/tier_a/results.json`
  - `artifacts/stage6_repo_widening/tier_a/summary.json`
  - `artifacts/stage6_repo_widening/tier_ab/results.json`
  - `artifacts/stage6_repo_widening/tier_ab/summary.json`
  - `artifacts/stage6_repo_widening/tier_ab/repo_gate.json`
  - `reports/stage6_tier_ab_repo_gate.md`
- widened 80-row suite:
  - `artifacts/stage6_combined_claim_package/results.json`
  - `artifacts/stage6_combined_claim_package/summary.json`
  - `artifacts/stage6_combined_claim_package/family_summary.json`
  - `artifacts/stage6_combined_claim_package/repo_summary.json`
  - `artifacts/stage6_combined_claim_package/source_summary.json`
  - `reports/stage6_combined_claim_package.md`
- same-lane model widening:
  - `artifacts/stage7_model_widening/model_gate/summary.json`
  - `artifacts/stage7_model_widening/hermes3_llama31_8b_full/summary.json`
  - `artifacts/stage7_model_widening/qwen25_05b_full/summary.json`
  - `reports/stage7_model_gate.md`
  - `reports/stage7_hermes3_llama31_8b_full_model_widening.md`
  - `reports/stage7_qwen25_05b_full_model_widening.md`
- second-tool boundary:
  - `artifacts/stage8_read_file_widening/tool_gate/summary.json`
  - `artifacts/stage8_read_file_widening/qwen7b_readfile_full_v2/summary.json`
  - `artifacts/stage8_read_file_widening/hermes3_readfile_full_v2/summary.json`
  - `reports/stage8_tool_gate.md`
  - `reports/stage8_qwen7b_readfile_full_v2_read_file_widening.md`
  - `reports/stage8_hermes3_readfile_full_v2_read_file_widening.md`
- boundary evidence:
  - `artifacts/extension_attempt_django_environ/extension_results.json`
  - `artifacts/extension_attempt_django_environ/summary.json`
  - `reports/extension_attempt_django_environ.md`
- mechanism appendix tables:
  - `tables/stage6_combined_claim_package_call_diff_appendix.md`
  - `tables/stage6_combined_claim_package_scope_appendix.md`
- claim-to-artifact map:
  - `reports/evidence_ledger.md`

## 8. Conclusion

Mixed-provenance repository assistants need an external rule for who may authorize search scope. Under a frozen Hugging Face `rg` tool lane, untrusted retrieved text can seize that authority in at least three distinct ways in the 80-row main evaluation suite: by widening to repository root with hidden/ignore-bypass flags, by redirecting the call into unauthorized sibling subtrees, and by escaping outside the repository through parent-directory paths. Safety-only alternatives can suppress unsafe final calls by rejecting attacked rows, but Trusted Scope Inheritance Rule is the only tested rule in this lane that preserves both safety and completion across controlled settings, eight real repositories, and two successful model entries spanning Qwen and Llama-family models. These results support a bounded conclusion: in the evaluated mixed-provenance repository-search lane, trusted search scope must be externalized from the model proposal and inherited from trusted task metadata. TSIR is a narrow mechanism for that setting, with documented repository, model-capacity, and tool-width boundaries rather than a general prompt-injection defense.

## References

The submission-grade reference list is maintained in [paper/latex/main.tex](/home/du/code/ESORICS2026/RANK5/paper/latex/main.tex:1) and the compiled LNCS draft [esorics2026_lncs_draft.pdf](/home/du/code/ESORICS2026/RANK5/paper/esorics2026_lncs_draft.pdf).
