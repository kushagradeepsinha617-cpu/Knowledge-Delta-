# Milestone 4: credible local evaluation

Status: live evaluation in progress. Real MiniLM ONNX embeddings and the Qwen
ten-question CPU hardware smoke now work locally: ten completed structured
answers, zero run errors. Seven explicit human case reviews are recorded in
examples/pydantic/REVIEW_LOG.md; three cases remain draft. Human answer judgments,
controlled correctness results and the final reviewed dataset remain pending.
See [actual local inference observations](LOCAL_INFERENCE_RESULTS.md).

## Scope and resource gates

First build ten reviewable Pydantic development cases, then measure the existing
reference assistant with its basic and version-filtered retrieval configurations.
Use the existing standard-library interface, review journal and report workflow.
Keep Smart App Control on. The observed pandas policy failure does not establish
whether Torch or Ollama will run; verify them separately without bypassing policy.

The user subsequently approved 12,000,000,000 bytes total project storage and
5,000,000,000 bytes additional artifact payload including retries, at most
1,000,000,000 bytes for CPU embedding dependencies. The previous UI-only limits
are superseded for this explicit model setup. Verify exact compatible assets,
hashes and expanded/temporary space before downloads. See the resource proposal. Retain zero spending, project-local state,
localhost binding, explicit setup and no automatic downloads during startup/tests.
Assume CPU operation; 16 GB RAM is user-reported and inference speed is unknown.

## Source pins and attribution

The following official sources were inspected during protocol preparation:

| Release | Resolved Git commit | Relevant source |
| --- | --- | --- |
| v1.10.21 | `0cbba0f9774c470e8d8a2a62abb921b8cea4027d` | [Models guide](https://github.com/pydantic/pydantic/blob/0cbba0f9774c470e8d8a2a62abb921b8cea4027d/docs/usage/models.md) |
| v2.10.6 | `df05e69a8a3fb37628a0e3a33518ca0425334bc9` | [Migration guide](https://github.com/pydantic/pydantic/blob/df05e69a8a3fb37628a0e3a33518ca0425334bc9/docs/migration.md) |

The v1 tag is annotated; its tag-object SHA is not the resolved commit above.
The inspected models/migration Git blob IDs are respectively
`99fa4ea1390ebbc29c6850063f4675f3fd5f24cf` and
`1f4404e822730375e3edb1bbcab4cde0a2abce0c`.
Both releases include the MIT license, covering associated documentation.
Bundle the exact [v1 notice](https://github.com/pydantic/pydantic/blob/0cbba0f9774c470e8d8a2a62abb921b8cea4027d/LICENSE)
and [v2 notice](https://github.com/pydantic/pydantic/blob/df05e69a8a3fb37628a0e3a33518ca0425334bc9/LICENSE)
with distributed excerpts; their copyright notices differ.

Record source commit/path, original content hash, extraction boundaries and
transformation for each excerpt. Preserve original wording and attribute omissions.
Software applicability follows the passage's meaning, not merely the repository
tag: the v2 migration guide also discusses historical v1 behavior. Keep that
comparison visible and avoid attributing every statement in a mixed passage to v2.

## First corpus pair: deliberately assembled, genuine source material

Recommended first batch:

- Before: selected pinned v2 documentation.
- After: exactly that v2 documentation plus pinned v1 distractor material.
- Keep the declared default and each requested version unchanged. Prefer the
  explicit label `2.10.6` rather than an unqualified claim about every v2 release.
- Preserve v2 document IDs, content and applicability across snapshots. Record
  v1 additions and build separate indexes.

This tests resistance to another version's documentation. It is **constructed
corpus assembly using genuine source excerpts**, not a naturally observed
upstream documentation edit or production ingestion regression. Use case
`provenance: constructed`, category `other_version_added`, and draft
`should_remain` relations. Record genuine source attribution separately.
Different applicable versions are not conflicting authorities for one version.

For a later genuine-revision experiment, retain an actual upstream before/after
commit pair, its verified document diff and applicability, and the separate
snapshot expectations. Do not relabel the assembly experiment as genuine source
change. Deliberately injected faulty answers remain evaluator fixtures, outside
live assistant results.

## Ten initial development families

All entries below are proposals requiring human review against the exact bundled
passages. Their v2 facts are supported by the pinned migration guide above.

| Family | Proposed v2 question focus | Essential review guard |
| --- | --- | --- |
| `pydantic-serialization` | Preferred model-to-dictionary method: `model_dump()` | `dict()` is deprecated compatibility behavior, not automatically removed. |
| `pydantic-orm` | Validate an attribute-based object using `model_validate` | Include `from_attributes=True`; distinguish deprecated `from_orm`. |
| `pydantic-optional` | Is `Optional[str]` without an assigned default required? | Required and nullable are separate; explicit `= None` changes requiredness. |
| `pydantic-union` | Default `Union[int, str]` result for input `'1'` | Preserve the string; distinguish explicit left-to-right mode. |
| `pydantic-number-string` | Default coercion of numeric input to a string field | Default coercion is disabled; configuration can enable it. |
| `pydantic-dict-pairs` | Validate an iterable of key/value pairs as a `dict` field | Do not generalize this to rejecting ordinary dictionaries. |
| `pydantic-validator-error` | Does a validator's `TypeError` become `ValidationError`? | In v2 it is not wrapped; avoid confusing this with invalid field input. |
| `pydantic-regex` | Default regex support for lookarounds/backreferences | Explain the default engine restriction and Python-engine alternative. |
| `pydantic-equality` | Is a model equal to a dictionary of its data? | v2 does not equate them; do not claim all model instances are unequal. |
| `pydantic-settings` | Where is `BaseSettings` provided for v2? | Identify `pydantic-settings`/`pydantic_settings`; do not claim settings vanished. |

Do not inflate this batch with paraphrases. Keep future variants of any family
in the same development split. The Widget demonstration datasets remain separate;
their cases do not satisfy the Pydantic benchmark's reviewed-case target.

## Completion evidence

Follow [EVALUATION.md](EVALUATION.md). First obtain actual human case reviews,
then freeze the dataset and configurations before scored runs. Draft diagnostic
runs may be retained but cannot supply reviewed correctness measurements.
Changing case review metadata changes the current dataset hash; retain earlier
revisions/results rather than silently rebinding an old run.

Deliver pinned attributed sources, reviewed-case records where they actually
exist, raw serial live traces or explicit runtime blockers, the controlled
comparison and fixed-subset variability observations, and JSON/HTML reports with
denominators and limitations. The later target remains 20 development plus 40
held-out reviewed cases, with whole families kept together. Report the actual
reviewed count if that target is not reached. A zero-improvement result is valid;
no commercial validation, novelty or production reliability follows from it.
