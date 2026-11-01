# Milestone 2 progress - offline contracts, not live inference

Status: limited offline checkpoint reviewed and ready for publication. Milestone 2
is not complete. Implemented boundaries and unverified live integrations are distinct.

## Implemented locally

- Exact-text chunks retain source offsets, snapshot/document identities, software
  versions, content/metadata hashes, and tokenizer identity/mode. The tokenizer
  contract counts input including special tokens and forbids silent truncation.
- Questions project only answering inputs; expectations and grading rubrics stay
  outside model inputs and the retrieval corpus.
- Basic semantic and explicit version-filtered retrieval share the pipeline.
  Missing or ambiguous applicability remains visible rather than inferred.
- Local-asset embedding/index adapters, prompt/response validation, bounded
  localhost Ollama transport, and single-question orchestration are implemented.
  Tests use explicit doubles; ordinary startup/tests must not download assets.
- `knowledge_delta/local_environment.py` configures this process for offline
  Hugging Face/Torch operation with caches and temporary paths inside the project.
  This is not an installer or proof that every dependency honors these settings.
- Traces distinguish retrieved evidence, configuration, malformed responses,
  attempts, timing, errors, policy abstention, and generation where available.
  Citation existence and structural validity do not establish semantic correctness.
- Recorded identities include chunker settings and available model digest;
  remote/cloud model aliases are rejected instead of silently substituted.

## Review corrections

Repeated tokenizer offsets can describe the same source span. Chunk progression
must preserve valid spans and terminate or fail explicitly rather than silently
lose evidence. Regression coverage exercises this boundary.

Chunk metadata can be forged independently of an apparently valid identifier.
Retrieval checks content and applicability/source metadata against the selected
immutable snapshot rather than trusting caller-supplied chunks. Regression checks
cover metadata substitution and snapshot mismatches.

These are traceability fixes, not evidence of model comprehension or measured
retrieval improvement. Test-double answers remain labeled. Policy abstention
without generation must not be presented as a model-generated answer.

## Checks and their limits

Executed offline source-run records are in
[evidence/milestone2-contracts](evidence/milestone2-contracts/).
The final recorded Windows/Python 3.15.2 run executed **183 tests**, with zero
failures, errors, or skips, using verified source-import pytest dependencies.
Actual foundation CLI checks also passed: exact fixture diff, seven draft cases
and zero human reviews, default readiness without downloads/service calls, and
invalid-input JSON error with exit code 2. Brain approved the limited offline
checkpoint, independently checked all 49 tested source hashes, and verified the
final transport-error and failed-index-label regression fixes.

- Run ID: `2e4af53709f549b38fa16cae66932cc3`.
- Tested source ID: `293ce31f394b3f5205cd31b8ef190fde6ee58b0c6eb32dea0784d0463b2c7aa0`.

The stored `checks.json`, `pytest.xml`, and `source-manifest.json` bind these
observations to the tested source. They do not establish compatibility beyond
the recorded configuration or successful live integration.

Tokenizer, embedding/index, and transport doubles exercise engineering contracts;
their outputs are not assistant benchmark results. Seven constructed cases remain
drafts. No human dataset review is implied.

Still unverified: real NumPy/sentence-transformers imports and embeddings; pinned
asset tokenizer behavior; Ollama/model installation and actual generation; API
compatibility; the ten-question CPU speed/memory smoke test; standard dependency
installation/build; and other Python/platform configurations.

## Explicit local answering command - setup required, unverified live

After separately approved ML setup has explicitly created and verified the
project-local `.tools/envs/milestone2` environment, run from the project root in
PowerShell. That environment/setup is currently unverified; these are future
integration commands, not a claim that the executable or assets already exist.

```powershell
.tools/envs/milestone2/Scripts/python.exe -B scripts/answer_question.py examples/constructed/before/manifest.json --question "What is the default timeout?" --target explicit_version --requested-version 1 --embedding-directory .tools/models/minilm --version-filter
```

`.tools/models/minilm` is a placeholder for the explicitly installed, pinned
embedding assets inside the project, not a download request. The command requires
compatible local ML dependencies, those complete assets, and a localhost Ollama
service with the selected model already available. It must not fetch missing
assets. The default model candidate is `qwen3:1.7b`; omit `--version-filter` for
the basic retrieval configuration while preserving the other settings.

A real subprocess test of the missing-assets path returns exit code 2. That
verifies the failure path only; no successful live answer is claimed. The command
prints a JSON trace; an answer pending human review is not a correctness pass.

## Full-dataset comparison command - same setup requirement

```powershell
.tools/envs/milestone2/Scripts/python.exe -B scripts/run_local_cases.py examples/constructed/before/manifest.json examples/constructed/after/manifest.json examples/constructed/cases.json --embedding-directory .tools/models/minilm --repeats 2
```

The command schedules every case against both snapshots using basic and
version-filtered retrieval. All other common configuration is held fixed.
`--repeats` accepts 1 through 5 (default 1); repeated runs do not use answer
caching. Explicit requested versions remain unchanged across snapshots.
The existing seven cases remain draft development cases. This is trace
collection for review, not an automatically graded benchmark.

The JSON output retains planned/recorded counts, index and generation failures,
review status and provenance. Failed index construction retains planned case
records in the error denominator rather than silently omitting them. The command
returns exit code 2 if run errors occur. No correctness scores or invented human
judgments are produced.

Offline regressions include constructed double-only repeated policy records and
deliberately injected index failures. They test orchestration and error accounting;
they are not live-model results, observed assistant failures, or benchmark scores.

## Resource and delivery boundaries

Per-push approval is waived until further user instruction. Remote changes must
still preserve existing work. This grants no additional download/install authority.
The user deferred the 12 GB folder / 4 GB download proposal and instructed work
to continue independently. No immediate answer is pending and no renewed request
is needed now. The existing 250 MB folder ceiling holds. No expanded model
downloads or global installations have been performed for these checks.

The [download proposal](MILESTONE_2_DOWNLOAD_PROPOSAL.md) records the requested
limits and gates. Keep intentional assets, caches, profiles, and temporary files
inside the approved folder. Ordinary tests/startup must not download models.

## Next acceptance steps

1. Publish the independently reviewed offline checkpoint.
2. Reconcile remote source hashes with the executed manifest and preserve
   historical Milestone 1 evidence.
3. Keep expanded ML/runtime downloads deferred unless the user later authorizes
   the resources; continue work that fits the existing allowance.
4. Verify real dependencies/assets and run local integration and the measured
   ten-question hardware smoke test if setup is approved.
5. Record actual results and errors before claiming Milestone 2 completion.

## Primary integration references

These describe intended boundaries, not proof of tested installation behavior.
Check capabilities against installed versions before relying on them.

- [Ollama generate API](https://docs.ollama.com/api/generate)
- [Ollama local-operation guidance](https://docs.ollama.com/faq)
- [Initial model candidate](https://ollama.com/library/qwen3:1.7b)
- [Embedding model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
