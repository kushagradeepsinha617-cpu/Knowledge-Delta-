# Milestone 1 acceptance audit

This audit covers the working foundation, not the full five-milestone product.

| Requirement | Evidence | Outcome |
|---|---|---|
| Project scope and plan | PROJECT_SPEC.md and PLAN.md | Written and current |
| Isolated project environment | environment.json: isolated_environment true; real .venv interpreter | Verified source-run setup |
| Dependency readiness and actual versions | environment.json and dependency-sources.json; actual pytest execution | Tested combination recorded |
| Model readiness | Explicit localhost inventory request refused; no download/inference | Unavailable, explicitly reported |
| Hardware information where accessible | Existing Python/Git, processor identifier, logical count and disk observations; RAM/GPU unknown | Observations separated from assumptions |
| Stable document identity and isolated snapshots | Real pytest identity, immutability, content/metadata/default tests | Passed |
| Snapshot/case schemas | Strict input, evidence, version/default, binding, review/split tests | Passed |
| Constructed snapshots | Real loader and exact expected diff; same reproducible IDs | Passed |
| Content edits, metadata edits, additions/removals | Actual compare output and pytest assertions | Passed |
| Runnable change command | cli.json: compare returns 0 and exact expected JSON | Passed |
| Meaningful ordinary offline tests | pytest.xml: 52 tests; zero errors/failures/skips | Passed |
| Actionable invalid inputs | UTF-8/path/read/domain regressions and real CLI exit 2 | Passed |
| Reproducible evidence | Source hashes stable through run; real commands/output/JUnit/environment saved | Passed for recorded configuration |
| Windows run/test instructions | README.md and TEST_SETUP.md | Direct source commands executed; ordinary pip install remains unverified |
| Preserve work and constraints | Original test.txt retained; single-folder setup, no global installs/models; per-push approval | Respected |
| Stop before Milestone 2 | PLAN.md | No retrieval/inference/UI implementation |

The declared Python floor is not an executed compatibility matrix. The actual
test interpreter was 3.15.2. Normal pip installation and a project wheel build
remain unverified; neither is needed for the executed direct-source workflow.

Seven constructed case labels remain drafts. Twenty development cases,
human semantic review, live answering, model smoke tests, evaluation metrics,
HTML reports and Streamlit are later work.

Interview concept: the stable document ID answers “which document is this?”;
its content/metadata hashes answer “what changed?”; the snapshot hash binds the
dataset to exactly the evidence evaluated.
