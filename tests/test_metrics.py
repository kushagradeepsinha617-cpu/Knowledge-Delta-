"""Synthetic bookkeeping tests, not live measurements or real human annotations.

Every live/human/reference label constructed below is TEST-ONLY data for checking
metric arithmetic and eligibility. No such reference file is published as evidence.
"""
from copy import deepcopy
from pathlib import Path

import pytest

from knowledge_delta.metrics import summarize_metrics
from knowledge_delta.evaluation import evaluate_run
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, digest, read_json
from knowledge_delta.workflow import fixture_report

ROOT = Path(__file__).resolve().parents[1]


def synthetic_evaluation(specs):
    """Two records per synthetic case; this bypasses inference intentionally."""
    assert len(specs) % 2 == 0
    template = read_json(ROOT / "examples/mvp/cases.json")["cases"][0]
    run_id, dataset_hash = "TEST-ONLY-SYNTHETIC-RUN", digest({"test-only": True})
    rows = []
    for index in range(len(specs) // 2):
        case = deepcopy(template)
        case.update(case_id=f"TEST-ONLY-{index}", family_id=f"TEST-ONLY-{index}")
        case["review"] = {"status": "human_reviewed", "reviewer": "TEST-ONLY-CASE-REVIEWER",
                          "scope": "Synthetic test labels; no real case review occurred."}
        details = {}
        for offset, slot in enumerate(("before", "after")):
            spec = specs[index * 2 + offset]
            if spec.get("draft"):
                case["review"] = {"status": "draft", "reviewer": None, "scope": None}
        for offset, slot in enumerate(("before", "after")):
            spec = specs[index * 2 + offset]
            outcome = spec.get("outcome", "pass")
            trace = {"snapshot_id": "TEST-ONLY-" + slot,
                "status": "run_error" if outcome == "run_error" else "answered_pending_review",
                "origin": spec.get("origin", "live"),
                "answer": None if outcome == "run_error" else {"answer": "TEST-ONLY synthetic answer",
                    "citations": [], "abstained": spec.get("abstained", False)}}
            if "latency" in spec:
                trace["elapsed_seconds"] = spec["latency"]
            if spec.get("missing"):
                trace["synthetic_missing_record"] = True
            key = {"run_id": run_id, "case_id": case["case_id"], "configuration_name": "TEST-ONLY-CONFIG",
                   "repetition": 1, "snapshot_slot": slot}
            bound = {"result_key": key, "dataset_hash": dataset_hash, "case_hash": digest(case),
                "expectation_hash": digest(case["expectations"][slot]), "snapshot_id": trace["snapshot_id"],
                "trace_hash": digest(trace)}
            human = spec.get("human", outcome in ("pass", "fail"))
            review = None
            if human:
                review = {"binding": deepcopy(bound), "basis": "human_review", "outcome": outcome,
                    "reviewer": "TEST-ONLY-REVIEWER", "reviewed_at": "2026-01-01T00:00:00+00:00",
                    "rationale": "Injected synthetic bookkeeping test, not an actual review.",
                    "failure_kind": spec.get("failure_kind"), "abstention_judgment": spec.get("abstention")}
            checks = [{"check_id": "TEST-ONLY-CHECK", "status": "fail" if spec.get("flag") else "pass"}]
            judgment = {"binding": bound, "outcome": outcome,
                "basis": "human_review" if human else "run_error" if outcome == "run_error" else "unresolved",
                "checks": checks, "review": review}
            details[slot] = {"trace": trace, "judgment": judgment, "expectation": deepcopy(case["expectations"][slot])}
        rows.append({"case_id": case["case_id"], "configuration_name": "TEST-ONLY-CONFIG", "repetition": 1,
                     "case": case, "snapshots": details})
    missing = sum(s.get("missing", False) for s in specs)
    return {"kind": "knowledge_delta_evaluation", "run_id": run_id, "dataset_hash": dataset_hash,
        "counts": {"planned_answer_records": len(specs), "recorded_answer_records": len(specs) - missing,
                   "missing_answer_records": missing}, "rows": rows}


def references(evaluation, outcomes):
    labels = []
    records = [detail for row in evaluation["rows"] for detail in row["snapshots"].values()]
    for detail, outcome in zip(records, outcomes):
        labels.append({"schema_version": 1, "binding": deepcopy(detail["judgment"]["binding"]),
            "reference_outcome": outcome, "basis": "independent_human_reference",
            "reviewer": "TEST-ONLY-REVIEWER", "reviewed_at": "2026-01-02T00:00:00+00:00",
            "rationale": "TEST-ONLY separate reference procedure; no actual independent audit occurred.",
            "independence_attested": True})
    return labels


def test_actual_fixture_never_becomes_a_model_benchmark_even_with_simulated_passes():
    p = ROOT / "examples/mvp"
    evaluation = fixture_report(p / "before/manifest.json", p / "after/manifest.json",
        p / "cases.json", p / "relations.json", simulate_judgments=True)
    metrics = summarize_metrics(evaluation)
    assert metrics["accounting"]["planned_answer_records"] == 80
    assert metrics["accounting"]["run_errors"] == 2
    assert metrics["accounting"]["simulated_judgments"] > 0
    assert metrics["partitions"]["origin"] == {"fixture": 80}
    assert metrics["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None
    assert metrics["assistant"]["confirmed_correct_per_planned_reviewed_case_answer"]["value"] is None
    assert metrics["testing_tool"]["precision"]["value"] is None
    assert metrics["testing_tool"]["recall"]["value"] is None


def test_errors_missing_and_unresolved_remain_in_conservative_denominator():
    evaluation = synthetic_evaluation([{}, {"outcome": "run_error", "missing": True, "origin": "unverified"},
        {"outcome": "needs_human_review", "human": False}, {"outcome": "fail", "failure_kind": "wrong_version"}])
    before = deepcopy(evaluation)
    result = summarize_metrics(evaluation)
    assistant = result["assistant"]
    assert assistant["accuracy_resolved_human_judgments_only"] == {"numerator": 1, "denominator": 2, "value": .5}
    assert assistant["confirmed_correct_per_planned_reviewed_case_answer"] == {"numerator": 1, "denominator": 4, "value": .25}
    assert assistant["review_coverage"]["value"] == .5
    assert assistant["reviewed_case_run_errors"] == assistant["reviewed_case_missing_records"] == 1
    assert result["accounting"]["recorded_answer_records"] == 3
    assert evaluation == before


def test_real_evaluator_index_error_without_snapshot_id_and_missing_records_are_retained():
    directory = ROOT / "examples/mvp"
    dataset = read_json(directory / "cases.json")
    snapshots = {slot: load_snapshot(directory / slot / "manifest.json") for slot in ("before", "after")}
    run = {"run_id": "TEST-ONLY-INDEX-ERROR", "origin": "unverified", "dataset_hash": digest(dataset),
        "snapshots": dataset["snapshot_ids"], "snapshot_defaults": {slot: s.default_version for slot, s in snapshots.items()},
        "repeats": 1, "configurations": {"basic": {"version_filter": False}},
        "results": [{"case_id": dataset["cases"][0]["case_id"], "snapshot_slot": "before", "configuration_name": "basic",
            "repetition": 1, "status": "run_error", "error_phase": "index", "error": "Injected TEST-ONLY index failure",
            "origin": "unverified"}]}
    evaluation = evaluate_run(run, dataset, read_json(directory / "relations.json"), snapshots=snapshots)
    result = summarize_metrics(evaluation)
    assert result["accounting"]["planned_answer_records"] == result["accounting"]["run_errors"] == 40
    assert result["accounting"]["recorded_answer_records"] == 1
    assert result["accounting"]["missing_answer_records"] == 39
    assert result["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None


def test_draft_cases_cannot_supply_correctness_ground_truth():
    result = summarize_metrics(synthetic_evaluation([{"draft": True}, {"draft": True}]))
    assert result["partitions"]["case_review_status"] == {"draft": 2}
    assert result["assistant"]["resolved_eligible_human_judgments"] == 0
    assert result["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None


def test_independent_reference_can_disagree_with_flag_and_same_person_is_allowed():
    evaluation = synthetic_evaluation([{"outcome": "fail", "flag": True}, {"outcome": "fail", "flag": True},
                                      {"outcome": "fail"}, {}])
    labels = references(evaluation, ["failure", "not_failure", "failure", "not_failure"])
    result = summarize_metrics(evaluation, labels)["testing_tool"]
    assert result["confusion"] == {"true_positive": 1, "false_positive": 1, "false_negative": 1, "true_negative": 1}
    assert result["precision"] == {"numerator": 1, "denominator": 2, "value": .5}
    assert result["recall"]["value"] == .5
    assert result["reference_coverage"]["value"] == 1


def test_answer_review_and_unattested_reference_cannot_be_recycled_as_tool_truth():
    evaluation = synthetic_evaluation([{}, {}])
    review = evaluation["rows"][0]["snapshots"]["before"]["judgment"]["review"]
    with pytest.raises(ValidationError):
        summarize_metrics(evaluation, [review])
    label = references(evaluation, ["failure"])[0]
    label["independence_attested"] = False
    with pytest.raises(ValidationError, match="separate independently"):
        summarize_metrics(evaluation, [label])


@pytest.mark.parametrize("fault", ["stale_trace", "wrong_run", "duplicate", "unknown_result"])
def test_stale_cross_run_unknown_and_duplicate_references_are_rejected(fault):
    evaluation = synthetic_evaluation([{}, {}])
    labels = references(evaluation, ["failure"])
    if fault == "stale_trace":
        labels[0]["binding"]["trace_hash"] = "changed"
    elif fault == "wrong_run":
        labels[0]["binding"]["result_key"]["run_id"] = "other-run"
    elif fault == "unknown_result":
        labels[0]["binding"]["result_key"]["case_id"] = "unknown-case"
    else:
        labels.append(deepcopy(labels[0]))
    with pytest.raises(ValidationError):
        summarize_metrics(evaluation, labels)


def test_fixture_draft_and_error_references_are_counted_as_ineligible_not_as_model_scores():
    fixture = synthetic_evaluation([{"origin": "fixture"}, {"origin": "fixture"}])
    result = summarize_metrics(fixture, references(fixture, ["failure", "not_failure"]))
    assert result["testing_tool"]["ineligible_reference_labels"] == 2
    assert result["testing_tool"]["precision"]["value"] is None
    error = synthetic_evaluation([{"outcome": "run_error"}, {"outcome": "run_error"}])
    result = summarize_metrics(error, references(error, ["failure", "not_failure"]))
    assert result["testing_tool"]["eligible_reference_labels"] == 0
    assert result["accounting"]["run_errors"] == 2


def test_abstention_requires_explicit_classification_and_latency_missing_is_visible():
    result = summarize_metrics(synthetic_evaluation([
        {"abstained": True, "abstention": "appropriate", "latency": 2},
        {"abstained": True, "outcome": "fail", "failure_kind": "unnecessary_abstention", "abstention": "unnecessary", "latency": 4},
        {"abstained": True}, {"outcome": "fail", "failure_kind": "unsupported_answer"}]))
    assistant = result["assistant"]
    assert assistant["abstention"]["records_in_reviewed_cases"] == 3
    assert assistant["abstention"]["unassessed_records"] == 1
    assert assistant["abstention"]["appropriate_among_assessed"]["value"] == .5
    assert assistant["primary_unsupported_answer_failure_labels"]["numerator"] == 1
    assert assistant["answer_pipeline_latency_seconds"]["mean"] == 3
    assert assistant["answer_pipeline_latency_seconds"]["missing_records"] == 2


@pytest.mark.parametrize("fault", ["denominator", "duplicate_result", "stale_answer", "mixed_origins"])
def test_corrupt_evaluation_cannot_silently_change_denominators_or_provenance(fault):
    evaluation = synthetic_evaluation([{}, {}])
    if fault == "denominator":
        evaluation["counts"]["planned_answer_records"] += 1
    elif fault == "duplicate_result":
        evaluation["rows"].append(deepcopy(evaluation["rows"][0]))
    elif fault == "stale_answer":
        evaluation["rows"][0]["snapshots"]["before"]["trace"]["answer"]["answer"] = "changed"
    else:
        detail = evaluation["rows"][0]["snapshots"]["before"]
        detail["trace"]["origin"] = "fixture"
        detail["judgment"]["binding"]["trace_hash"] = digest(detail["trace"])
        detail["judgment"]["review"]["binding"] = deepcopy(detail["judgment"]["binding"])
    with pytest.raises(ValidationError):
        summarize_metrics(evaluation)
