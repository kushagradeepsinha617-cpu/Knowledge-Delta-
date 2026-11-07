# Recorded development experiment results

These are real local Qwen runs, using the genuine pinned Pydantic excerpts in
the explicitly constructed v1-addition experiment. They are development data,
not held-out results or an estimate of industry-wide failure rates. The recorded
main runs froze seven reviewed case definitions and three drafts. All ten current
definitions have since been approved; the frozen runs are not rewritten. Four
actual answer judgments are recorded for one selected family, as detailed below.
No independent evaluator-reference labels are available.

## Original 128-token configuration

| Run | Planned/recorded records | Valid structured responses | Final run errors | Run wall time |
| --- | --- | --- | --- | --- |
| Ten-case comparison | 40/40 | 22 | 18 | 1117.842 seconds |
| Fixed three-case repeat study | 36/36 | 6 | 30 | 753.579 seconds |

The ten-case run made 60 chat attempts. All 38 rejected attempts reported
`done_reason: length` with `eval_count: 128`; 18 records exhausted their two
attempts. The repeat study's 60 rejected attempts also reached that limit.
The errors are retained, not excluded from the planned-record denominators.
These counts describe response completion, not answer correctness.

The report identified one incompatible citation: `pydantic-equality`, basic
retrieval, after snapshot. Its question requests 2.10.6, but the cited supplied
chunk is scoped to 1.10.21. This establishes citation-version incompatibility.
It does not establish semantic incorrectness, a previously-correct regression,
or a sole causal explanation. Brain independently checked this trace.

The exported main report therefore has 18 run errors, one mechanical failure
flag and 21 unresolved results. It contains zero human pass judgments. Semantic
accuracy and evaluator precision/recall remain unavailable. A conservative
confirmed-correct count of zero reflects absent review, not a measured 0%
semantic accuracy.

The repeat study used the predeclared serialization/optional/union subset and
three repetitions for each snapshot/configuration, without answer caching.
Ten of its twelve groups produced three run errors each. The two union/after
groups each produced three valid responses with identical answer objects.
This narrow observation does not establish general model determinism, semantic
equivalence of arbitrary outputs, or correctness. Most repeat records were
unusable for semantic variability analysis because of the output limit.

## Separate 256-token development experiment

The CLI now accepts explicit `--max-output-tokens 256`, preserving 128 as the
default. This was chosen after observing development failures, and is recorded
as a new experiment rather than replacing the original results. The model,
questions, prompt messages, context4096, retrieval/chunking settings and retry
limit remain fixed. Both retrieval configurations receive the same output cap.
The new protocol was frozen before inference. The run completed all 40 planned
records with 40 structured responses, zero run errors and 40 chat attempts;
all responses reported a normal stop. Total run time was 841.381 seconds.
The comparison command verified all 40 matched rows: same exact retrieved
passages/scores, prompt messages/schema, indexes, embeddings and model/runtime
identity; the generation requests differ only in the output cap. This is a
recorded completion improvement from 22/40 to 40/40, not better correctness.
Runtime order/system-load effects prevent a causal speedup claim.

The new report has two citation-version failure flags and 38 unresolved results,
with zero human answer reviews. More complete responses can expose additional
issues; valid JSON is not a semantic pass. Four new offline CLI tests passed in
the 498-test checkpoint; the subsequent comparison utility has 15 synthetic
control tests, including deliberately changed evidence, prompts and model IDs.

Reproduce the read-only control check without inference:

```powershell
& .\.venv\Scripts\python.exe -B scripts/compare_output_budget.py runs/pydantic-live-main.json runs/pydantic-live-main-256.json --output runs/output-cap-check-new.json
```

The original runs remain unchanged. The separate output-cap study used only
development data. It does not tune a held-out set or measure semantic accuracy.

Within this 256-token run, basic retrieval had **2 incompatible-citation flags
out of 20 records**; version filtering had **0 out of 20**, with zero run errors
in each group. Each includes 14 records from reviewed cases and 6 from drafts;
neither has human answer judgments. This measures metadata compatibility of
citations only, not wrong-version answer semantics or evidence support.

## Separate genuine revision diagnostic

The [pinned generic-model warning example](../examples/pydantic-revision/README.md)
has four actual local records, zero run errors, and four unresolved results.
The model answered Yes before the real warning addition and No afterward in
both configurations. These are observed texts, not reviewed correctness labels
or proof that software behavior changed. Release applicability remains unknown;
no target version is invented, and filtering has no effective version target
in this diagnostic. Its case and expected relation remain drafts.

The complete diagnostic and HTML/JSON report are archived under
`docs/evidence/milestone4-genuine-revision-diagnostic/genuine-revision-diagnostic.zip`.

## Inspect the complete reports

Full raw requests/responses, exact evidence and self-contained HTML/JSON reports
are stored in lossless ZIP archives to avoid publishing several duplicated
megabytes of expanded text. Archive manifests record the SHA256 and size of
each original file; the archives were extracted in memory and compared byte
for byte before publication. Models, environments and keys are excluded.

From the local repository, extract the main report into a new runs folder:

```powershell
Expand-Archive -LiteralPath "$env:TEMP\Knowledge-Delta-\docs\evidence\milestone4-pydantic-live-main\live-main-report.zip" -DestinationPath "$env:TEMP\Knowledge-Delta-\runs\published-live-main"
```

Open `runs/published-live-main/report.html`. Its export did not regenerate any
answers. The repeated-run archive is under
`docs/evidence/milestone4-pydantic-variability/live-variability-report.zip`.
Its included subset dataset and draft relations are bound to those runs; no
new human case/relation/answer review was fabricated.

The real CPU smoke, runtime/backend versions and measurement limitations are
documented in [local inference results](LOCAL_INFERENCE_RESULTS.md).

The separate 256-token archive is
`docs/evidence/milestone4-output-cap-256/live-output-cap-256-report.zip`.
It includes the full raw run plus self-contained HTML/JSON reports. Extract it
to a new project-local runs folder using the same procedure as the main archive.

## Actual human review of the selected main-case family

The user reviewed all four dict-pairs answers and approved the unchanged-answer
relation. Two answers passed and two failed. This was an assisted, unblinded,
post-hoc diagnostic selection of one family, not a representative sample. The
other 36 answers lack human semantic judgments; two of those have mechanical
citation-version flags. Do not describe 2/4 as overall benchmark accuracy.

The basic comparison is previously_correct_now_incorrect; the filtered comparison
recovered from a prior failure. These are human-confirmed outcomes for those
recorded answers, not a general claim that version filtering improves correctness.
An exploratory check found identical recorded before-snapshot generation requests
that produced No and Yes. Model/runtime state was not fully controlled. The
document addition therefore is not established as the sole cause of the observed
regression. Original fixed-subset variability results remain reported separately.

Four exact review bindings and the approved relation are saved in
`docs/evidence/milestone4-human-answer-review/human-review-records.json`; the
complete reviewed export is in `human-reviewed-subset-report.zip` there. The
counts and metrics were independently reproduced with evaluate_run and
summarize_metrics from public raw/label files, without the private SQLite journal
or inference. Independent evaluator-reference labels are still absent, so
failure-flag precision/recall remain unavailable.

The genuine case definition and should_change relation were subsequently approved.
Its old draft diagnostic is preserved, and a fresh reviewed-case four-record run
completed without errors. Human actual-answer review of those new traces is pending;
the later 60-case study has separate provisional AI assessments.

## Frozen 60-case study: completed execution, provisional semantic analysis

The frozen protocol binds 324 source/configuration/fixture files, 20 development
and 40 held-out case definitions, two retrieval configurations and two snapshots.
The user approved all definitions as a batch; only 11 case definitions and one
expected relation have item-specific human review. These review types are not
interchangeable. The study used the same local Qwen model digest and MiniLM ONNX
backend throughout. The only intended configuration difference was explicit
software-version filtering.

The [verified report](evidence/milestone5-analysis/final-study-report.html) gives
the full denominators and per-bundle accounting. Exact answer/evidence traces
are preserved in the raw bundle archives. The main run retained **240/240**
planned records: **236 structured**, including **24 deterministic policy
abstentions** after evidence removal, and **4 run errors**. It logged **216 chat
attempts** and **212 completed model responses**. Basic retrieval had 120
structured records and zero errors; version-filtered retrieval had 116
structured records and four errors. No general correctness improvement follows
from those counts.

All 240 records have hash-bound **AI-assisted provisional proposals**: 125 pass
(101 generated answers and 24 policy abstentions), 95 fail, 16 need human review,
and four run errors. In pass/fail/unresolved/error order, development proposals
were 50/22/7/1 and held-out proposals were 75/73/9/3. Basic-retrieval proposals
were 64/47/9/0, and version-filtered proposals were 61/48/7/4. These are agent observations, not human-validated
accuracy or independent evaluator labels. The new study has **zero human answer
judgments**. The four older human judgments remain attached to their earlier
run and are not copied here. Testing-tool precision/recall therefore remain
unavailable. Most observed failure patterns should be treated as model or
evidence problems in these tested cases; the corpus change is not established
as their sole cause.

The fixed three-case variability subset retained **36/36** repeated records with
zero errors and answer caching disabled. Five of twelve
case/configuration/snapshot cells produced more than one distinct structured
answer object over three repetitions. That is an exact-object observation;
semantic difference was not adjudicated. Formatting controls changed whitespace
only. Empty-after removal rows exercised the configured evidence-only policy,
not the model's ability to infer a fact from deleted evidence.

The [artifact manifest](evidence/milestone5-study/final-artifact-manifest.json)
binds raw archives, the frozen source and review packets. The
[offline reproduction receipt](evidence/milestone5-study/offline-reproduction-receipt.json)
records a fresh project-local extraction that regenerated the exact JSON/HTML
report hashes without model inference. The current source has a later
validation-only model-digest fix, separately verified by 589 offline tests;
the recorded study used the archived source.
