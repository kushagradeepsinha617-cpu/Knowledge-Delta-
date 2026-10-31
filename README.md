# KnowledgeDelta

A local tool for testing whether documentation changes cause incorrect answers
in an AI documentation assistant.

**Status:** Milestone 1 foundation implementation prepared. Python execution and
live inference are unverified. This is an engineering portfolio project;
commercial demand and novelty are not established.

## What is available in the foundation

- Immutable, reproducibly identified document snapshots.
- Detection of added, removed, content-edited and metadata-edited documents.
- Strict case validation, exact evidence references and snapshot bindings.
- A read-only readiness command.
- Two constructed snapshots and seven draft development cases.
- Offline pytest tests and an independently calculated expected JSON diff.

There is no answering model pipeline, evaluator, Streamlit UI or HTML export yet.
The sample diff is document comparison, not an assistant benchmark.
No human dataset review has occurred.

## Windows setup (explicit, user-run steps)

These instructions describe future local setup. Agents have not cloned this
repository, installed anything, downloaded models, or created local project files.

Prerequisites: Python 3.11+ and a local copy of this repository.
If Python is not installed, install it explicitly from https://www.python.org/downloads/windows/.
Git is optional if you download the repository using GitHub instead.
Open PowerShell in the repository root.

Create the isolated environment and install the small foundation plus test extra.
These setup commands use internet access and create local environment files:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pip list --format=json
```

The proposed Python floor and test dependency range have not been resolved or
executed in the agent environment. Record the actual package versions from the
last command; there is no verified lockfile yet.

## Run without Ollama or model downloads

All commands below print JSON and run from the repository root.
They do not generate answers or download models.

```powershell
.\.venv\Scripts\python.exe -B -m knowledge_delta doctor
.\.venv\Scripts\python.exe -B -m knowledge_delta compare examples/constructed/before/manifest.json examples/constructed/after/manifest.json
.\.venv\Scripts\python.exe -B -m knowledge_delta validate-cases examples/constructed/before/manifest.json examples/constructed/after/manifest.json examples/constructed/cases.json
```

Expected comparison: five document records:
- widget.config: content and source-revision metadata changed.
- widget.install: wording and source-revision metadata changed.
- widget.legacy: removed.
- widget.scope: version metadata changed, content unchanged.
- widget.v2: added.

Expected dataset summary: seven cases, seven draft, zero human-reviewed.
Expected diff: [examples/constructed/expected-diff.json](examples/constructed/expected-diff.json).
Changing fixture bytes intentionally invalidates dataset snapshot bindings.

Optional explicit local Ollama inventory request, without generation/download:

```powershell
.\.venv\Scripts\python.exe -B -m knowledge_delta doctor --check-ollama
```

It requests only http://127.0.0.1:11434/api/tags with a timeout.
A present model is not a passed inference test. Installation/model pulling and
the ten-query hardware test belong to Milestone 2, after user instruction.

## Offline tests

After the explicit setup, tests need no network, Ollama or model assets:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

Test inputs are read-only fixtures or in-memory edits. No test downloads models.
The tests cover identity/isolation, metadata/default changes, removals, unsafe
paths, invalid schemas/evidence, review/split rules, CLI output, and missing
services. Later inference/evaluator/cache acceptance tests are not claimed here.

**These Python commands have not yet been run by the agents.**
See [verification](docs/VERIFICATION.md) for checks actually performed.

## Design and next steps

See [project scope](PROJECT_SPEC.md), [plan/status](PLAN.md),
[decisions](docs/DECISIONS.md), [schema contracts](docs/SCHEMAS.md) and
[dataset card](docs/DATASET_CARD.md).

Interview concept: a document keeps its identity across edits, while a snapshot
gets a new content-derived identity when its evidence or relevant metadata changes.

Milestone 2 will add local retrieval and inference only after instruction.
The full application will eventually start with a documented local Streamlit
command; that interface is not implemented at this milestone.
