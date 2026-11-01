# Current state - Milestone 2 offline work complete; live acceptance blocked

- User authorized Milestone 2 work and waived per-push approval until further notice.
  This does not authorize additional downloads or installations.
- Local chunking, question/prompt/response contracts, embedding/index adapters,
  bounded localhost Ollama client, and single-question orchestration are implemented.
- Added explicit scripts/answer_question.py and process-local offline/cache
  configuration; the command requires separately installed assets and dependencies.
  Missing-assets exit code 2 is tested; successful live execution is unverified.
- Added full-dataset scripts/run_local_cases.py orchestration for both snapshots
  and retrieval configurations, repeated runs without answer caching, and retained
  error denominators. Draft cases and double outputs are not benchmark results.
- Published smoke unit: ten-question smoke harness, explicit CLI, constructed
  hardware-only inputs and residency observations; offline checkpoint reviewed.
  New evidence is separate in docs/evidence/milestone2-smoke-contracts: 195 executed
  tests, zero failures/errors/skips, plus real CLI checks. Brain approved the
  limited checkpoint with all 55 tested source hashes independently matching.
  Run f26de47c60b1430783205d64ef8c0e9c; source ID
  78c2e05518dfdfcefd1436bb823dfee45c03e7eaf07e8b2a5dcf5ab3720efd80.
  No live measurements are claimed; CPU observation differs from requested control.
- Published readiness unit: explicit real-NumPy integration checks and contained
  Windows runtime planning/start controls. Final source run executed 206 ordinary
  tests with zero failures/errors/skips, plus real foundation CLI checks. Actual
  read-only runtime plan returned missing_runtime/exit 2 without state changes or
  native execution. The separate NumPy attempt was unavailable (exit 1, zero verified
  numeric checks). All three observations use the same frozen source identity.
  Brain approved the limited readiness checkpoint: all 59 source hashes match,
  and ordinary checks, runtime-plan and unavailable integration evidence agree.
  Native runtime execution remains unverified; tests use explicit process doubles.
- Current evidence run: f196d7458a5f46d894857666e69224ca; source ID:
  6d56aeec4f6fb6e242aada783465786d01e8ea2205fbd325f4f1da18b0dde188.
- Offline verification uses explicitly labeled tokenizer/index/transport doubles.
  Published pipeline checkpoint executed 183 tests with zero failures/errors/
  skips, plus real foundation CLI checks, on Windows/Python 3.15.2 with verified
  source-import test dependencies. Brain approved this limited offline checkpoint
  and independently verified all 49 source hashes and the final regression fixes.
  Real NumPy, sentence-transformers, Ollama inference, and hardware performance
  remain unverified.
- Evidence run: 2e4af53709f549b38fa16cae66932cc3; source ID:
  293ce31f394b3f5205cd31b8ef190fde6ee58b0c6eb32dea0784d0463b2c7aa0.
- Fixed repeated-offset chunk progression and forged chunk metadata; regressions
  protect snapshot/evidence identity without claiming semantic correctness.
- User deferred the 12 GB / 4 GB resource proposal; the existing 250 MB folder
  ceiling holds. Continue independent implementation without asking again now.
  No new ML/model downloads were performed for the contract checks.
- Pipeline 74ca2f6 and smoke e9ff0c0 are published; all 49/55 corresponding remote
  source hashes were reconciled. Their evidence is preserved historical data.
- Readiness checkpoint ddc9862540157c45a51da303701b578d8ba95924 is published;
  all 59 remote source hashes match its recorded manifest. Its scoped observations
  remain 206 passing ordinary tests, missing runtime/exit 2, and unavailable
  NumPy/exit 1 with zero verified numeric integration checks.
- Independent Milestone 2 implementation, preflight and scaffolding are complete.
  Remaining real acceptance is blocked by missing ML dependencies/runtime/assets
  and the user's deferred expanded-resource authorization. No renewed request now.
- Next: only when resources are later authorized, verify real numeric/embedding
  imports and live inference, measure ten CPU queries, and check native write
  containment. No Milestone 3 work or additional placeholder features are started.
- Existing folder footprint is approximately 14.6 MB under the 250 MB ceiling;
  zero project spending and no new model/runtime assets.
- Milestone 2 is not complete. See docs/MILESTONE_2_PROGRESS.md.

## Historical records - superseded status and authorization

The entries below preserve earlier observations. Their current/next instructions,
per-push approval statements, and "Milestone 2 unstarted" status describe past
stages. Current authorization and work status are stated above.

# Earlier Milestone 2 readiness - download approval pending

- User authorized Milestone 2 work and revoked per-push approval until further notice.
- Existing Python 3.15.2 is an installation candidate; published CPU/native
  wheels were checked, but the full ML resolution/imports remain unverified.
- Prepared docs/MILESTONE_2_DOWNLOAD_PROPOSAL.md and machine-readable metadata.
- Request: 12 GB folder ceiling and 4 GB initial-download ceiling; estimated
  initial transfer 3.2–3.6 GB, including a 500 MB CPU-wheel allowance.
- Only metadata was retrieved. No large downloads, global installations,
  model inference or embedding run occurred. The current 250 MB limit holds.
- Shell networking remains restricted. A reviewed repo-local command may need
  to be run in the user's normal terminal if the restriction remains.
- Next: obtain resource approval, preflight complete assets/hashes/expanded ZIP
  totals, then implement and verify the defined Milestone 2 pipeline.
- Keep ordinary tests/startup offline and all caches/profile/state inside the folder.

## Previous audit history

# Current audit status

The complete Milestone 1 audit found verification/input gaps missed by the
original suite. The user approved publication of the reviewed audit fixes.

- Latest run: 92 executed tests, zero failures/errors/skips, real CLI checks.
- Actual inherited collect-only/plugin/optimization settings were ignored.
- All 34 tested source hashes independently checked by Brain.
- Source ID: a489c9c88098203b30366d4fe9aebfa0a9222277a8d1c5f483329c366503afa6.
- New evidence: docs/evidence/milestone1-audit; original 52-test evidence retained.
- Corrected stale-success, environment overrides, concurrent writers, JUnit
  validation, reserved/special paths, JSON errors, redirects/response limits,
  evidence placement and dependency hash checking.
- Scope and setup limits remain explicit in docs/MILESTONE_1_AUDIT.md.
- Next: publish the approved update, reconcile published source hashes, and hand off the audit.
- Milestone 2 remains unstarted.

## Earlier Milestone 1 history

# Plan and current state

## Milestone 1 — verified source-run configuration

Completed:
- Strict immutable snapshot and case schemas; exact content/metadata hashes.
- Deterministic additions, removals, edits and manifest metadata changes.
- Readiness command with disk information, explicit unknown hardware, and
  opt-in localhost model inventory.
- Two constructed snapshots and seven draft development cases.
- Source-only isolated test environment using existing Python 3.15.2.
- Three review fixes: actionable resolution errors, invalid Unicode rejection,
  and same-domain dataset validation, with regression tests.
- Reproducible offline runner and real subprocess CLI checks.
- Exact dependency releases, source provenance, source hashes, raw output,
  JUnit results, environment observations and Windows instructions.

Checks actually run:
- Original remote state inspected at 3026066735e6a6ed8379a5361ba1fbc98fc786a8;
  initial foundation delivered as 884e48301f10ba3cb447aa84635f318ae6c923bc.
- Local source copy reconciled byte-for-byte against all 38 original Git blobs.
- Actual isolated CPython 3.15.2 execution: **52 pytest tests passed**.
  Saved JUnit: 52 tests, zero failures, errors or skips.
- Real compare command matched expected-diff.json exactly.
- Real validate-cases reported seven drafts and zero human reviews.
- Default doctor ran without service calls/downloads; invalid CLI input returned
  a JSON error and exit code 2.
- Tested project source hashes captured before/after execution; unchanged.
- Five official dependency source trees and their generated version metadata
  verified against recorded hashes before use. The unchanged packaging copy
  has separately recorded origin/version and SHA256 hashes.
- Git 2.56.0.windows.3 and an Intel x64 processor identifier observed;
  environment reports 12 logical processors.
- Disk free space observed. RAM/GPU queries denied; reported 16 GB RAM remains
  user-supplied. Local Ollama endpoint refused connection; no inference run.
- Folder footprint approximately 13 MB at measurement, below approved 250 MB.
- Brain reviewed the complete core/test/helper source and actual evidence.

Execution limits:
- Standard PyPI downloads were blocked by the shell network sandbox.
- Tests used genuine upstream pytest and dependencies as explicitly staged
  source imports. No pip installation or project wheel build was verified.
- Only Python 3.15.2 was tested, not every version in the declared Python range.
- No model, embedding, latency, evaluator, UI or HTML-report claims are made.
- No human dataset reviews occurred.

Authorization and delivery:
- User approved a single-folder local source/test setup with a 250 MB ceiling,
  no global installation and no intentional writes outside that folder.
- Home-directory creation was denied. The permitted copy is in
  %TEMP%/Knowledge-Delta-; all agent-created setup assets are inside it.
- Initial setup/copy failures and source-dependency import failures were
  corrected before the successful recorded run.
- No GitHub Actions or paid service was enabled.
- User explicitly approved the verification update for publication.
  Future pushes continue to require separate approval.

Next:
1. Publish the user-approved verification update.
2. Verify the published source hashes match the executed source manifest.
3. Report the final Milestone 1 evidence and exact run command.
4. Wait for user instruction before Milestone 2.

## Deferred milestones

M2: inference/embeddings and measured hardware smoke test.
M3: evaluation/manual review, UI, JSON/HTML reports, 20 development cases.
M4: genuine licensed sources, held-out dataset and controlled evaluation.
M5: portfolio packaging. None of these milestones is claimed complete.
