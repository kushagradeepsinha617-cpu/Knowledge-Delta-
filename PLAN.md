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
