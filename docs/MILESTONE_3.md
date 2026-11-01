# Milestone 3 - fixture-based testing and evidence review

Status: first working fixture-based checkpoint independently reviewed and ready
for publication. Milestone 3 is not complete. The evaluator, SQLite
review store, fixture CLI and JSON/HTML export work locally; Streamlit is not yet
implemented or installed. No live inference or complete interface is claimed.

## Authorization and scope

The user explicitly authorized Milestone 3 using labeled fixtures while larger
Milestone 2 downloads remain deferred. Keep the 250 MB project-folder ceiling,
zero spending, no global installations and no model downloads. Per-push approval
is waived for authorized work, but publish only concrete verified checkpoints
with guarded non-force updates and preserve existing work.

Milestone 2 live acceptance remains incomplete: actual numeric/embedding imports,
Ollama inference, CPU timings, model selection and native containment still need
real local dependencies/assets. Fixture-based Milestone 3 does not satisfy those
checks or establish assistant accuracy.

## Staged implementation

1. Standard-library evaluator: independent snapshot judgments, justified citation/
   applicability checks, unresolved semantic judgments, and derived comparisons.
2. Manual-review records bound to the exact run/result, snapshot, trace, dataset,
   case and expectation revisions. Modified inputs invalidate old reviews.
3. Labeled fixture/replay workflow, JSON export and self-contained escaped HTML
   with both answers, expectations, evidence, checks, review status and errors.
4. Optional Streamlit adapter after dependency availability, compatibility and
   footprint are understood. No successful installation/UI launch is implied.

## Working fixture CLI

From the project root in PowerShell, using the existing isolated foundation Python:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --simulate-judgments --output-dir runs/fixture-demo
```

This actual CLI path has exported 80 scripted answers and 40 comparisons across
20 cases, two snapshots and two retrieval-configuration labels. All seven
comparison statuses are demonstrated with explicitly simulated judgments.
These are fixtures, not outputs from actual retrieval/model inference, measured
assistant accuracy, human reviews, or ML timings.

Omit `--simulate-judgments` to keep semantic judgments unresolved unless a justified
mechanical failure is observed. Inspect exported JSON and the self-contained HTML
in the selected output directory. Generated `runs/` outputs and review databases
are ignored, not published as raw personal review history.

A checked-in explicitly simulated sample is available as
[self-contained HTML](samples/mvp-fixture/report.html) and
[machine-readable JSON](samples/mvp-fixture/report.json). The actual command
that generated this reproducible sample was:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --simulate-judgments --output-dir docs/samples/mvp-fixture
```

The sample contains 80 scripted records, each with no model and no generation
performed, and zero human reviews. Its HTML is 789,217 bytes and JSON is 847,798
bytes. Source-bound CLI evidence is recorded in
`docs/evidence/milestone3-evaluation/fixture-cli.json`. This is a shareable tool
demonstration, not a model benchmark or screenshot of actual inference.

## Dataset and review integrity

`examples/mvp` contains 20 distinct constructed development cases, before/after
snapshots and case-bound expected-change annotations. All 20 cases are drafts:
**zero human case reviews** have occurred. Draft relation annotations are not
human approval that the substantive answer should change or remain equivalent.
These cases are separate from the ten hardware-only smoke questions.

Expected answers, rubrics and relation labels are evaluation inputs, not answering
model context. Gold labels must remain outside retrieval indexes and prompts.
Case families must remain in one split; do not manufacture a held-out benchmark
or pad the dataset with paraphrases.

The evaluator preserves raw answering traces. Successful structure/citation
checks alone leave semantic correctness unresolved; deterministic failures must
cite their mechanical basis. Semantic passes need an actual review, or an
explicit simulated fixture judgment that cannot be mixed into live metrics.

Human review records identify the reviewer, time, rationale and exact revision
bindings. Fixture/mechanical records must not invent a reviewer or review time.
Draft, simulated and reviewed expected-change relations remain distinct. A
changed string is not enough to establish a regression or expected change.

## Evidence and current limits

Initial evaluator evidence is in
[evidence/milestone3-evaluation](evidence/milestone3-evaluation/).
The latest actual source run executed 250 tests with zero failures/errors/skips
(6.24s), run `85050ab4133b40cd88df124c6c0f1287`. It includes actual built-in
SQLite temporary-database tests and evaluator/report/review-store checks.
Tested source identity is
`95a2905f74bf4e6b3280a1eddad71ebb87c32a7f4a084e53d267be553f66fe9b`.
Brain cleared publication after independently verifying all 115 source hashes,
the source-bound fixture CLI and sample provenance; no blocking findings remained.
No passing live integration, Streamlit
launch, human review or assistant benchmark is implied.

The project folder measured 17,963,006 bytes, below 250 MB. No package installation,
model download or global installation was needed for this checkpoint.

Retain missing judgments and run errors in reported counts. Fixture outputs and
deliberately faulty answers test the tool; they are not natural model failures.
No evaluator precision/recall against human labels is available yet.

## Streamlit candidate - metadata only

Checked on 2026-11-01: [PyPI](https://pypi.org/project/streamlit/) lists Streamlit
1.66.1 with Python >=3.11 and a 10.4 MB wheel. The
[official installation guide](https://docs.streamlit.io/get-started/installation/command-line)
lists support for Python 3.11 through 3.15. This identifies a candidate, not a
chosen pin, installed version, compatibility test or download authorization.

The complete transitive download/installed footprint and imports are unknown.
Do not infer that the entire environment fits 250 MB from the Streamlit wheel
size. No Streamlit package download or installation has occurred in this step.

## Next acceptance checks

- Publish the tested working fixture checkpoint requested by the user, preserving
  ignored output directories and previous milestone evidence.
- Keep real review work pending; stale/revision-bound records and fixture/live
  separation are tested contracts, not evidence that a human reviewed the cases.
- Next implement the optional Streamlit/manual-review interface unit only within
  the existing resource boundary; record
  unavailable dependencies and any unverified UI behavior explicitly.
- Record subsequent source/evidence and interface checks separately. Milestone 3
  completion remains pending; Streamlit is the next independent implementation unit.
