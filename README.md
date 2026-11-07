# KnowledgeDelta

Test whether documentation changes cause incorrect answers in an AI documentation assistant.

KnowledgeDelta compares two document snapshots, asks the same version-specific questions, and preserves the answers and exact evidence for review. A changed answer can be expected; an old document can still be correct for an old software version.

**Status:** working local application and exploratory evaluation. The expanded 60-case study is currently running under a frozen protocol. User approval of all definitions is recorded separately from item-level human review. [Review provenance](docs/REVIEW_PROVENANCE.md) explains that distinction.

## What you can inspect

- Stable document identities, content/metadata hashes, and snapshot additions, edits and removals.
- Separate snapshot indexes; basic semantic retrieval versus explicit software-version filtering.
- Local CPU inference with Ollama/Qwen and MiniLM ONNX embeddings, with no hosted fallback.
- Answer text, exact supplied passages, citations, model/configuration identities, malformed attempts and errors.
- Per-snapshot judgments, expected-change comparisons, manual review history and HTML/JSON exports.
- Clearly labeled fixture replay that works without models or downloads.

## Run the interface

From the repository root, using the existing project environment:

```powershell
& '.\.venv\Scripts\python.exe' -B scripts/run_web.py --serve --port 8501
```

Open **http://127.0.0.1:8501**. Leave the terminal open; Ctrl+C stops the service.
Choose **Scripted fixture replay**, then **Load comparison records**. File paths are under **Files and advanced options**. Fixture outputs and draft labels remain explicitly identified; this screen does not run a model.

For an existing saved experiment, choose **Existing run JSON** and supply its original snapshot manifests, frozen dataset, relations and raw run JSON. Loading records does not regenerate answers. See [interface instructions](docs/LOCAL_WEB_UI.md).

A fresh source-only UI environment needs Python and the standard library:

```powershell
py -3 -m venv --without-pip .venv
& '.\.venv\Scripts\python.exe' -B scripts/run_web.py --serve --port 8501
```

Python 3.15.2 and the separate Python 3.14.10 setup are the recorded Windows configurations; the declared Python range is not a verified cross-platform compatibility matrix.

## Run offline checks

The repository's verified source-dependency setup uses:

```powershell
& '.\.venv\Scripts\python.exe' -B scripts/run_checks.py --source-dependencies --evidence-dir runs/checks-new
```

The latest source checkpoint executed **583 tests**, with zero failures, errors or skips. Ordinary tests use constructed/fault fixtures and do not need Ollama, network access or model downloads. [Raw verification evidence](docs/evidence/milestone5-owner-approval-and-controls/checks.json) and [test setup](docs/TEST_SETUP.md) describe the environment and provenance.

For a conventional explicit test installation, the project declares the pytest dependency in `.[test]`. Keep setup/cache state project-local:

```powershell
New-Item -ItemType Directory -Force .tools/tmp, .tools/pip-cache | Out-Null
$env:TEMP = (Resolve-Path .tools/tmp).Path
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = (Resolve-Path .tools/pip-cache).Path
& '.\.venv\Scripts\python.exe' -B -m ensurepip
& '.\.venv\Scripts\python.exe' -B -m pip install -e '.[test]'
& '.\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider --basetemp .tools/pytest
```

This explicitly installs test dependencies and may use the internet. It is not application startup. The archived source-dependency test route and an offline wheel/fresh-pip-install probe have actually run; this conventional online test-install route and fresh resolution of the full ML stack have not been claimed as exercised.

## Actual observations

- The ten-question CPU smoke produced ten structured responses and zero run errors in **122.453 seconds**. This establishes execution, not semantic accuracy.
- A 40-record development experiment at a 128-token output cap retained **18 run errors**. The separate 256-token experiment completed **40/40 structured responses**, with zero run errors; recorded inputs were checked for the intended cap-only change.
- Four actual human answer judgments for one selected dict-pairs family showed a basic-retrieval regression and filtered recovery. This assisted, post-hoc example is not a representative accuracy estimate or proof of a sole cause.
- The core package built into a wheel and installed through pip in a fresh isolated environment, offline with already downloaded build tools. Installed CLI commands, packaged assets and the local fixture HTTP workflow passed.

See [recorded results](docs/EXPERIMENT_RESULTS.md), [human review evidence](docs/HUMAN_REVIEW.md), [local inference details](docs/LOCAL_INFERENCE_RESULTS.md) and [Milestone 5 scope](docs/MILESTONE_5.md). New expanded-study outcomes will be added after their completion/control checks pass.

## Evaluation boundaries

The expanded dataset has **20 development and 40 held-out cases** in one Pydantic domain. The held-out set spans **22 semantic families**. Its cases are withheld from project tuning, not claimed unseen during pretraining or independently authored.

The owner approved all definitions as a batch. Existing **11 item-level human case reviews** and **four human answer judgments** remain distinct from that authorization. AI-drafted cases and AI-assisted analysis do not become independent human ground truth.

The study separates genuine upstream revisions from constructed corpus changes. Whitespace controls test formatting stability. Empty evidence-removal snapshots exercise the evidence-only abstention policy; those abstentions are not model calls. Semantic accuracy and testing-tool precision/recall require qualifying judgments, with errors and unknowns visible in denominators.

## Architecture and setup

Python, Ollama, local Qwen, MiniLM ONNX Runtime, NumPy, JSON and SQLite. The local interface uses the standard library. Windows protection remains enabled; the ONNX backend and interface replacement are explicit engineering decisions after native-library policy failures.

- [Architecture and engineering decisions](docs/ARCHITECTURE.md)
- [Dataset card and source attribution](docs/DATASET_CARD.md)
- [Evaluation protocol](docs/EVALUATION.md)
- [Explicit local model setup](docs/MILESTONE_4.md)
- [Reproducible offline build/install probe](docs/evidence/milestone5-packaging/verify_packaging.py)
- [Demo script](docs/DEMO_SCRIPT.md) and [case study](docs/CASE_STUDY.md)
- [Code audit](docs/CODE_AUDIT.md) and [verification history](docs/VERIFICATION.md)

Model/dependency setup is explicit. Normal operation uses local assets; services bind to localhost. There is no required paid API, cloud hosting or subscription. Models and environments are excluded from GitHub.

## Scope and limitations

This is an exploratory AI-engineering tool for small English Markdown/text corpora, one software domain and one local answering model. It is not a production connector test, universal semantic grader or validated commercial product. Existing RAG evaluation and regression tools are prior art; no unique-invention claim is made.

Fresh core installation is verified in the recorded Windows/Python 3.14.10 environment. Fresh full-ML dependency resolution, other platforms/Python versions, OS peak memory and broad generalization remain unverified. Tests and successful execution do not guarantee bug-free software.

Earlier setup and verification details are preserved in the [archived README](docs/archive/README-before-milestone5.md).
