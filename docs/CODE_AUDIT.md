# Pre-portfolio code audit

The user requested a code audit before portfolio packaging. Six confirmed issues
were fixed. The complete ordinary offline suite executed **568 tests**, with
**zero failures, errors or skips**, on Windows/Python 3.15.2 using the existing
verified source dependencies. This adds 49 regression cases to the preceding
519-test checkpoint. No benchmark answers or human judgments were changed.

## Scope and findings

The review covered the snapshot/case contracts, chunking and versioned retrieval,
local embedding/inference adapters, experiment orchestration, imported-run
validation, review journal, metrics, HTML/JSON exports, local interface and setup
helpers. Brain independently reviewed the evaluation/review/export paths. This
was source inspection plus reproducible fault tests, not exhaustive proof of all
possible inputs, operating systems or execution paths.

| Confirmed defect | Correction and regression evidence |
| --- | --- |
| An imported answer could name one configuration while recording different retrieval settings, prompt budgets or request budgets. | Validate configuration types and exact row/envelope agreement, require complete answered-live controls, compare prompt/request budgets and reject excess retries. Covered by `test_evaluation.py` and `test_saved_run_review.py`. |
| An answer labeled live could contain explicitly simulated generation or contradictory generation status/completion flags. | Such contradictions now produce a run error; human pass labels cannot override that integrity error. Scripted fixtures cannot conceal a generation record. Covered by `test_evaluation.py`. |
| A report export could target the active `.venv-ml` environment. | Protect both `.venv` and `.venv-ml`, including nested paths, before writing either output. Regression checks preserve pre-existing environment files. Covered by `test_fixture_reports.py`. |
| Ollama-runtime and MiniLM download redirect handlers inherited urllib's unbounded redirect-body draining outside the payload ledger. | Close redirect bodies without reading them; only the existing bounded final-response reader consumes artifact data. All five supported redirect statuses and redirect-loop limits are tested for both handlers in `test_download_redirect_accounting.py`. |
| A cached Ollama receipt could omit executable/library hashes and still be treated as verified. | Require pinned release/archive identity, the known executable hash, exact installed file inventory and matching recorded hashes before native execution. Covered by `test_ollama_setup.py`. |
| A cached Python receipt could omit runtime entries and skip verification before creating the ML environment. | Require the executable/venv identities, pinned release/archive identity, exact installed inventory and matching hashes. Covered by `test_ml_python_setup.py`. |

Runtime receipts are local records, not signed attestations against a malicious
local owner who can also edit the application. Initial archives remain pinned by
their existing SHA256 checks. The redirect fix bounds application-consumed
payload; it is not a measurement of all transport-layer network traffic.

## Checks actually run

- Full offline suite: run `9c9c70b5d60a45f9ab3634e156b3aec4`, 568/568 executed,
  22.65 seconds of pytest execution. JUnit and stdout are preserved.
- Real subprocess CLI checks: expected document diff, seven initial draft cases,
  download-free default readiness and actionable invalid-input errors.
- All 213 hashed source/configuration/fixture files matched before and after
  execution. Source ID:
  `f3b0648ea8791e7f0908478c38bacc14af9470003549b3d4dfbcbd2895e30a9c`.
- Saved 128-token experiment: unchanged 1 mechanical failure, 21 unresolved
  answer judgments, 18 run errors. Saved 256-token experiment: unchanged
  2 mechanical failures, 38 unresolved answer judgments, 0 run errors.
- Published human-review ZIP: reproduced the exact saved counts and metrics for
  four actual answer reviews, without opening the private journal.
- Genuine reviewed-case run: all four actual answers remain unresolved,
  with zero run errors. No approval or semantic judgment was invented.
- Installed Python receipt verified 2208 files; installed Ollama receipt verified
  75 files. These checks read/hash existing files without executing native code.
- No model inference, new artifact download, paid service or security-setting
  change occurred during this audit.

Reproduce the ordinary tests from the repository root:

```powershell
& '.\.venv\Scripts\python.exe' -B scripts/run_checks.py --source-dependencies --evidence-dir runs/audit-recheck
```

The saved-run compatibility probe also requires the existing project-local
runtimes and raw `runs/` artifacts from this working copy:

```powershell
& '.\.venv\Scripts\python.exe' -B docs/evidence/pre-portfolio-code-audit/verify_preserved_runs.py
```

See [checks.json](evidence/pre-portfolio-code-audit/checks.json),
[JUnit results](evidence/pre-portfolio-code-audit/pytest.xml),
[CLI evidence](evidence/pre-portfolio-code-audit/cli.json),
[source manifest](evidence/pre-portfolio-code-audit/source-manifest.json) and
[saved-run compatibility results](evidence/pre-portfolio-code-audit/compatibility.json).
Raw runs remain available in the existing lossless experiment report archives;
this audit does not republish environments or model files.

## Remaining limits

No additional confirmed defect remains open from this audit. That does not
guarantee an absence of bugs. Fresh pip installation, wheel builds, the full
declared Python compatibility range, POSIX locking and an automated visual UI
layout audit remain unverified. Existing bounded live-model measurements are
preserved; inference was not rerun for changes confined to validation, exports
and setup verification. Broad semantic accuracy, independent evaluator
precision/recall, a 60-human-reviewed-case dataset and a real held-out study
remain outside the demonstrated results.

Milestone 5 packaging has not started. The main engineering lesson here is that
recorded experiment configuration and provenance need consistency checks before
the evaluator can use them to compare results: a valid answer JSON alone does
not establish a valid experiment record.
