# KnowledgeDelta: testing documentation changes with local evidence

## Problem

A documentation assistant can produce a different answer after a corpus update.
That alone does not tell a developer whether the answer improved, regressed or
correctly followed a new documented behavior. An older document can also remain
the right source for a question about an older software release.

KnowledgeDelta implements a small local workflow for comparing explicit document
snapshots against snapshot-specific expectations. The main deliverable is the
test and evidence report, with a deliberately small reference RAG assistant.
Demand for a standalone commercial product remains unvalidated.

## Implementation

The Python pipeline gives documents stable IDs, hashes contents and relevant
metadata, and builds separate snapshot indexes. It chunks passages within the
embedding tokenizer limit, embeds them with pinned MiniLM ONNX assets and ranks
them with NumPy. Qwen runs through local Ollama on the CPU, one request at a time.
The comparison changes only explicit version filtering; model, prompt and other
retrieval settings stay fixed within that experiment.

Answers retain citations, exact model context, request settings, model digest,
timings and every malformed attempt. The evaluator checks what can be checked
mechanically and leaves unsupported semantic conclusions for review. A local
standard-library browser interface supports case inspection, review history and
self-contained HTML/JSON exports.

The original Streamlit route encountered Windows native-library policy blocks.
The project moved to the standard-library UI and an explicitly recorded ONNX
embedding backend without disabling Windows protection.

## Demonstrated observations

- The recorded ten-question CPU smoke produced ten structured responses and no
  run errors in 122.453 seconds. These were hardware probes, not a reviewed
  semantic benchmark.
- A 40-record Pydantic development run with a 128-token output cap retained 18
  errors. A separately recorded 256-token configuration completed 40 structured
  responses with no run errors; exact recorded controls differed only in the
  intended output cap. JSON completion is not answer correctness.
- Four actual human answer judgments for one assisted, post-hoc dict-pairs family
  showed a basic-retrieval regression and filtered recovery. This is a concrete
  diagnostic example, not a representative estimate or a causal proof.
- A fresh offline wheel build and isolated pip installation were exercised using
  already downloaded build tools. This does not establish online ML dependency
  resolution or compatibility on every Python/operating system.
- The frozen 60-case execution retained all 240 planned main records: 236
  structured results, including 24 deterministic abstentions after evidence
  removal, and four run errors. It recorded 216 chat attempts and 212 completed
  model responses. The fixed variability subset retained all 36 repeats with
  zero errors; five of twelve case/configuration/snapshot cells had more than
  one distinct answer object. Those differences have not been semantically
  adjudicated.
- A hash-bound AI-assisted review proposes 125 passes (24 from the policy
  abstention path and 101 generated answers), 95 failures, 16 unresolved cases
  and four run errors. These are provisional diagnostic labels, **not** human
  benchmark accuracy. In this exploratory run, wrong answers often appeared
  in both snapshots, so a changed corpus alone is not established as their
  cause. Basic retrieval had no run errors; version-filtered retrieval had four.

See [the full study report](evidence/milestone5-analysis/final-study-report.html),
[the source and raw-artifact manifest](evidence/milestone5-study/final-artifact-manifest.json),
[offline reproduction receipt](evidence/milestone5-study/offline-reproduction-receipt.json),
EXPERIMENT_RESULTS.md and HUMAN_REVIEW.md for denominators and limitations.

## Expanded evaluation and review provenance

The expanded study prepares 20 development and 40 held-out cases in one Pydantic
domain. The held-out cases cover 22 semantic families and are withheld from
project tuning; they are not claimed unseen during model pretraining. Cases and
answers are AI-assisted, not independently authored ground truth.

The project owner explicitly approved all definitions as a batch. The execution
ledger binds that authorization to exact cases, expected relations, datasets and
snapshot IDs. It preserves 11 existing item-level human case reviews instead of
inventing 49 more. Actual-answer human review remains a separate record.

The 240 main-record and 36-repeat study completed under a frozen 324-file source
manifest. The final JSON/HTML report reproduced offline from that source archive
and the archived raw runs. A later validation-only fix requires both model-digest
observations for answered live rows; it was tested separately and did not
change the historical answers. The new study has **zero human answer judgments**;
the four earlier human judgments remain bound to their original run. No
human-validated held-out accuracy or independent evaluator precision/recall is
asserted.

## Lessons

The hardest engineering problem was maintaining the meaning of an experiment:
software version, source snapshot, expected behavior, retrieved evidence and
review provenance all have to agree. A valid JSON answer or a green test suite
cannot establish semantic accuracy by itself.

The work demonstrates local model integration, retrieval, test-case design,
trace validation, fault-oriented tests, reproducible artifacts and explicit
experimental controls. A separate rebuilt index does not test a production
connector's incremental deletion behavior.

## Limits and future work

This is a small exploratory engineering study. It does not establish commercial
demand, general benchmark accuracy, independent evaluator precision/recall or
production readiness. OS peak memory, broad platform compatibility and robust
causal attribution remain outside the demonstrated evidence. Broader human
semantic review and an external assistant adapter are possible follow-ups.
