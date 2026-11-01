# Ten-question local hardware smoke harness

Status: limited offline checkpoint independently reviewed, ready to publish. No live model
latency, memory, residency, or answer-quality measurements have been made.
Milestone 2 remains incomplete and larger downloads remain deferred by the user.

## Purpose and inputs

The harness schedules ten short, distinct questions sequentially against one
constructed snapshot and one selected local model. It measures execution traces
after separately authorized setup rather than automatically selecting a model.

`examples/constructed/smoke/manifest.json` and its guide are constructed fixtures.
`examples/constructed/smoke_questions.json` contains ten **draft hardware-only**
questions. They are not reviewed correctness cases and do not count toward the
seven existing regression cases or the 20-development/60-total dataset targets.
Their snapshot binding and distinct IDs/question strings are validated.

## Future command - assets and environment required

After explicitly approved setup creates and verifies the project-local ML
environment, embedding assets, Ollama service and selected model, run from the
project root in PowerShell:

```powershell
.tools/envs/milestone2/Scripts/python.exe -B scripts/smoke_local_model.py examples/constructed/smoke/manifest.json examples/constructed/smoke_questions.json --embedding-directory .tools/models/minilm
```

Both the environment and `.tools/models/minilm` path are setup prerequisites,
not assets this command downloads. This future live command is unverified.
The default candidate is `qwen3:1.7b`; any explicit model choice must be recorded
as its own measurement. The harness does not download, switch models, unload
resident models, or change global installations.

## Request and trace contract

- Ten planned questions, one at a time; basic retrieval with `top_k=1` and
  `max_attempts=1`, so at most ten chat POST attempts.
- No answer cache. Missing evidence can produce a policy abstention without
  generation; that is not silently counted as a completed model response.
- Record planned questions, actual chat attempts, completed generation responses,
  structured answers pending review, run errors, and policy abstentions separately.
- `generation_attempted` records a request attempt; `generation_performed` requires
  a confirmed completed response naming the requested model. A transport failure
  does not prove inference happened or supply invented inference timing.
- Preserve exact retrieved evidence, responses/errors, elapsed timings, available
  model digest, token counts and runtime-reported generation/load durations.
- Observe Ollama process residency before and after each question. Observation
  errors remain visible; they do not become successful residency measurements.

The command prints JSON, not a performance score or recommendation. Exit code 0
requires `live_cpu_measurement_verified`; otherwise it returns 2. The distinct
`live_ten_request_measurement_verified` flag establishes ten completed live
responses with the same model/settings, not confirmed CPU residency. CPU verification
also requires all ten matching residency observations to report CPU and no run
errors. A successful response still requires semantic review.

## CPU, cold/warm, and memory interpretation

Generation requests ask for CPU operation (`num_gpu=0`). That requested setting
alone does not prove observed CPU-only execution. Ollama-reported CPU residency
checks matching digests across all resident aliases, rather than relying on tag
names. Zero reported VRAM qualifies only for the matching digest and context;
missing digests or ambiguous metadata remain unknown.

A confirmed matching resident model using GPU memory violates the requested CPU
control. The harness stops later generation requests, preserves blocked rows in
the ten-question plan, and records control violations instead of continuing a
misleading CPU benchmark.

Pre-request non-residency is a cold-load candidate; a matching resident model and
context is a warm candidate. Neither establishes operating-system disk-cache
coldness. No forced unload is performed to manufacture a cold measurement.

`os_peak_ram_bytes` remains null: peak process/system RAM is not measured. A
model download size or Ollama resident-size field is not peak runtime RAM. CPU
speed, GPU availability, and a final model choice require actual observations.

## Verification and remaining acceptance

New offline records are isolated in
[evidence/milestone2-smoke-contracts](evidence/milestone2-smoke-contracts/).
The recorded source run executed 195 tests with no failures/errors/skips, plus
real foundation CLI checks, on Windows/Python 3.15.2 with verified source-import
test dependencies. Brain approved this limited checkpoint with no blocking
findings and independently matched all 55 tested source hashes.

- Run ID: `f26de47c60b1430783205d64ef8c0e9c`.
- Source ID: `78c2e05518dfdfcefd1436bb823dfee45c03e7eaf07e8b2a5dcf5ab3720efd80`.

This count is not a live inference result. The published 183-test pipeline
checkpoint and its evidence remain unchanged historical observations.

Tests use explicit tokenizer/index/transport doubles and injected observations.
They can verify counting, residency labels and failure handling, not real model
speed, memory, or CPU capability. No correctness scores or human reviews are
fabricated from these hardware-only questions.

Next: publish the reviewed checkpoint and reconcile remote source hashes against
the recorded evidence. Expanded setup and the actual ten-question
hardware run remain deferred until separately authorized resources are available.

## Integration references

- [Ollama running-model observations](https://docs.ollama.com/api/ps)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama FAQ](https://docs.ollama.com/faq)

References describe intended API integration; capabilities still require checking
against the actual installed runtime before live measurement claims.
