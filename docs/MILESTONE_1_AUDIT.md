# Milestone 1 adversarial audit

## Outcome

The deeper review found real gaps that the original 52 tests did not cover.
The original recorded run did execute and remains valid for its earlier source.
The new audit fixes passed **92 actual executed tests**, with zero failures,
errors or skips, plus real CLI checks on Windows / Python 3.15.2.

Current evidence: [checks](evidence/milestone1-audit/checks.json),
[JUnit](evidence/milestone1-audit/pytest.xml),
[CLI](evidence/milestone1-audit/cli.json), and
[source hashes](evidence/milestone1-audit/source-manifest.json).
The earlier [52-test record](evidence/milestone1/pytest.xml) is preserved.

## Findings and corrections

| Priority | Finding in earlier code | Correction and regression evidence |
|---|---|---|
| P1 | A failed test/setup/timeout could leave a previous checks.json marked passed | Write current run ID/running state before checks; terminal failed/error records preserve diagnostics; passed status is persisted last |
| P1 | Inherited PYTEST_ADDOPTS could collect or select tests without executing the full suite; explicit plugins could still load | Ignore collection/plugin/optimization/interactive overrides; use explicit project config/test path; require executed JUnit cases |
| P2 | Concurrent writers could mix evidence from different runs | Nonblocking OS lock for each evidence directory, held through final persistence; a rejected writer leaves its owner's record alone |
| P2 | Suite-level JUnit errors or inconsistent aggregate counts could be overlooked | Validate root, failure/error elements, declared counts and executed cases; reject zero-test/collection-only results |
| P2 | Windows device aliases such as CON .md bypassed the stem check; special files could be opened as documents | Normalize reserved-name stems and require regular production files before opening; tests avoid reading actual devices |
| P2 | Integer-decoder ValueError escaped the structured JSON error path | Translate parser ValueError/RecursionError into actionable ValidationError |
| P2 | The localhost inventory opener retained automatic redirects; responses were unbounded and weakly typed | Reject redirects, limit response to 1 MiB and validate model/digest types; decoder errors remain explicit |
| P2 | Evidence could be placed in source directories, invalidating its own run; copied packaging hashes were not rechecked | Reject source-directory evidence targets; bind dependency pins as tracked test inputs and verify packaging SHA256 too |

## Concrete reproduction

Before fixes, at fe2ee049cf603a24c07c24760d8da3996f79dc1f, the runner was called
with PYTEST_ADDOPTS=--collect-only. It returned result=passed even though pytest
reported only "52 tests collected". No evidence directory was supplied during
that probe, so the historical successful run was not overwritten.

The corrected runner was executed with these actual inherited values:

- PYTEST_ADDOPTS: --collect-only -k nonexistent
- PYTEST_PLUGINS: nonexistent.audit.plugin
- PYTHONOPTIMIZE: 1

The saved audit record lists the ignored overrides and **92 executed tests**.
The nonexistent plugin was not imported, and collection/selection settings did
not replace the full test run.

Other failure-process outputs and malformed JUnit documents in
tests/test_adversarial.py are explicitly constructed regression fixtures.
They are not model benchmark results or observed assistant failures.

## Fixture family correction

The two version-1 status-command questions shared the same fact/support but had
separate family IDs. Both now use widget-status-v1. A regression moves one to
the held-out split and confirms rejection without relabeling its family.
Both remain drafts; their relation is not independent benchmark evidence.

## Review scope

Reviewed the complete foundation package, both verification helpers, all tests,
constructed snapshots/cases, project configuration, setup guidance, and published
evidence. Brain independently reviewed the changes and recomputed all 34 current
tested file hashes.

Source ID:
a489c9c88098203b30366d4fe9aebfa0a9222277a8d1c5f483329c366503afa6

The current source manifest includes the checked-in dependency pin data.
The runner checks consistency against those trusted pins; it does not claim a
security attestation against a hostile local filesystem or deliberately altered
tests. Filesystem path hygiene is not a race-proof sandbox.

## Remaining practical limits

- Normal pip installation/package builds and other Python versions remain
  unverified because the available execution route uses staged source imports.
- Windows locking was executed; the POSIX branch was not exercised.
- If storage becomes unwritable, the process reports a persistence error but
  cannot guarantee that an older disk record can be replaced. Check exit status,
  run ID and timestamps rather than treating an existing file as a new success.
- A terminated process can leave a running record. Its closed OS handle releases
  the lock; lock-file presence alone is not proof a process is still running.
- Seven constructed case labels remain drafts. No model inference, human
  semantic review, RAG evaluation, UI or benchmark was performed.

No remaining material blocker was found for the reviewed Windows source-run
Milestone 1 configuration. This is bounded audit evidence, not a claim of
universal bug freedom or compatibility across every environment.
