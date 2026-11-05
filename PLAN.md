# Current state — Milestone 4 authorized and in progress

- On 2026-11-05 the user authorized real local model/embedding runs, genuine
  documentation, human-reviewed cases, controlled experiments and measured results.
- The user separately approved 12,000,000,000 bytes total project storage and
  5,000,000,000 bytes additional artifact payload including retries, with at most
  1,000,000,000 bytes for CPU embedding dependencies. These supersede the UI-only
  resource limits for this explicit setup; no global installs or security changes.
- First source batch: ten development cases using pinned MIT Pydantic
  documentation. A=v2 excerpts; B=same excerpts plus v1 models. Snapshot assembly
  is constructed, source material genuine. One explicit human case review, nine drafts; zero human answer reviews or live results.
- Implemented offline source/excerpt/case verification and explicit bounded model
  metadata preflight. Full dependency closure/space planning and native execution
  remain pending. See docs/MILESTONE_4.md, docs/EVALUATION.md and
  docs/MILESTONE_4_RESOURCE_PROPOSAL.md.
- User reported loading and inspecting scripted replay in the new local web UI.
  This is a manual workflow observation, not an automated visual/layout audit or
  dataset correctness review.
- Verified checkpoint: 389 offline tests passed, zero failures/errors/skips, run
  edaa1763bbb84c20b6f79524a448245f. Actual CLI verified the source bundle and
  exported 40 clearly simulated Pydantic records: all await semantic review,
  no live generation. The larger-source fixture prompt overflow was reproduced
  and fixed with traceable fixture-only quote windows; live retrieval is unchanged.
- The agent shell's five bounded metadata requests failed with WinError 10013.
  No assets were downloaded. The normal-terminal metadata command is the next
  external execution step; its report must be inspected before installation.
- Next: inspect actual runtime metadata, freeze genuinely
  human-reviewed cases, install only validated assets and execute controlled runs.

## Historical Milestone 3 checkpoint (preserved)

# Standard-library UI checkpoint

- The user explicitly approved option 1 on 2026-11-05: replace Streamlit as the
  default UI with Python standard-library HTTP plus HTML/CSS/JavaScript. Keep
  Smart App Control On. No blocked native file or protection setting was modified.
- New entry point: scripts/run_web.py --serve, bound to 127.0.0.1:8501. Existing
  controller/metrics/review/export behavior is reused. Loading records makes no
  model requests. Legacy Streamlit and its installation evidence are retained.
- Focused real HTTP checks passed, including fixture/load/import/review/export,
  stale-revision rejection and a subprocess with third-party imports disabled.
  The verified full suite executed 373 tests with zero failures/errors/skips,
  run 797bcc303da64a88bdb4534e430bf23b. Evidence:
  docs/evidence/milestone3-local-web-verified. Earlier observations are preserved:
  milestone3-local-web passed on the initial source; milestone3-local-web-final
  exposed a Windows TCP reset on rejection with an unread body. Consuming bounded
  request bodies before rejecting actions fixed that response path.
- Browser automation host access was unavailable. Native browser verification
  was stopped after detected user activity changed the active tab. No new-app
  screenshot or successful visual interaction is claimed. User visual review is
  the next acceptance step; see docs/LOCAL_WEB_UI.md.
- The 750 MB folder ceiling and 150 MB artifact allowance remain in force. The
  new UI requires no additional package or model download. This historical checkpoint
  preceded the user's subsequent Milestone 4 authorization.

## Earlier UI setup observations (preserved)

- The user's approved setup installed all 34 locked packages. The final import
  check failed on an unsigned pandas native module, with Code Integrity event
  3077 naming VerifiedAndReputableDesktop. No security settings were changed.
- Independent NumPy/PyArrow imports succeeded. The actual NumPy integration suite
  executed 15 tests, all passing, with labeled tokenizer/vector doubles. This is
  not live model integration. Evidence: docs/evidence/milestone3-ui-installation.
- Download reservations are 86,786,569 bytes of 150 MB; later folder inventory is
  371,959,665 logical bytes of the 750 MB allowance. No installation peak is claimed.
- Next: confirm the Windows Security protection state and identify a legitimate
  policy/publisher resolution. Do not redownload or rerun the blocked native import
  merely to repeat the same failure. Streamlit rendering and live inference remain
  unverified. See docs/MILESTONE_3_UI_INSTALLATION_STATUS.md.

- The user's normal-terminal inspector completed successfully. The saved report's
  source hash, selected wheel tags, active dependency constraints and totals were
  independently checked offline. It resolved 34 candidate wheels: 86,786,535 bytes
  compressed and 280,478,795 bytes of declared expanded files. No installation.
- These packages alone exceed the former 250 MB total-folder ceiling. The user
  approved 750 MB total storage and at most 150 MB future UI artifact
  transfer; the conservative plan using the later larger folder inventory is
  694,104,324 bytes. Actual installer peak is unverified. Neither requested limit
  is an open-ended allowance. Models remain excluded.
- The bounded setup helper and its 17 focused offline tests are implemented.
  The full suite executed 358 tests with zero failures/errors/skips, run
  712d4f2b0aab427ba5a2453a3cd09c70. Actual default-plan execution returned ready
  with 34 pending packages and made no network requests or installation changes.
  Evidence: docs/evidence/milestone3-ui-setup-helper. Real setup/imports remain
  unverified until the normal-terminal installation command runs.
- Next action: use the user's working normal-terminal connection for explicit UI setup.
  Preserve the approved wheel lock, resource ledger and original inspector output.

- User authorized fixture-based Milestone 3. On 2026-11-04 the user retired
  Deliverer, briefly required milestone push approval, then explicitly granted
  all push permissions again. The primary agent handles tested repository
  checkpoints directly until that instruction changes.
  Keep all intentional files project-local,
  preserve remote work, spend zero, avoid global/model installs, and stay below
  the newly approved 750 MB UI-only ceiling. Non-model UI dependencies may be set up within that ceiling
  after full compatibility/footprint checks; none have been installed.
- Published saved-run/metrics checkpoint: 0dfa9ac1b6b71f5c5b7aaabe23a5c02db0f497bb,
  with 294 passing tests and all 127 remote source hashes reconciled. Prior proof
  and sample artifacts remain historical records.
- Current unit exposes optional independent reference-label JSON and abstention
  judgments through the controller, CLI and UI source, preserving them in escaped
  exports. Reference inputs are project-local lists capped at 16 MiB, require exact
  result bindings and default to no labels. Fixture metrics remain ineligible/null.
  The actual offline run executed 313 tests with zero failures/errors/skips,
  run 8d929a4f44d04dbd822b7a85115f1347, source ID
  90d3cd8df8d4ffe705faf951e8f73709eec78619ba2bbe65dc401578b5db6fc0.
  Evidence: docs/evidence/milestone3-measurement-inputs. Brain independently
  verified all 129 source hashes and the 313-test evidence and found no blocking
  issue. Actual empty-reference CLI inspection/export retained 80 fixture records,
  zero human reviews and null scores; synthetic labels exist only in tests.
  The user approved the tested checkpoint and then granted all push permissions
  on 2026-11-04. Published commit bf3a8a1187d175477595fd64659418d3b849437d
  contains its 16 files plus two metadata-only UI proposal files. All 129 tested
  source files match the published Git objects; all 53 prior evidence/sample
  files are unchanged. No package/model installation or storage expansion was
  authorized by the push instruction.
- The broader workflow audit identified and fixed a substantive gap: the review
  controller now imports saved raw experiment JSON as well as replaying fixtures.
  Manifest/dataset/origin checks preserve original answers/evidence; no gold-answer
  regeneration or new inference occurs during import. CLI/UI controls identify
  the selected configuration and repetition.
- Separate assistant and testing-tool metrics retain honest denominators, errors,
  missing judgments and provenance. Assistant accuracy needs eligible reviewed
  live results. Failure-flag precision/recall needs independently attested
  reference labels; identity/execution claims are not authenticated.
- Historical published source ID:
  55635b9d92192d36dcd4768c3e04085129237447399654898c690d717bee16c8.
  Run 026df346a922443abf76d9bc9181c8a4 executed 294 tests with zero failures,
  errors or skips. Brain independently checked all 127 source hashes and the
  final CLI preservation/provenance proof, clearing this bounded checkpoint.
- Evidence: docs/evidence/milestone3-run-import-final. Actual saved-run CLI
  imported/exported 80 fixture records and 40 comparisons with input bytes
  unchanged, zero human reviews, no inference and null assistant accuracy.
  Earlier docs/evidence/milestone3-run-import remains intermediate history.
- Current twenty constructed development cases remain drafts. TEST-ONLY temporary
  database reviews are not real human validation. Historical simulated samples
  demonstrate seven comparison statuses, not measured assistant performance.
- Published historical fixture checkpoint 2c9e9d5 recorded 250 tests and 115
  reconciled remote source hashes. Historical interface checkpoint 4c270e0 recorded
  266 tests and 124 remote source hashes. Their evidence/sample reports remain
  preserved; the older local 257-test controller run is also historical.
- Real Streamlit remains unavailable: historical readiness returned missing package/
  exit 2 without state changes, real AppTest returned unavailable/exit 1 with zero
  UI checks verified, package/HEAD probes failed network access, and base/user-site
  inventory found no usable installation. Controller tests do not verify rendering,
  browser interaction, actual launcher containment or live model integration.
- The user reported HTTP 200 from the requested normal-terminal PyPI HEAD check.
  Agent-side PyPI requests still fail with WinError 10051. This identifies a manual
  inspection route, not a successful installation or a budget change. The bounded
  setup inspector now passed 341 offline tests with zero failures/errors/skips,
  run f65c4026fd3b47d188990fc008e0823e. Evidence is in
  docs/evidence/milestone3-ui-preflight-final. The earlier 340-test observation
  is retained as intermediate evidence before the output-preservation fix.
  The script is ready for an explicit normal-terminal run. It reads metadata and
  bounded archive ranges, installs nothing, and refuses to overwrite existing
  files. Actual dependency/expanded-size resolution remains unverified until run.
- Last folder measurement: 78,348,353 logical bytes including ignored artifacts,
  below 250 MB. No package/model downloads or global installation occurred.
- Earlier metadata-only preparation is preserved in
  docs/MILESTONE_3_UI_DOWNLOAD_PROPOSAL.md. The successful user-run inspection and
  new explicit budget proposal above supersede its unresolved-closure status.
  Actual UI/live acceptance still needs missing dependencies/runtime/assets.
  Milestone 3 is incomplete. Do not advance to Milestone 4 or add speculative
  placeholder features. See docs/MILESTONE_3.md and docs/MILESTONE_3_INTERFACE.md.

## Milestone 2 checkpoint - offline work complete; live acceptance blocked

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
  containment. Milestone 3 fixture work is separately authorized above; it does
  not complete or replace these live Milestone 2 acceptance checks.
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
