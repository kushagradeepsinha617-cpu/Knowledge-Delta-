# Local web interface

The user approved replacing Streamlit with this standard-library interface on
2026-11-05. It uses the existing comparison, evidence, review and export controller.
It does not import pandas, Streamlit, NumPy or PyArrow. Windows Smart App Control
remains On; the blocked pandas file is neither loaded nor modified.

## Start

From the repository root:

```powershell
.venv/Scripts/python.exe -B scripts/run_web.py --serve
```

Or, from any normal PowerShell terminal:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\run_web.py" --serve
```

Open **http://127.0.0.1:8501**. Ctrl+C stops the server. If that port is already in
use, the command reports an error; select another port explicitly with `--port`.
Without `--serve`, the command prints readiness and opens no listening socket.
No package installation, model request, download or automatic browser launch occurs.

## Review workflow

1. Leave the supplied manifests/dataset selected and choose **Load comparison
   records**. The complete example has twenty draft constructed cases, eighty
   scripted answers and forty comparisons. It performs no retrieval or inference.
2. Inspect the provenance notice, counts and document changes. Filters change
   the displayed rows, not the planned case matrix or run-error denominators.
3. Select a case/configuration/repetition. Read both answers, separate expectations,
   citations, exact recorded passages, checks and raw traces.
4. Save only your own evidence-based answer or expected-change reviews. Reviewer
   name and rationale are required. Abstention classification is available only
   for actual abstentions. A semantic pass cannot override a mechanical failure.
5. An outdated binding or revision rejects the save. Unsaved drafts survive case
   navigation; **Reload data and clear review forms** explicitly loads new records
   and clears those drafts. Answer reviews do not approve draft dataset labels.
6. Export HTML/JSON to a project-local directory. Different existing content is
   preserved. The links open the saved reports inline; no automatic Downloads-folder
   copy is requested. Personal review journals stay under ignored `runs/`.

Existing raw experiment JSON and optional independently assessed reference labels
can be loaded using project-local paths. The selected manifests, dataset and
annotations must match. Imported answers are preserved, not reconstructed from
expected answers. Origins/model identities in imported files remain recorded
claims rather than authenticated execution. No inferred human judgments are added.

## Implementation and limits

- Python `ThreadingHTTPServer`, bound only to `127.0.0.1`, serves three local assets.
  There is no extra frontend framework, hosted service or runtime dependency.
- UI actions use bounded JSON requests and a per-process request token. Host/origin
  checks reject cross-site requests. Arbitrary directory/file browsing is absent.
- Source text is rendered with DOM `textContent`; reports retain escaped HTML and
  restrictive content policies. Inputs and exports use the existing project-path
  and revision validation, not a second grading implementation.
- Operations are serialized within one server. The SQLite controller retains its
  cross-session optimistic revision checks. This is a local developer tool, not a
  public production service or an authentication boundary against local processes.
- This version loads fixture replay or saved run records. Actual local inference
  remains available only through the separately gated reference-pipeline commands;
  no live run is implied by loading records in this interface.

The legacy Streamlit adapter and historical setup evidence remain in the repository
for traceability. Its pandas policy block remains unresolved. Existing installed
packages are retained; this change does not uninstall or replace them.

## Verification scope

The final ordinary run executed **373 tests**, all passing with zero failures,
errors or skips (run `797bcc303da64a88bdb4534e430bf23b`). Evidence is in
[local web verification](evidence/milestone3-local-web-verified/checks.json).
Earlier source runs and the intermediate Windows connection-reset failure remain
preserved separately; the final server consumes bounded bodies before rejection.

The ordinary suite tests the real localhost HTTP server: fixture loading, saved-run
import, answer/abstention/relation review, stale revisions, exports, source-path
boundaries, request validation, static assets and cross-site rejection. A separate
subprocess disables all four third-party imports and loads the fixture workflow.
All TEST-ONLY review writes use isolated copied projects, not the real journal.

The JavaScript syntax and static element references were checked. Browser-host
automation was unavailable; attempted native browser interaction was stopped when
user activity changed the target tab. No successful browser interaction, layout
inspection or screenshot of this new app is claimed. A manual browser check is
still needed. No human dataset review or live model inference is verified here.

An interview point: the interface calls the same revision-bound controller as the
CLI, so changing the UI technology does not redefine correctness or grading rules.
