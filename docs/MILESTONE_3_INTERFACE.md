# Milestone 3 interface and manual-review checkpoint

This is the historical Streamlit checkpoint. The user approved a new default
[standard-library web UI](LOCAL_WEB_UI.md) that reuses the same controller and
does not load the blocked pandas module. Windows protection remains unchanged.

Current runtime gate: packages are now installed, but a Windows policy blocks
pandas. See [actual installation status](MILESTONE_3_UI_INSTALLATION_STATUS.md).
The missing-package observations below describe the earlier source checkpoint.

Latest setup authorization: 750 MB total project-folder storage and at most
150 MB of future UI artifact downloads. This supersedes the earlier 250 MB
fixture-only allowance without authorizing models or global installation.

Status: reviewed source checkpoint published as
[`4c270e0`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/4c270e0cc7d5f80a0a4bb78a37146fe70015ca40),
with all 124 remote source hashes matched to its 266-test manifest. The optional
Streamlit adapter, contained Windows launcher, review controller, CLI and stale-form
tokens are implemented. Streamlit is unavailable here; rendering, successful UI
launch and runtime write containment remain unverified. Milestone 3 is incomplete.

Current follow-up: saved experiment JSON import/review/reporting and separate
assistant/tool metrics are now implemented and independently reviewed. The final
offline run executed 294 tests with no failures/errors/skips, run
`026df346a922443abf76d9bc9181c8a4`; all 127 source hashes match identity
`55635b9d92192d36dcd4768c3e04085129237447399654898c690d717bee16c8`.
Evidence: [final run-import checks](evidence/milestone3-run-import-final/checks.json)
and [saved-run CLI proof](evidence/milestone3-run-import-final/saved-run-cli.json).
The actual import/export preserved the input bytes, retained 80 fixture records/
40 comparisons and zero human reviews, and left assistant accuracy null. See
[saved-run commands and prerequisites](MILESTONE_3.md) for `--run`/`--repetition`.
The 266-test observations below are preserved historical interface evidence,
not fresh UI integration results for this follow-up.

## Boundaries and existing evidence

The user authorized fixture-based Milestone 3 within 250 MB and zero spending,
with no model downloads. Larger Milestone 2 setup remains deferred. This interface
uses scripted fixture answers; no live inference, ML timing or assistant accuracy
is established. Existing 250-test sample reports/evidence remain historical.

The final ordinary offline run executed **266 tests**, zero failures/errors/skips
(7.30s), run `ee12938adf304f519a70eaf0e82d0dcb`, source ID
`63010193367c4fa932de8dec2b11ca40c7f4aa6a91b5362f9e1c09786f5bfc22`.
Brain cleared this bounded checkpoint and independently matched all 124 source
hashes and the source-bound observations below, with no blocking findings.

New records are in
[evidence/milestone3-interface](evidence/milestone3-interface/):

| Observation | Actual result | Limit |
| --- | --- | --- |
| Ordinary source tests and foundation CLI | 266 executed tests passed | Explicit UI/process doubles are not a rendered app |
| UI readiness command | Exit 2, missing Streamlit, no state changes | No server started |
| Manual-review inspection CLI | Exit 0, no journal creation/write | No human judgment recorded |
| Export including manual-review journal | 80 fixture records, 40 comparisons, zero human reviews | Zero passes; 7 mechanical failures, 71 unresolved, 2 run errors |
| Real Streamlit AppTest attempt | Exit 1, dependency unavailable | Zero UI integration checks verified |
| Package-index probe | Failed, no installation | Not evidence of package availability in this environment |
| Direct PyPI connection | WinError 10051, network unreachable | No artifact download or installation |
| Existing base/user-site package inventory | No usable Streamlit installation found | Recorded in `existing-packages.json`; no packages moved or installed |

## Readiness and future launch

From the project root in PowerShell, using the existing isolated Python:

```powershell
.venv/Scripts/python.exe -B scripts/run_interface.py
```

This is read-only readiness inspection. It does not install or fetch packages.
`missing_streamlit`/exit 2 is expected until compatible dependencies have been
explicitly installed within the folder and resource allowance. Streamlit 1.66.1
remains a metadata candidate; its full installed footprint/imports are unverified.
No new resource permission question is pending.

Only after compatible Streamlit is actually available in the isolated project
environment, explicit `--serve` starts the app:

```powershell
.venv/Scripts/python.exe -B scripts/run_interface.py --serve
```

The Windows launcher requests `127.0.0.1:8501`, disables usage statistics, browser
auto-opening and file watching, checks the port, and directs child profile/cache/
temporary state inside the project. These are configured controls; no real server
or universal write-containment verification has occurred. Startup never installs
dependencies or models. Other platforms remain unverified.

## Three manual-review flows

### 1. Inspect an answer or expected-change binding

```powershell
.venv/Scripts/python.exe -B scripts/review_fixture.py --case-id request-timeout-change --configuration basic --slot after
.venv/Scripts/python.exe -B scripts/review_fixture.py --case-id request-timeout-change --kind relation
```

Inspection prints the exact binding hash and current revision with the question,
expectations and available trace. It does not write a review or create a journal.
Read both answers and their evidence before making a judgment.

### 2. Explicitly record your own review

Add `--save`, the inspected `--expected-binding` and `--expected-revision`, plus
your actual `--reviewer` name and evidence-based `--rationale`. Answer reviews also
need `--outcome pass|fail|needs_human_review` and a justified `--failure-kind` for
a failure where required. Relation reviews use `--kind relation --relation
should_change|should_remain|undetermined`. These choice lists are documentation,
not literal shell arguments. Never manufacture a reviewer identity or rationale.

Binding and optimistic revision checks reject stale displays/concurrent updates.
The append-only SQLite journal stays under ignored `runs/`. A review of a scripted
answer does not approve the draft case labels or become a live-model judgment.
The Streamlit form uses the same controller/tokens, but rendered interactions
remain unverified until real AppTest/browser checks can run.

### 3. Export with the current journal

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --include-manual-reviews --output-dir runs/fixture-reviewed
```

This actual export path works without Streamlit. Without real human records or
simulated judgments it does not invent semantic passes. Stale stored reviews remain
visible instead of silently falling back to simulated labels. Exports preserve
fixture origin and separate human/mechanical/unresolved judgments.

No actual human reviews were saved for the delivered evidence. Unit checks that
exercise saving use temporary databases and explicitly TEST-ONLY reviewer labels.
They test storage/control behavior, not real human review or independent validation.

## Optional real UI integration check

After dependencies are explicitly installed in a contained environment with pytest:

```powershell
.venv/Scripts/python.exe -B -m pytest scripts/interface_integration_tests.py -q -x -p no:cacheprovider
```

The real AppTest tests are separate from ordinary tests. They copy fixtures into
a temporary project and use TEST-ONLY interactions; they never populate the real
review journal. Missing Streamlit fails setup visibly, without a skip/green claim.
The recorded attempt was unavailable, so no rendered-flow success is reported.

## Remaining acceptance

The reviewed source checkpoint is published and remotely reconciled. Actual
Streamlit imports/rendering, browser interactions and launcher containment remain
genuinely blocked by missing dependencies and failed agent-side network access.
Controller tests cannot substitute for those observations. No further placeholder
features or Milestone 4 work are planned; Milestone 3 remains incomplete.

One read-only PyPI HEAD check was requested in the user's normal terminal to
identify a usable manual setup/network route. The answer is pending; no conclusion
about the user's connectivity is established. That check installs nothing and
changes no resource/budget authorization. After the run-import follow-up the
existing folder measured 46,064,960 logical bytes, within 250 MB. No package/model downloads, installations
or live model operations occurred for this checkpoint.
