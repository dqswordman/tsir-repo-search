# Implementation Security Notes

created_at: 2026-04-18T22:20:00+08:00
status: "stage-2 wrapper hardening"

## Current implementation boundary

The repository now centralizes the current `TSIR` execution boundary in:

- `scripts/tsir_policy.py`

That module owns:

- path canonicalization;
- repo-containment checks;
- authority-within-scope checks;
- `<tool_call>` parsing for the exposed `rg_search` schema;
- final-call authority evaluation; and
- the `TSIR` rewrite function.

## Security-significant changes in this hardening pass

- Boolean parsing for `hidden` and `no_ignore` no longer uses raw Python truthiness.
  - This closes the bug where JSON strings such as `"false"` would previously coerce to `True`.
- Non-string `path` values in parsed JSON are now rejected rather than coerced.
  - Arrays or objects cannot silently become valid authority-bearing paths.
- Authority checks now resolve paths against the repository root before deciding containment.
  - This makes symlink escape testable at the policy layer instead of relying only on lexical prefix checks.
- `TSIR` rewrite is exposed as a reusable function rather than being embedded only inside one runner.

## Tests added in this pass

- `tests/test_canonicalization.py`
  - dot-segment normalization
  - parent escape rejection
  - absolute outside-path rejection
  - authorized subtree acceptance
  - unauthorized sibling rejection
  - symlink escape rejection
- `tests/test_parser_fuzz.py`
  - quoted boolean handling
  - malformed path rejection
  - first-tool-call behavior
  - fallback parser boolean extraction
  - extra-string flag smuggling rejection
- `tests/test_policy.py`
  - rewrite on unauthorized path and flag escalation
  - safe-path preservation
  - flag escalation detection
  - sibling pivot detection
  - symlink escape detection

## Remaining explicit assumptions

- The current exposed tool schema still contains only `pattern`, `path`, `hidden`, and `no_ignore`.
- Future scope-widening options must be classified as authority-bearing before they are exposed.
- The wrapper still studies one single-turn `rg_search` lane, not a multi-tool or multi-step loop.
