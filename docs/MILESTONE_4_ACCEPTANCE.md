# Milestone 4 acceptance audit

This audit maps the original Milestone 4 deliverables to recorded evidence.
Final completion also requires publication and remote hash reconciliation.
The original milestone does not require semantic judgments for every case or
provenance group: the main four-answer subset provides actual human evaluation;
the genuine reviewed-case run remains explicitly ungraded unless its optional
answer review is supplied. No expected-change success is inferred from its text.
The larger 60-reviewed-case target and held-out validation are not claimed.

| Requirement | Authoritative evidence | Current state |
| --- | --- | --- |
| Real local embeddings and answering | Actual MiniLM ONNX/retrieval evidence; ten-query Qwen CPU smoke; immutable model digest | Verified on the recorded Windows setup |
| Genuine licensed/versioned sources | Pydantic source pins/licenses; actual parent-child generic warning addition; offline source verifier | Verified; release applicability of mainline revision remains unknown |
| Human-reviewed cases | Main REVIEW_LOG and current ten approved definitions; separate genuine-case/relation approval | Eleven case definitions reviewed; prior run labels remain frozen |
| Development/test split discipline | Dataset validator/family split tests; all study families marked development | Implemented; no actual held-out evaluation |
| Support60-case target without invented reviews | In-memory capacity test runs 20 development/40 held-out placeholders through 240 records and HTML/JSON export | Workflow capacity verified; synthetic plumbing fixture is not a benchmark dataset |
| Separate snapshot indexes and source isolation | Actual NumPy retrieval check; snapshot/index IDs in every trace | Verified for the selected corpora |
| Basic versus version-filtered retrieval | Same recorded model/settings;256-token run has2/20versus0/20citation-version flags | Mechanical citation compatibility only; not semantic effectiveness |
| Controlled experiment and raw records | Cap comparison validates exact prompts/schema/passages/model/request settings across 40 rows | Verified cap-only recorded-input change; original runs preserved |
| Variability checks without answer caching | Predeclared three-case/three-repeat 36-record run; explicit 30 errors/6 structured answers | Completed with output-limit caveat; not general determinism evidence |
| Additional variability/causality caution | Post-hoc identical-request No/Yes observation | Document change is not proven the sole cause of semantic regression |
| Actual semantic judgments and comparison | Four exact user-approved dict-pairs judgments and should_remain relation | Main diagnostic subset reviewed; genuine reviewed-case answers explicitly ungraded |
| Judge each snapshot independently | Human-bound pass/fail records yield basic regression and filtered recovery | Verified for the selected four records |
| Counts, errors, missing judgments | Original40/36runs, separate256run and report metrics | All planned rows retained; unreviewed answers never counted correct |
| Distinguish constructed/genuine/draft/live | Separate case directories, protocols, run IDs and report archives | Preserved; fixture outputs never substitute for live inference |
| Assistant and testing-tool metrics separate | Report accounting and source metrics; no independent reference labels | Correctness limited to reviewed subset; precision/recall unavailable |
| Reproducible review evidence | Exact review bindings plus public raw run/cases/relations; evaluation reproduced without SQLite journal | Verified for main subset |
| Self-contained exports | Lossless byte-checked HTML/JSON/raw archives; static resource audit | Generated; no browser visual-layout audit claimed |
| Offline ordinary tests | Latest 519-test source verification with explicit JUnit counts | Passed, zero failures/errors/skips |
| Local/resource constraints | Project-local assets/state, localhost-only calls, zero purchases; resource observation | Windows protection unchanged; OS peak RAM and physical peak storage unmeasured |

The capacity fixture is deliberately labeled TEST ONLY and stays in test code.
It does not pad the real corpus with 60 questions or invent human/held-out labels.
The actual study is exploratory development work; selection of the reviewed
four-answer family occurred after inspecting outputs and was assisted/unblinded.
It supports those recorded outcomes, not a representative accuracy estimate.

The main run's frozen dataset contains seven reviewed cases/three drafts even
though the current dataset now has ten approvals. The original genuine four-row
diagnostic remains bound to its draft dataset. The newer genuine run was frozen
after case approval; its actual answers remain ungraded unless separate human decisions are supplied.

Milestone 5portfolio packaging, a broader reviewed dataset, independent reference
labels and held-out validation remain future work and must not be implied by
completion of the small Milestone 4 evaluation workflow.
