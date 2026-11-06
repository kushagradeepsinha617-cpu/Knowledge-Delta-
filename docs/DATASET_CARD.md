# Pydantic evaluation dataset card

## Purpose and current status

The study tests a local documentation assistant under controlled corpus changes,
using English Pydantic documentation and reviewed or explicitly qualified case
definitions. It is a small curated engineering study, not a representative
industry benchmark or validation of commercial demand.

There are **60 prepared, blanket-owner-approved definitions**: 20 development
cases across 15 semantic families and 40 held-out cases across 22 families, for
37 families overall. Existing observed families remain in development. The study
keeps its seven snapshot-pair bundles separate instead of rebinding old approvals
or old runs to new corpora.

The frozen 60-case execution has started. Held-out outcomes, final completion
counts and correctness are **pending** in this card; preparing or starting a run
does not establish that it finished. The main plan is 240 answer records, with a
separate 36-record development variability run. Policy abstentions are records
without model generation, so these totals are not model-call counts.

## Inventory and split allocation

| Bundle | Split | Cases | Corpus change |
| --- | --- | ---: | --- |
| `examples/pydantic` | development | 10 | Constructed addition of pinned v1 material to selected v2 excerpts |
| `examples/pydantic-revision` | development | 1 | Genuine upstream warning addition; release applicability unknown |
| `examples/pydantic-evaluation/development-extension` | development | 9 | Constructed addition of other-version material |
| `examples/pydantic-evaluation/heldout-other-version-added` | held_out | 11 | Constructed addition of other-version material |
| `examples/pydantic-evaluation/heldout-evidence-removed` | held_out | 12 | Constructed removal of the entire selected supporting corpus |
| `examples/pydantic-evaluation/heldout-wording-only` | held_out | 10 | Constructed whitespace-only changes |
| `examples/pydantic-evaluation/heldout-unrelated-change` | held_out | 7 | Constructed change to an unrelated control note |

The held-out allocation is **11/12/10/7 cases** across those four conditions.
Family assignment determines the condition; it is not randomized or balanced by
case count. Related cases stay together. Forty cases are not forty independent
families, and multiple answers from a case/family share underlying evidence.
Report results by split, condition and provenance rather than treating every
record as an independent observation.

The new held-out contracts cover field defaults and aliases, strict input
representations, partial JSON parsing, JSON-schema customization, TypeAdapter
lifecycle, validator execution/context and call validation. These are distinct
contracts, not repetitive paraphrases used to reach a target. The first ten
observed Pydantic migration families and the generic-bound clarification remain
development examples, along with the nine reserved migration contracts.

## Sources, selection and applicability

Sources are pinned official Pydantic documentation, with local source inventories,
exact Git blob/content hashes, extraction boundaries and MIT attribution.
The existing Pydantic source inventory and licenses remain in `examples/pydantic`;
the new concept documents are recorded in `examples/pydantic-evaluation/sources.json`.
Full source files and case recipes are not automatically the retrieval corpus:
each manifest selects the actual passages supplied to its snapshot index.

Most cases request **2.10.6** in both snapshots. An older-version addition does
not change that question. The main source pins are v2.10.6 commit
`df05e69a8a3fb37628a0e3a33518ca0425334bc9` and v1.10.21 commit
`0cbba0f9774c470e8d8a2a62abb921b8cea4027d`.

The genuine warning pair uses `docs/concepts/models.md` at parent
`55dd8daeb6091b9317b92836765f3f1396b3e9ba` and child
`6f7691b5c1e1838aedf88414a41cd6a9a0caf1d6`. Its question targets the supplied
documentation without inventing a release version. Nominal mainline version
metadata does not establish released-software applicability. The warning
clarifies existing behavior; the dataset does not claim software behavior changed.

Constructed snapshot assembly remains `constructed` even when the excerpts are
genuine and the model calls are live. It is separate from the genuine upstream
revision, from injected faulty-output tests and from scripted UI replay.

## Approval, review and answer labels

The owner explicitly approved all definitions and expected relations as a batch.
The ledger in `examples/pydantic-evaluation/user-approval.json` binds all 60 case,
dataset, relation and snapshot identities. Source-checking was AI-assisted and
included exact quote/extraction verification. Neither the ledger nor the source
checks establish independent human gold labels.

Preserved schema counts are **11 item-specifically human-reviewed definitions and
49 drafts**. One expected relation has an item-specific human review; the other
59 do not. The blanket owner approval permits execution under the amended gate;
it does not silently relabel those 49 cases as human-reviewed. The original target
of 60 item-specifically human-reviewed definitions remains unachieved.

There are four actual human answer judgments from one earlier development family,
selected after seeing outputs and assessed with agent assistance, unblinded.
They are bound to that earlier run and cannot grade the new 240 records. New-run
semantic judgments remain pending unless separately recorded. Owner approval of
a case is not approval of a model output; valid JSON and existing citations are
not semantic passes. Draft cohorts remain excluded from metrics requiring human
ground truth. Independent-reference failure-flag precision/recall is unavailable
without qualifying separate annotations. See
[REVIEW_PROVENANCE.md](REVIEW_PROVENANCE.md).

## Interpretation limits

- Held out means case families withheld from project tuning. It does not mean
  unseen source documents, unknown model pretraining, independent case authorship
  or blind human review. Freeze settings before observing held-out outputs.
- The wording condition changes whitespace only; it does not test arbitrary
  semantic paraphrasing.
- Evidence-removal after snapshots are empty. Their abstentions exercise the
  no-evidence policy, not difficult generation with misleading residual passages.
  Removal does not make an underlying Pydantic fact false.
- Some families share sections and related contracts. Small, condition-specific
  counts do not establish broad generalization or causal latency improvements.
- The study uses a local model, selected context settings and one answering
  policy. Keep model weakness, retrieval issues and document-change effects
  distinguishable; do not assign a root cause from correlation alone.
- Report planned/recorded/missing rows, errors, review coverage and eligibility
  exclusions. Keep unresolved judgments unresolved, with explicit denominators.

See [EVALUATION.md](EVALUATION.md), [EXPERIMENT_RESULTS.md](EXPERIMENT_RESULTS.md)
and the frozen execution artifacts for methodology and measured results. This
card must be reconciled with actual completion evidence before final publication
of study findings.

## Widget demonstration datasets

`examples/constructed` contains the original seven draft Widget foundation cases;
`examples/mvp` contains twenty draft constructed Widget development cases. These
fictional fixtures support offline tests and UI demonstrations. They do not count
toward the 60-case Pydantic study and are not live benchmark results.

The original foundation card below is historical; its seven-case counts and
implementation-status statements do not describe the later application.

## Historical foundation card (preserved)

# Constructed dataset card

Domain: imaginary Widget software. All documentation and cases are constructed
for this repository; none are authoritative software advice.
No third-party documentation excerpts are bundled.

Two snapshots, seven draft development cases, zero human-reviewed cases,
zero held-out cases. Each requested version remains "1" across snapshots.
Cases cover all seven requested categories. Their small size is a foundation
example, not a benchmark or the eventual 20/60-case dataset.

The timeout changes within version 1 are deliberately constructed evidence
changes across source revisions, not a verified real release change.
One source has missing version metadata before a metadata correction.
The version-2 addition coexists with unchanged version-1 status evidence.
Two version-1 sources deliberately contradict each other about worker limits.
Removed export evidence makes the evidence-only expectation abstention, not a
claim that export files stopped existing.

Related cases remain in the development split. The two version-1 status-command
cases share family widget-status-v1, so a later split cannot separate them.
No prompts/thresholds or answering
models exist yet. No live outputs, empirical error rates or market conclusions
can be inferred from these cases.

Next: human review before correctness measurement; later add revision-pinned,
license-verified genuine Pydantic material and reserve independent held-out
families. A review workflow must record actual human review; agent approval
does not count as human dataset review.
