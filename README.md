# KnowledgeDelta

A local tool for testing whether documentation changes cause incorrect answers
in an AI documentation assistant.

**Milestone 1:** the defined foundation passed **92 offline pytest tests** and
real CLI checks in the configuration below.

**Milestone 4 is in progress.** Ten Pydantic development cases now use pinned,
MIT-licensed upstream documentation in a clearly labeled constructed snapshot
experiment. Seven cases are explicitly human-reviewed; three remain draft. Human reviews, real embeddings, local inference
and controlled measurements are pending. See [Milestone 4](docs/MILESTONE_4.md)
and the [Pydantic source/review batch](examples/pydantic/README.md).

**Milestone 3 fixture workflow:** The evaluator, fixture
replay, reports, manual reviews and local web interface are implemented. The user
approved replacing Streamlit with a Python standard-library interface that does
not use pandas. Smart App Control remains On. The user has manually loaded and inspected scripted replay; an automated visual
layout audit remains unverified. Live embeddings/model inference remain unverified.
The user approved bounded model setup: 12 GB total project storage and 5 GB
additional artifact payload including retries, at most 1 GB for CPU embedding
dependencies. Exact compatibility/hash/space checks still precede downloads.
See [Milestone 3 progress](docs/MILESTONE_3.md) and
[Milestone 2 integration limits](docs/MILESTONE_2_INTEGRATION_READINESS.md).
Saved raw experiment JSON can now be imported for review/reporting without
regenerating answers. Assistant and testing-tool metrics remain separate, with
explicit exclusions and unavailable scores when eligible labels do not exist.

## Verification scope

**Proven setup:** Windows with **Python 3.15.2**, using explicitly staged upstream
dependency sources inside an isolated environment.

**Not yet verified:**

- Fresh installation through pip.
- Package and wheel builds.
- Other Python versions.
- POSIX file locking (for example, on Linux or macOS).
- Local model inference.

Milestone 1 completion refers to the foundation working in this recorded setup.
It **does not mean compatibility has been verified in every environment or that
the software is guaranteed bug-free**. The declared Python version range is not
a verified compatibility matrix.

See [the adversarial audit](docs/MILESTONE_1_AUDIT.md) and
[verification history](docs/VERIFICATION.md) for the evidence and limitations.

## Run the fixture report

For the local browser interface, run:

```powershell
.venv/Scripts/python.exe -B scripts/run_web.py --serve
```

Open **http://127.0.0.1:8501** and select **Load comparison records**. It works with
the standard library and existing fixture files; no further setup is required.
See [interface instructions and verification limits](docs/LOCAL_WEB_UI.md).

The standalone fixture report remains available:

From the repository root, using the existing isolated Python:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --simulate-judgments --output-dir runs/my-fixture-report
```

Open `runs/my-fixture-report/report.html` in your browser. This standard-library
workflow requires no model, service, or extra runtime package. Omit
`--simulate-judgments` to leave semantic judgments unresolved. Existing reports
with different content are preserved; choose a new output directory for a new run.

The [self-contained HTML sample](docs/samples/mvp-fixture/report.html) and
[machine-readable JSON sample](docs/samples/mvp-fixture/report.json) contain
**20 draft cases, 80 scripted answer records, zero human reviews and no model
execution**. Download the HTML file and open it locally; GitHub displays its source.
Simulated correctness labels illustrate the workflow and are not benchmark results.

The current local offline suite executed **373 tests**, with no failures, errors
or skips; see [local web UI verification](docs/evidence/milestone3-local-web-verified/checks.json).
The earlier [358-test setup-helper verification](docs/evidence/milestone3-ui-setup-helper/checks.json)
and subsequent 15 real NumPy checks are preserved separately. Those numeric checks
do not verify pandas or browser rendering.
The [341-test UI preflight verification](docs/evidence/milestone3-ui-preflight-final/checks.json)
remains preserved.
The earlier [313-test measurement-input verification](docs/evidence/milestone3-measurement-inputs/checks.json)
remains preserved.
The published saved-run checkpoint executed **294 tests**. Brain independently
checked all **127 source hashes** against the
[saved-run/metrics verification](docs/evidence/milestone3-run-import-final/checks.json).
The actual saved-run CLI preserved its input bytes and exported 80 fixture answers
and 40 comparisons, with zero human reviews and null assistant accuracy.
The [266-test interface checkpoint](docs/evidence/milestone3-interface/checks.json)
is preserved as historical evidence.
The earlier [250-test fixture checkpoint](docs/evidence/milestone3-evaluation/checks.json)
and sample reports remain historical evidence. Streamlit and live inference are
unverified; passing mocked launcher tests is not a successful UI launch.

## Review answers and check the interface

Import an existing raw experiment (the path below must already exist and its
snapshots/dataset must match the displayed defaults):

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --run runs/recorded-run.json --output-dir runs/imported-report
.venv/Scripts/python.exe -B scripts/review_fixture.py --run runs/recorded-run.json --case-id request-timeout-change --slot after --repetition 2
```

Repetition 2 must actually exist in that run; selecting it performs no generation.
For other inputs, pass matching `--before`, `--after`, `--dataset` and `--relations`
paths. See [saved-run prerequisites and metrics limits](docs/MILESTONE_3.md).

Optional measurement inputs are now wired into the local CLI/controller:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --run runs/recorded-run.json --reference-labels runs/reference-labels.json --output-dir runs/reference-report
```

The reference file must already contain independently assessed labels with exact
result bindings; no labels are created automatically. For an answer that actually
abstained, an explicit review save may include `--abstention-judgment appropriate`
with a pass or `--abstention-judgment unnecessary` with a fail. Reviewer identity,
rationale, binding and revision are still required. See the
[measurement-input schema](docs/MILESTONE_3.md#optional-measurement-inputs) before
using these options. Ordinary source tests cover these inputs; real UI rendering
remains unverified. Brain cleared this checkpoint; it is published as
[`bf3a8a1`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/bf3a8a1187d175477595fd64659418d3b849437d),
with all 129 tested source files reconciled and prior evidence preserved.

Inspect an answer and its review binding without writing a review:

```powershell
.venv/Scripts/python.exe -B scripts/review_fixture.py --case-id request-timeout-change --slot before
```

Saving requires your reviewer name, rationale, judgment, and the binding/revision
shown during inspection. Reviews are stored in an append-only project-local
SQLite journal; they do not automatically approve draft dataset labels.
See the [review and interface guide](docs/MILESTONE_3_INTERFACE.md) for commands.

Export your current inspections while keeping fixture provenance:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --include-manual-reviews --output-dir runs/reviewed-fixture
```

Check UI readiness (no install, model request, or server start):

```powershell
.venv/Scripts/python.exe -B scripts/run_web.py
```

This is the new standard-library interface. It does not load the blocked pandas
module or change Windows protection. The older `scripts/run_interface.py` and
Streamlit adapter remain historical alternatives; they are not required for this
interface. No startup command installs dependencies or downloads models.

The user reported a successful normal-terminal PyPI connectivity check. The
agent's Python still cannot reach PyPI. An explicit metadata/archive-directory
preflight is documented in the [UI setup proposal](docs/MILESTONE_3_UI_DOWNLOAD_PROPOSAL.md);
it installs nothing. The subsequent user-run preflight resolved 34 wheels declaring
280.5 MB of expanded files, exceeding the current 250 MB total-folder ceiling.
The [UI-only installation proposal](docs/MILESTONE_3_UI_INSTALLATION_PROPOSAL.md)
now has user approval for a 750 MB UI-only ceiling and a 150 MB future package-download
cap. The explicit setup helper passed offline checks and the user installed all
34 packages. Its final import check hit a Windows policy block on pandas. NumPy
and PyArrow import successfully; 15 separate real NumPy tests passed. No models
are installed. See the [actual setup status](docs/MILESTONE_3_UI_INSTALLATION_STATUS.md)
before taking further setup actions; do not redownload packages to repeat the failure.

## Foundation features

- Immutable snapshots with stable document IDs and reproducible snapshot hashes.
- Added/removed documents and independent content/metadata change detection.
- Strict case validation, exact evidence quotes, fixed requested versions,
  snapshot bindings, review labels and family split checks.
- Read-only readiness information and an opt-in localhost model inventory.
- Two constructed snapshots, seven draft cases, and a sample JSON diff.
- Reproducible CLI checks, pytest tests, source hashes and execution artifacts.

This milestone tests the foundation. The RAG answering pipeline, semantic
evaluation, Streamlit interface and HTML reports belong to later milestones.
The seven example cases have **zero human reviews** and provide no benchmark
or commercial-validation claims.

## Windows setup

Use an existing Python 3.11+ installation; only 3.15.2 was exercised here.
Open PowerShell in the repository root. Choose the actual Python executable
if Python is not in your PATH:

```powershell
# Replace this with your existing interpreter path.
$basePython = "C:\path\to\python.exe"
New-Item -ItemType Directory -Path ".tools\tmp" -Force | Out-Null
$env:TEMP = (Resolve-Path ".tools\tmp").Path
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = "1"
& $basePython -B -m venv .venv
.\.venv\Scripts\python.exe -B -m pip install --no-cache-dir -r requirements-test.txt
```

This is the intended ordinary dependency-installation route. The agent's network
sandbox prevented PyPI installation, so that installer step was **not verified**.
The tested source-only fallback and its exact revisions are documented in
[TEST_SETUP.md](docs/TEST_SETUP.md). Neither route installs an answering model.
The application runs directly from the repository; editable installation and
the optional console entry point are not required.

## Run the sample

From the repository root, these commands print JSON:

```powershell
.\.venv\Scripts\python.exe -B -m knowledge_delta doctor
.\.venv\Scripts\python.exe -B -m knowledge_delta compare examples/constructed/before/manifest.json examples/constructed/after/manifest.json
.\.venv\Scripts\python.exe -B -m knowledge_delta validate-cases examples/constructed/before/manifest.json examples/constructed/after/manifest.json examples/constructed/cases.json
```

The comparison produces five document-change records: configuration and
installation content/source-revision changes, legacy evidence removal, a
version-scope metadata correction, and a version-2 document addition.
See [the expected diff](examples/constructed/expected-diff.json).
Case validation reports seven drafts and zero human-reviewed cases.
Changing fixture bytes invalidates their dataset snapshot bindings by design.

An explicit local Ollama inventory check is available without generation:

```powershell
.\.venv\Scripts\python.exe -B -m knowledge_delta doctor --check-ollama
```

It queries only `http://127.0.0.1:11434/api/tags`; it does not download models.
The local service refused the connection during verification.

## Offline checks and evidence

After explicit dependency setup, run:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_checks.py
```

On the existing machine's separately staged source-dependency setup, the
**verified command** is:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_checks.py --source-dependencies --evidence-dir docs/evidence/milestone1-audit
```

.tools setup is never pushed. The source-dependency option requires the ignored `.tools/vendor` assets
described in TEST_SETUP.md; a fresh checkout does not contain those assets.

The runner rejects inherited pytest collection/selection/plugin overrides, verifies
JUnit execution and counts, and locks shared evidence outputs. It disables
bytecode, pytest caching and third-party plugin autoload,
keeps its temporary directory within the project, runs actual pytest, and checks
the real CLI in subprocesses. No test or application startup downloads anything.
An explicit evidence path saves JUnit XML, CLI output and a source-hash manifest.
An explicit evidence path updates its current-run records on success or failure.
Use a fresh output directory to retain previous runs. A busy directory is rejected.
An unwritable destination is reported as an error.

Checked-in results: [JUnit](docs/evidence/milestone1-audit/pytest.xml),
[checks](docs/evidence/milestone1-audit/checks.json),
[CLI output](docs/evidence/milestone1-audit/cli.json),
[tested source hashes](docs/evidence/milestone1-audit/source-manifest.json), and
[environment](docs/evidence/milestone1-audit/environment.json).

## Design and status

See [scope](PROJECT_SPEC.md), [plan](PLAN.md), [decisions](docs/DECISIONS.md),
[schemas](docs/SCHEMAS.md), [dataset card](docs/DATASET_CARD.md), and
[Milestone 1 acceptance](docs/MILESTONE_1_ACCEPTANCE.md).

Interview concept: a document keeps its identity across edits; its content hash
and the containing snapshot's identity change. This distinguishes an edit from
a removal followed by an unrelated addition.

Milestone 2 readiness is in progress; see the [download proposal](docs/MILESTONE_2_DOWNLOAD_PROPOSAL.md).
Large downloads are deferred. No AI model, UI, semantic evaluator
or production incremental-ingestion behavior has been measured.
