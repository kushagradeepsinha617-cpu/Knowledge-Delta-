"""Persist the source-aware AI review of four actually inspected revision answers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from knowledge_delta.evaluation import result_key
from knowledge_delta.validation import digest, read_json

path = ROOT / "runs/milestone5-study/bundle-2.json"
raw = path.read_bytes()
run = json.loads(raw)
case = read_json(ROOT / "examples/pydantic-revision/cases.json")["cases"][0]
expected = {
    "before": "Yes, Pydantic checks that the type satisfies the upper bound when parametrizing a generic model with a concrete type.",
    "after": "No, Pydantic does not check that the provided type satisfies the type variable's upper bound when parametrizing a model with a concrete type."
}
records = []
for trace in run["results"]:
    slot = trace["snapshot_slot"]
    if trace["status"] != "answered_pending_review" or trace["answer"]["answer"] != expected[slot]:
        raise RuntimeError("Actual inspected answer changed; do not silently transfer this assessment")
    before = slot == "before"
    rationale = (
        "The confident Yes fails the reviewed evidence-only expectation to abstain. Both supplied chunks concern unparametrized type variables and instance-data validation; neither establishes checking a concrete type argument at parametrization. The answer conflates those contracts. A citation exists but does not substantiate the claim. The earlier documentation's silence does not show the underlying software behavior was different."
        if before else
        "The No answer matches the reviewed expectation and the supplied warning explicitly stating that a concrete provided type is not validated for assignability to an upper bound. The cited chunk contains that warning. It distinguishes the asked parametrization check without asserting that instance-data validation never occurs. Release applicability remains unspecified; no software-release claim is inferred.")
    records.append({"result_key": result_key(run, trace), "snapshot_id": trace["snapshot_id"],
        "trace_hash": digest(trace), "expectation_hash": digest(case["expectations"][slot]),
        "proposed_outcome": "fail" if before else "pass", "failure_kind": "unsupported_answer" if before else None,
        "rationale": rationale, "cited_chunk_ids": trace["answer"]["citations"],
        "assessor": "Codex AI-assisted", "human_review": False, "independent_reference": False, "provisional": True})
report = {"schema_version": 1, "kind": "provisional_agent_assessment", "run_id": run["run_id"],
    "raw_run_path": path.relative_to(ROOT).as_posix(), "raw_run_sha256": sha256(raw).hexdigest(),
    "dataset_hash": run["dataset_hash"], "assessed_at": datetime.now(timezone.utc).isoformat(),
    "assessor": "Codex AI-assisted", "human_review": False, "independent_reference": False, "provisional": True,
    "scope_note": "Four actual answers and all supplied passages inspected. Proposals are not human judgments or independent benchmark truth. Both configurations exhibit the same before/after pattern; no filtering improvement or software behavior change is established.",
    "summary": {"assessed_records": 4, "proposed_outcomes": {"pass": 2, "fail": 2}, "human_answer_judgments_created": 0},
    "records": records}
output = ROOT / "docs/evidence/milestone5-analysis/genuine-revision-assessments.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
print(json.dumps(report["summary"]))
