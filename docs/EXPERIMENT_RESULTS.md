# Recorded development experiment results

These are real local Qwen runs, using the genuine pinned Pydantic excerpts in
the explicitly constructed v1-addition experiment. They are development data,
not held-out results or an estimate of industry-wide failure rates. Seven of
the ten case definitions are human-reviewed; three are drafts. There are no
human answer judgments or independent evaluator-reference labels yet.

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
