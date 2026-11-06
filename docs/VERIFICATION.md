# Milestone 5 current verification checkpoint

The study runner and bound owner-approval gate passed **583 offline tests**,
zero failures/errors/skips, run `25f2ca58950a4edcb05e740f1443b209`.
All 324 tested source/configuration/fixture files matched at the study freeze.
See `evidence/milestone5-owner-approval-and-controls/` for JUnit, raw output,
real CLI checks and exact source hashes. Failed earlier path-length fixture
verification remains preserved separately; it was not counted as a pass.

The core wheel built using existing setuptools 84.2.1 and installed through the
previously hash-verified pip wheel into a new isolated Python 3.14.10 environment.
Installed CLI help, doctor, real document comparison, packaged web assets and
the installed local HTTP fixture load passed. Receipt:
`evidence/milestone5-packaging/fe44d2c91ac643b894994586e9c44999.json`.
No network, model request, global installation or security change was used for
that probe. Fresh online/full-ML resolution and a cross-platform matrix remain
unverified; this checkpoint is broader than the earlier source-only test setup.

Actual Chrome desktop fixture screenshots are in `screenshots/` and described
in SHOWCASE.md. They show observed UI state, not live benchmark results. A full
viewport/browser visual audit is not established by those three captures.

The expanded study was started under a frozen protocol; successful complete
execution and semantic findings are not claimed by these code/setup checks.

## Earlier verification history (preserved)

# Initial Milestone 1 verification (historical)

This record describes the original 52-test source at commit fe2ee049.
The [subsequent adversarial audit](MILESTONE_1_AUDIT.md) found additional gaps,
fixed them, and recorded 92 executed tests for the current source.
The original artifacts below are preserved as historical evidence.


## Result and scope

**52 genuine pytest tests passed** on isolated CPython **3.15.2**, Windows x64.
The real comparison command exactly matched the checked-in expected JSON.
Case validation reported **7 draft / 0 human-reviewed** cases. Default readiness
and invalid-input CLI behavior were exercised.

This is foundation-tool verification. No model inference, assistant benchmark,
semantic grading, hardware inference-speed result or human case review occurred.

## Authoritative artifacts

- [checks.json](evidence/milestone1/checks.json): executed commands, exit codes,
  stdout/stderr, dependency mode and tested project source hashes.
- [pytest.xml](evidence/milestone1/pytest.xml): actual pytest JUnit results;
  52 tests, zero failures/errors/skips.
- [cli.json](evidence/milestone1/cli.json): real CLI subprocess output and checks.
- [source-manifest.json](evidence/milestone1/source-manifest.json): SHA256 hashes
  of tested package, helper, test, fixture and relevant configuration files.
- [environment.json](evidence/milestone1/environment.json): actual interpreter,
  import origins, readiness, package versions and measured local footprint.
- [dependency-sources.json](evidence/milestone1/dependency-sources.json):
  exact source revisions/files, build-version metadata and packaging provenance.

The runner requires source hashes to remain unchanged through the test run.
The source manifest excludes generated evidence and prose documentation, avoiding
circular hashes. Execution duration is a test-run observation, not an assistant
latency benchmark.

## Tested dependency configuration

| Dependency | Exercised release |
|---|---|
| pytest | 9.2.0 |
| pluggy | 1.6.0 |
| iniconfig | v2.3.0 source tag; module has no version attribute |
| colorama | 0.4.6 |
| packaging | 26.2, copied unchanged from existing pip 26.2.2 |
| Pygments | 2.20.0, complete official package source |

Official dependency source files were read through the GitHub connector and
verified against Git blob hashes. Licenses were preserved in the ignored local
setup. Pytest and pluggy needed their usual generated build-version files;
those files were explicitly generated from verified release tags and have
separate recorded SHA256 hashes. Testing algorithms were not modified.

Full Pygments source was used after the pre-existing pip-vendored copy proved
trimmed. The failed import attempts ran no tests and are not counted as passes.
Unused setup copies remain inside the permitted folder, below the size ceiling.

**This was source execution, not verified pip installation or package building.**
The normal installation route in README is the intended reproduction route on
machines with PyPI access. The source-only fallback is detailed in TEST_SETUP.md.
No compatibility claim is established for Python versions other than 3.15.2.

## Environment and authorization observations

The first PATH lookup missed Python and Git. Later read-only app/known-location
inspection found working existing Python 3.15.2 and Git 2.56.0.windows.3.
No Python runtime or model download was necessary.

The user approved local setup only within one repository folder, with a 250 MB
ceiling and no global installation. Home-directory creation was denied; the
permitted source copy is %TEMP%/Knowledge-Delta-. The measured footprint was
about 13 MB before the final small documentation update.

The first materialization added an extra newline to each file; this was a copy
artifact, not a snapshot algorithm failure. All 38 original files were reconciled
against their published Git blob hashes before the successful checks.

Terminal download attempts were blocked. Browser automation ended because it
could not reliably identify the URL for its policy checks; it was not bypassed.
Dependencies were instead explicitly staged from official GitHub source files.

Observed: Intel x64 processor identifier; environment reports 12 logical
processors; approximately 361 GB free disk at observation. RAM/GPU CIM access
was denied, so 16 GB RAM remains user-reported and GPU capability unknown.
The localhost Ollama inventory request was refused. No installed model digest
or live generation is verified.

## Earlier evidence

Initial repository state: 3026066735e6a6ed8379a5361ba1fbc98fc786a8.
First foundation implementation: 884e48301f10ba3cb447aa84635f318ae6c923bc.

Independent Node fixture checks preceded Python execution: seven documents per
snapshot, five changes, seven draft cases/categories and 13 exact applicable
evidence references. Those checks established fixture consistency only.

The actual Python sample reproduced snapshot IDs:
- before: 7262a50984bb805b83af313334fb88c8759a11755f88b4968af1ad2e52b54904
- after: b80b764e3d4b3a408740848d1780a91bd404f5c6310a5a20980d500d1ffd2231

Published-source references checked:
- https://pypi.org/project/pytest/
- https://ollama.com/library/qwen3:1.7b
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

A model listing is availability evidence, not an installation, memory or speed
measurement. Full RAG acceptance checks belong to later milestones.
