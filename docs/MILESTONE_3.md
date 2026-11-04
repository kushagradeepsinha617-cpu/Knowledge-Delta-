# Milestone 3 - fixture-based testing and evidence review

Status: first working fixture checkpoint published as
[`2c9e9d5`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/2c9e9d509046b3e8bc7accfb5995f9284e91ec2f),
with all 115 remote source hashes and both sample checksums reconciled.
The interface source checkpoint is published as
[`4c270e0`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/4c270e0cc7d5f80a0a4bb78a37146fe70015ca40),
with all 124 remote source hashes matched to its 266-test manifest. Milestone 3
is not complete; real UI acceptance remains blocked.
The evaluator, SQLite store, fixture CLI and JSON/HTML export work locally;
Streamlit remains uninstalled and no UI runtime or live inference is claimed.

The broader audit's saved-run gap is now fixed locally and independently reviewed:
the controller accepts existing experiment JSON with snapshot/dataset/origin
checks, preserved raw answers/evidence and repetition selection. Gold answers do
not regenerate imported responses. Separate assistant/tool metrics retain counts,
errors and missing judgments; tool precision/recall needs independently attested
reference labels. The 294-test/127-source proof below binds this checkpoint.

The [interface checkpoint guide](MILESTONE_3_INTERFACE.md) records the implemented
adapter/launcher/controller and exact review commands. Its frozen ordinary run
executed 266 tests with zero failures/errors/skips; Brain cleared the bounded
checkpoint and independently matched all 124 source hashes and scoped evidence.
Actual Streamlit readiness and AppTest were unavailable, so
rendering/runtime containment are not verified. No package/model installation
occurred; the network probe was unreachable. Human reviews remain zero.

## Authorization and scope

The user explicitly authorized Milestone 3 using labeled fixtures while larger
Milestone 2 downloads remain deferred. Keep the 250 MB project-folder ceiling,
zero spending, no global installations and no model downloads. On 2026-11-04,
the user retired Deliverer, briefly required milestone push approval, and then
explicitly granted all push permissions again. The primary agent handles tested
checkpoints directly with guarded non-force updates until that instruction changes.
This does not authorize model downloads or a larger footprint. Preserve existing work.

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

## Saved-run review and reporting - current integration unit

The local controller/CLI now accepts `--run` with an existing raw experiment JSON
inside the project. This selects imported-run mode instead of fixture replay.
Its manifests, dataset and expected-change annotations must match the original
run; do not point a seven-case run at the twenty-case MVP defaults. Importing
preserves original answers/evidence and does not call a model or reconstruct an
answer from an expectation. The full offline suite passed and Brain cleared the
bounded checkpoint for publication.

Example commands below assume `runs/recorded-run.json` already exists and was
produced from exactly the displayed MVP manifests/dataset. The path is an input
placeholder, not a newly generated or checked-in live run:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --run runs/recorded-run.json --before examples/mvp/before/manifest.json --after examples/mvp/after/manifest.json --dataset examples/mvp/cases.json --relations examples/mvp/relations.json --output-dir runs/imported-report
.venv/Scripts/python.exe -B scripts/review_fixture.py --run runs/recorded-run.json --before examples/mvp/before/manifest.json --after examples/mvp/after/manifest.json --dataset examples/mvp/cases.json --relations examples/mvp/relations.json --case-id request-timeout-change --configuration basic --slot after --repetition 2
```

The second command is valid only if that configuration/case/repetition exists in
the saved run. `--repetition` selects the exact answer to inspect/save; it does
not generate another answer. The report includes recorded repetitions rather
than silently merging them. `--run` cannot be combined with simulated correctness
judgments to relabel an imported result. Review saves still require the displayed
binding/revision and the actual person's own name/rationale.

The Streamlit adapter is being wired to the same input/repetition controls, but
actual rendering and interactions remain unverified while dependencies are absent.
Imported origin is validated and preserved; a supplied live label is not independent
proof that a model was actually run. Import itself performs no inference.

Assistant metrics and testing-tool metrics are separate contracts. Report counts,
eligible reviewed denominators, missing judgments and run errors explicitly;
fixture judgments are not live assistant correctness. Failure-flag precision/recall
requires independent, revision-bound reference labels and coverage disclosure.
Do not compare the evaluator's own judgments against themselves as ground truth,
exclude errors to inflate scores, or invent human labels. Final metric fields and
checks are recorded in the current source-bound evidence. Independent reference
labels represent a separately attested procedure, not authenticated identity,
another person or proof of blind review. Recorded origin/reviewer claims are not
independent proof of live execution or a reviewer's identity.

Final evidence in [evidence/milestone3-run-import-final](evidence/milestone3-run-import-final/):
294 executed tests with zero failures/errors/skips, run
`026df346a922443abf76d9bc9181c8a4`, 127-source ID
`55635b9d92192d36dcd4768c3e04085129237447399654898c690d717bee16c8`.
The actual saved-run CLI check imported/exported 80 fixture answer records and
40 comparisons while preserving the input file bytes, with zero human reviews.
It did not regenerate answers, run a model or turn fixture labels into accuracy:
assistant accuracy remains null. The measured folder contains 46,064,960 logical
bytes including ignored outputs, within 250 MB. Brain independently verified all
127 source hashes and the final CLI preservation/provenance checks;
Streamlit rendering and Milestone 2 live integration remain unverified.
The earlier `milestone3-run-import` evidence remains preserved as an intermediate
source observation rather than being overwritten by this corrected final run.

## Optional measurement inputs

The current local unit exposes existing measurement annotations through CLI and
UI source. The offline suite executed 313 tests with zero failures, errors or skips,
run `8d929a4f44d04dbd822b7a85115f1347`. Brain independently checked all 129 source
hashes against `90d3cd8df8d4ffe705faf951e8f73709eec78619ba2bbe65dc401578b5db6fc0`
and cleared the bounded implementation. Evidence is in
[measurement-input verification](evidence/milestone3-measurement-inputs/checks.json).
Actual CLI inspection/export with an empty reference list retained 80 fixture
records, zero human reviews and null scores; nonempty synthetic labels and saved
review actions are exercised only in temporary test projects. This local checkpoint
is published as [`bf3a8a1`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/bf3a8a1187d175477595fd64659418d3b849437d),
with all 129 tested source files reconciled and all 53 prior evidence/sample files
preserved. It creates no real human labels. Actual Streamlit rendering
remains unverified.

`--reference-labels runs/reference-labels.json` accepts an existing project-local
JSON list up to 16 MiB. Omit it to supply no independent labels. Unknown, duplicate
or stale result bindings are rejected. The file is a separate reference procedure,
not a copy of the tool's own flags or a substitute for answer-review records.

Each list item requires exactly these fields:

| Field | Required meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `binding` | Exact complete judgment binding from the evaluated result |
| `reference_outcome` | `failure` or `not_failure` |
| `basis` | `independent_human_reference` |
| `reviewer` | Actual reviewer's nonempty name/identifier |
| `reviewed_at` | Actual ISO8601 review timestamp with timezone |
| `rationale` | Actual assessment and its supporting reasoning |
| `independence_attested` | Boolean `true`, explicitly attesting a separate assessment procedure |

The complete binding includes `result_key`, dataset/case/expectation hashes,
snapshot ID and trace hash. Copy it from the exact evaluated record; the short
inspection binding hash is not the complete binding object. Changing the run,
trace, case, expectations or snapshot invalidates an old label.

Independence refers to the assessment procedure. The same person may conduct
both reviews; this is not authentication of reviewer identity, proof of blinding,
or evidence that an independent reviewer participated. Never manufacture names,
times, rationale or attestations to obtain a score. Fixtures stay ineligible for
live assistant/tool metrics even when synthetic tests exercise the annotation path.

Example export, assuming both matching input files already exist:

```powershell
.venv/Scripts/python.exe -B scripts/fixture_demo.py --run runs/recorded-run.json --reference-labels runs/reference-labels.json --output-dir runs/reference-report
```

For an actual abstention, the answer-review CLI additionally accepts
`--abstention-judgment appropriate` only with `--outcome pass`, or
`--abstention-judgment unnecessary` only with `--outcome fail`. The usual explicit
save, reviewer, rationale and inspected binding/revision are required. Omit the
option to leave abstention unassessed; do not infer it from keywords.

JSON and escaped HTML preserve supplied reference labels for inspection. CLI
and UI inputs do not authenticate those claims or turn fixture reviews into live
benchmarks. Current temporary test records are labeled TEST-ONLY; no real human
reference labels or answer reviews were created for delivery.

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

The next unit checks actual package availability, cache/profile/temp containment
and full footprint before any installation attempt within the existing 250 MB
allowance. Network restrictions may block that route. Published fixture reports
and their 250-test source evidence remain historical records; new interface
verification must be recorded separately, including any unavailable runtime.

## Next acceptance checks

On resumption (2026-11-03), remote `main` still points to the published `2c9e9d5`
checkpoint. Newer local `review_workflow.py` and
`docs/evidence/milestone3-interface` were preserved. The last recorded local
controller run executed 257 tests with zero failures/errors/skips, run
`5eb31a98ccba42b2a50445328ae51e9e`, source
`82790bd4f6630820d8c90d5ac37fe2535b62df8618ce787f1321c908a1f32ef0`.
This is historical controller evidence, not a new test run on resumption and not
proof of a functioning Streamlit app. The later reviewed 266-test checkpoint is
now published; its complete 124-source remote reconciliation supersedes that run.

- Preserve the published fixture checkpoint, ignored output directories and
  previous milestone evidence while building the next independent unit.
- Keep real review work pending; stale/revision-bound records and fixture/live
  separation are tested contracts, not evidence that a human reviewed the cases.
- Actual Streamlit imports/rendering and launcher containment require compatible
  dependencies and a usable setup/network route; these remain blocked. Record
  unavailable checks rather than claiming UI success.
- One read-only PyPI HEAD check was requested in the user's normal terminal to
  identify an available route. No answer has arrived; user connectivity remains
  unknown. No install, model operation or resource expansion was requested.
- Publish the independently reviewed saved-run review/report and metrics checkpoint,
  then reconcile remote hashes. Do not advance to Milestone 4.
- Preserve the published historical sample and evidence. Last measured folder size
  is 46,064,960 logical bytes, within 250 MB; no packages/models were installed.

Non-model UI dependencies are permitted as routine project-local setup only after
compatibility and full-footprint checks within 250 MB; none have been installed.
The user forbids model downloads, excess storage and global installation, rather
than every possible UI dependency installation. Observed network failures remain
an execution limit, and no claim of user-terminal connectivity is made.
