# Formal TSIR Spec

created_at: 2026-04-18T22:20:00+08:00
status: "stage-1 formalization"

## Scope

This note formalizes the current `TSIR` object for the exposed `rg_search` tool schema used in the repository.

It does not claim:

- arbitrary tool generality;
- arbitrary prompt-injection resistance; or
- correctness when trusted metadata itself is wrong.

## Trusted metadata

For one task instance, define trusted metadata:

`T = (repo_root, authorized_roots, trusted_default_path, trusted_literal, allowed_flags, path_policy, flag_policy)`

Where:

- `repo_root` is the repository root on disk;
- `authorized_roots` is the set of trusted files or subtrees this task may search;
- `trusted_default_path` is the fallback path used when a proposal is out of scope;
- `trusted_literal` is the trusted search literal;
- `allowed_flags` is the deny-by-default authority flag map;
- `path_policy` defines normalization and repo-containment checks; and
- `flag_policy` defines which authority-bearing flags may be enabled.

## Search call object

For the current exposed tool schema:

`C = (pattern, path, hidden, no_ignore)`

Authority-bearing fields:

- `path`
- `hidden`
- `no_ignore`

Evidence-bearing fields:

- `pattern`

Future path-expanding options such as `follow_symlinks`, `glob`, `max_depth`, `no_ignore_parent`, `no_ignore_vcs`, `type_add`, and `unrestricted` belong to the same authority-bearing class if they are ever exposed.

## Safety predicate

Let `canon_T(path)` be the repository-relative path obtained after the current normalization policy and repo-containment check under `repo_root`.

Define:

`Safe_T(C)` iff

- `canon_T(C.path)` is contained inside one member of `authorized_roots`; and
- every enabled authority-bearing flag in `C` is permitted by `allowed_flags`.

## TSIR enforcement

Given a model proposal `Ĉ`, the wrapper computes:

`TSIR_T(Ĉ) = Ĉ` if `Safe_T(Ĉ)` holds after normalization.

Otherwise:

`TSIR_T(Ĉ) = (trusted_literal, trusted_default_path, allowed_flags.hidden, allowed_flags.no_ignore)`

In the current implementation, literal anchoring is an engineering choice layered on top of the path/flag authority rule. The paper's primary unsafe labels are defined by path and flag violations, not by literal drift alone.

## Theorem 1: Path-and-flag safety

For any trusted metadata `T` and any model proposal `Ĉ`, the executed call `TSIR_T(Ĉ)` is safe with respect to `T`.

### Proof sketch

There are two cases.

1. If `Ĉ` is already safe under `T`, the wrapper executes its normalized form, which remains inside `authorized_roots` and does not enable unauthorized flags.
2. Otherwise, the wrapper rewrites the call to `trusted_default_path` and resets authority-bearing flags to the trusted allowlist encoded in `T`.

In either case, the executed call satisfies `Safe_T`.

## Theorem 2: Authority noninterference

Holding `T` fixed, varying untrusted retrieved text may change the model proposal but cannot expand the authority of the executed call beyond the safe call set induced by `T`.

### Proof sketch

Untrusted text influences only the proposal seen by the wrapper. The wrapper either accepts a proposal already inside `Safe_T` or rewrites it to the trusted fallback call encoded by `T`. Therefore untrusted text cannot increase the final call's path scope or flag authority beyond what `T` allows.

## Assumptions

The above statements hold under the current repository execution lane:

- all repository search executions pass through the wrapper;
- `rg_search` is read-only;
- path normalization and repo-containment checks are correctly implemented;
- symlink escape is evaluated on resolved paths;
- parser fallback does not grant authority on malformed path or flag fields; and
- trusted metadata itself is correct.
