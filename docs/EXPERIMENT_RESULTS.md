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
The new protocol was frozen before inference. Completion and prompt/evidence
identity must be checked against the baseline after it finishes; no improvement
is claimed in advance. Four new offline CLI tests passed in the 498-test suite.

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
