# KnowledgeDelta

A local tool for testing whether documentation changes cause incorrect answers
in an AI documentation assistant.

**Milestone 1:** the foundation passed **92 offline pytest tests** and real CLI
checks on **Python 3.15.2 / Windows**. This verification used explicitly staged
upstream dependency sources inside an isolated environment. Normal pip
installation, package builds, other Python versions, and local model inference
remain unverified. See [the adversarial audit](docs/MILESTONE_1_AUDIT.md) and [verification history](docs/VERIFICATION.md).

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

Milestone 2 awaits the user's instruction. No AI model, UI, semantic evaluator
or production incremental-ingestion behavior has been measured.
