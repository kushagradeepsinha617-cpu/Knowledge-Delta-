# Actual local inference checkpoint

## Ten-question CPU smoke

The first completed hardware smoke used real local MiniLM ONNX embeddings,
NumPy retrieval and Ollama 0.40.14 with `qwen3:1.7b`. Its ten questions and
Widget documentation are constructed draft hardware probes. No semantic
correctness score or human answer review is claimed.

| Observation | Actual result |
| --- | --- |
| Planned distinct questions | 10 |
| Chat POST attempts | 10 |
| Completed model responses | 10 |
| Valid structured answers, pending semantic review | 10 |
| Run errors | 0 |
| Total command wall time | 122.453 seconds |
| Median per-question pipeline time | 11.009 seconds |
| Median pipeline time for nine pre-observed resident requests | 10.800 seconds |
| First response's reported model load time | 3.962 seconds |
| OS peak RAM | Not measured |

All requests used the same digest before/after generation:
`8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
Thinking was explicitly disabled, temperature was zero, context 4096, output
budget 128 tokens, `num_gpu=0`, and one attempt/request was allowed for this
hardware probe. Answer caching was disabled. Post-request observations reported
the matching model/context with zero VRAM for every question. This is an
Ollama residency observation, not an independent peak-RAM measurement.

The first request observed the model absent from Ollama residency; the next
nine observed it resident. Disk-cache coldness and operating-system load were
not controlled. The command wall time includes setup and observation overhead;
pipeline latency is distinct from isolated token-generation duration.

The model tag is `qwen3:1.7b`; this installed runtime reports `parameter_size`
as `2.0B` and quantization `Q4_K_M`. Preserve both recorded identifiers rather
than rewriting the model's reported metadata. No smaller model was substituted.

## Discovery and execution environment

The first agent-launched server could not read the ordinary V2 manifest and
returned an empty model list. Starting the same verified launcher in the user's
normal PowerShell allowed discovery of the exact expected digest. The exact
cause of the earlier native access failure remains unproven. No ACL or Windows
protection changes were made. The user-started server remains a foreground
process bound to 127.0.0.1 with cloud operation disabled and project-local state.

The initial smoke invocation passed a snapshot directory instead of its
`manifest.json` file. It returned a pre-inference input error and is preserved
separately; the corrected command produced the ten responses above. It is not
counted as a completed hardware experiment.

## Controlled development experiment

The original 40-record run and 36-record repeat study have now completed. Full
counts, retained output-limit failures and report archives are documented in
[recorded experiment results](EXPERIMENT_RESULTS.md). A separate 256-token
development experiment is in progress; its results are not yet established.

The existing Pydantic protocol was frozen before its first answer run. It plans
40 records: ten cases, two snapshots, and basic/version-filtered retrieval with
otherwise identical settings. Seven case definitions are human-reviewed; three
remain draft. All answer judgments remain unresolved until actually reviewed.

The source excerpts are genuine pinned Pydantic material, but this first
snapshot pair is constructed corpus assembly: adding v1 documentation to an
unchanged v2 corpus. It does not establish a naturally observed upstream edit
or production incremental-update failure. A separate predeclared three-case,
three-repetition experiment plans 36 variability records without answer caching.

Neither malformed-output detection nor citation existence proves semantic
correctness. Report errors, missing judgments and draft cases explicitly.
The 60-reviewed-case target and genuine-revision experiment remain unfinished.
