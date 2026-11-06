# Human review coverage and reproduction

The implementation runs locally and the operational experiments are recorded.
Four main-study answer judgments are recorded. This page distinguishes those
actual judgments from remaining optional reviews; no unreviewed answer is marked
correct automatically. Broader review would enlarge the evidence, not establish
a representative result retroactively.

## Case definitions

All ten Pydantic 2.10.6 development case definitions have now been explicitly
reviewed in chat, including validator-error, regex and settings on 2026-11-06.
The questions, both expectations, source passages and rubrics are recorded in
`examples/pydantic/cases.json`. Both snapshots retain the requested 2.10.6
version; adding v1 material does not change the question's meaning.

The separate case in `examples/pydantic-revision/cases.json` and its expected relation were explicitly approved on 2026-11-06.
That review covered both selected Generic models sections and the proposed
earlier evidence-only abstention. The actual warning addition is verified;
released-software applicability remains unknown.
Do not convert nominal mainline version metadata into a verified release claim.

## Actual answer review

The main 256-token run contains 40 actual answers: 28 records from the seven
reviewed cases and 12 from the three drafts. Four dict-pairs answers have now received actual human judgments; the other 36
lack resolved human judgments.
Two have automatic citation-version failure flags; these are not independently
reviewed correctness labels. The older genuine diagnostic remains bound to its
draft dataset. Four newly generated records use the approved genuine case;
their actual answer review is pending.

For each reviewed answer, inspect the requested context, exact supplied evidence,
answer, citations, expected behavior and rubric. Record pass, fail or unresolved
with a rationale; distinguish unsupported facts, wrong-version answers and
appropriate/unnecessary abstention where justified. Do not approve a result
merely because it contains a keyword or valid JSON.

Use the local web interface's saved-run import/manual review workflow, or inspect
the hash-bound CLI review form. The following command performs inspection only:

```powershell
& .\.venv\Scripts\python.exe -B scripts/review_fixture.py --run runs/pydantic-live-main-256.json --before examples/pydantic/before/manifest.json --after examples/pydantic/after/manifest.json --dataset docs/evidence/milestone4-output-cap-256/cases-at-run.json --relations docs/evidence/milestone4-output-cap-256/relations-at-run.json --case-id pydantic-equality --configuration basic --slot after
```

The frozen cases/relations preserve the labels that existed when the run was
made. New case approvals change dataset identity; do not rewrite old runs or
silently grade them against a different dataset revision. Keep the recorded
review binding and revision when explicitly saving an actual human decision.

## Reproduce the four recorded judgments offline

From the repository root, this verifies the published raw-run hash and recreates
the counts and metrics from the actual human labels. It reads the lossless ZIP
directly and requires neither the private SQLite journal nor a running model:

```powershell
@'
import json
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from knowledge_delta.validation import read_json
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.evaluation import evaluate_run
from knowledge_delta.metrics import summarize_metrics
root = Path.cwd()
record = read_json(root / 'docs/evidence/milestone4-human-answer-review/human-review-records.json')
with ZipFile(root / 'docs/evidence/milestone4-human-answer-review/human-reviewed-subset-report.zip') as archive:
    raw = archive.read('raw-run.json')
assert sha256(raw).hexdigest() == record['source_run_sha256']
snapshots = {s: load_snapshot(root / 'examples/pydantic' / s / 'manifest.json') for s in ('before', 'after')}
evaluation = evaluate_run(json.loads(raw), read_json(root / 'docs/evidence/milestone4-output-cap-256/cases-at-run.json'), record['relation_annotations'], record['review_records'], snapshots=snapshots, allow_fixture=False)
assert evaluation['counts'] == record['counts']
assert summarize_metrics(evaluation) == record['metrics']
print(evaluation['counts'])
'@ | & .\.venv\Scripts\python.exe -B -
```

These are four assisted, unblinded judgments from one family chosen after seeing
outputs. They establish those outcomes, not representative benchmark accuracy.

## Report reviewed findings

Reviewing all 40main answers is preferable. If reviewing a subset, declare the
selection rule, selection timing, scope and denominator; do not present that
subset as representative or held-out. No held-out families were invented or
silently moved out of development.

Failure-flag precision/recall requires separately attested reference annotations.
The same person may supply them under the documented separate procedure, with
exposure to existing flags disclosed. Otherwise leave those metrics unavailable.

After actual judgments exist, regenerate reports and document measured
correctness, abstention, errors, unresolved cases and limitations. The current
60-reviewed-case goal remains a target, not a claim that 60 reviews happened.
