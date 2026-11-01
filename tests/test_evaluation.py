"""Injected traces/review records exercise the evaluator; no real human reviews exist here."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
from types import SimpleNamespace

import pytest

from knowledge_delta.cases import validate_dataset
from knowledge_delta.evaluation import (binding, compare_judgments, evaluate_run, judge_snapshot,
                                        make_review, validate_relation, validate_relations, validate_review)
from knowledge_delta.questions import QuestionInput
from knowledge_delta.prompts import build_prompt
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, digest, read_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def example():
    directory = ROOT / "examples/mvp"
    dataset = read_json(directory / "cases.json")
    snapshots = {slot: load_snapshot(directory / slot / "manifest.json") for slot in ("before", "after")}
    case = dataset["cases"][0]
    run = {"run_id": "test-only-run", "origin": "fixture", "dataset_hash": digest(dataset),
           "snapshots": dataset["snapshot_ids"], "snapshot_defaults": {slot: value.default_version for slot, value in snapshots.items()},
           "repeats": 1, "configurations": {"basic": {"version_filter": False}}, "results": []}
    traces = {}
    for slot, snapshot in snapshots.items():
        doc = snapshot.document(case["expectations"][slot]["evidence"][0]["document_id"])
        identity = "test-only-chunk-" + slot
        passage = {"chunk_id": identity, "snapshot_id": snapshot.snapshot_id,
                "document_id": doc.document_id, "software_versions": list(doc.software_versions), "text": doc.content,
                "source_reference": doc.source_reference, "source_revision": doc.source_revision}
        traces[slot] = {"case_id": case["case_id"], "configuration_name": "basic", "repetition": 1,
            "snapshot_slot": slot, "snapshot_id": snapshot.snapshot_id, "origin": "fixture",
            "question": asdict(QuestionInput.from_case(case, slot)), "effective_version": "1",
            "status": "answered_pending_review", "answer": {"answer": case["expectations"][slot]["answer"],
                "citations": [identity], "abstained": False},
            "retrieved_passages": [passage], "generation": None, "generation_attempted": False,
            "generation_performed": False, "prompt_origin": "fixture_simulated",
            "prompt": build_prompt(QuestionInput.from_case(case, slot), snapshot, (SimpleNamespace(**passage),))}
    run["results"] = list(traces.values())
    return run, dataset, case, traces


def sim_review(example, slot, outcome="pass", kind=None):
    run, dataset, case, traces = example
    return make_review(run, traces[slot], dataset, case, outcome, basis="fixture",
                       rationale="Explicit simulated unit-test judgment, not a human review.", failure_kind=kind)


def relation(example, value="should_change", basis="fixture"):
    case = example[2]
    return {"schema_version": 1, "case_id": case["case_id"], "case_hash": digest(case),
            "relation": value, "basis": basis, "reviewer": None, "reviewed_at": None,
            "rationale": "Draft/simulated unit-test relation only."}


def test_twenty_distinct_draft_cases_and_bound_relations_validate():
    directory = ROOT / "examples/mvp"
    dataset = read_json(directory / "cases.json")
    summary = validate_dataset(dataset, load_snapshot(directory / "before/manifest.json"), load_snapshot(directory / "after/manifest.json"))
    assert summary["case_count"] == summary["draft"] == 20 and summary["human_reviewed"] == 0
    annotations = validate_relations(read_json(directory / "relations.json"), dataset)
    assert len(annotations) == 20 and all(item["basis"] == "draft" for item in annotations.values())


def test_valid_citations_and_keyword_presence_never_prove_semantic_correctness(example):
    run, dataset, case, traces = example
    traces["before"]["answer"]["answer"] = "It is NOT 10 seconds; it is a million seconds."
    value = judge_snapshot(run, traces["before"], dataset, case)
    assert all(check["status"] == "pass" for check in value["checks"])
    assert value["outcome"] == "needs_human_review"


@pytest.mark.parametrize("before,after,relation_basis,kind,expected,recovered", [
    ("pass", "pass", "draft", None, "pass", False),
    ("pass", "pass", "fixture", None, "expected_answer_change", False),
    ("pass", "fail", "fixture", "retained_previous_behavior", "failure_to_adopt_expected_change", False),
    ("pass", "fail", "fixture", "incorrect_answer", "previously_correct_now_incorrect", False),
    ("pass", "fail", "draft", "retained_previous_behavior", "previously_correct_now_incorrect", False),
    ("fail", "fail", "fixture", "incorrect_answer", "incorrect_in_both_snapshots", False),
    ("fail", "pass", "fixture", None, "pass", True),
    ("pass", "needs_human_review", "fixture", None, "needs_human_review", False),
])
def test_status_derivation_uses_independent_judgments_and_explicit_relation(example, before, after, relation_basis, kind, expected, recovered):
    run, dataset, case, traces = example
    a = judge_snapshot(run, traces["before"], dataset, case, sim_review(example, "before", before,
        "incorrect_answer" if before == "fail" else None), allow_fixture=True)
    b = judge_snapshot(run, traces["after"], dataset, case, sim_review(example, "after", after, kind), allow_fixture=True)
    comparison = compare_judgments(a, b, relation(example, basis=relation_basis), allow_fixture=True)
    assert comparison["status"] == expected and comparison["recovered"] is recovered
    assert comparison["simulated"] is True


def test_run_error_dominates_and_is_not_a_new_semantic_regression(example):
    run, dataset, case, traces = example
    traces["after"].update(status="run_error", answer=None, error="Injected test-only service failure")
    a = judge_snapshot(run, traces["before"], dataset, case)
    b = judge_snapshot(run, traces["after"], dataset, case)
    assert compare_judgments(a, b, relation(example), allow_fixture=True)["status"] == "run_error"


@pytest.mark.parametrize("change", ["answer", "rubric", "run", "slot"])
def test_changed_answers_rubrics_and_run_identity_invalidate_reviews(example, change):
    run, dataset, case, traces = example
    review = sim_review(example, "before")
    if change == "answer":
        traces["before"]["answer"]["answer"] = "Changed after review"
    elif change == "rubric":
        case["expectations"]["before"]["rubric"] += " Additional requirement."
        run["dataset_hash"] = digest(dataset)
    elif change == "run":
        run["run_id"] = "another-run"
    else:
        traces["before"]["snapshot_slot"] = "after"
    with pytest.raises(ValidationError):
        validate_review(review, run, traces["before"], dataset, case, allow_fixture=True)


def test_deterministic_check_cannot_create_a_semantic_pass(example):
    run, dataset, case, traces = example
    with pytest.raises(ValidationError, match="never semantic passes"):
        make_review(run, traces["before"], dataset, case, "pass", basis="deterministic_check", rationale="Keywords matched")


@pytest.mark.parametrize("fault,kind", [("missing_citation", "invalid_response"), ("wrong_version", "citation_version_mismatch")])
def test_known_faults_are_caught_without_keyword_grading(example, fault, kind):
    run, dataset, case, traces = example
    trace = traces["after"]
    if fault == "missing_citation":
        trace["answer"]["citations"] = ["invented"]
    else:
        trace["retrieved_passages"][0]["software_versions"] = ["2"]
        request = json.loads(trace["prompt"]["messages"][1]["content"])
        request["evidence"][0]["software_versions"] = ["2"]
        trace["prompt"]["messages"][1]["content"] = json.dumps(request)
    judgment = judge_snapshot(run, trace, dataset, case)
    assert judgment["outcome"] == "fail" and judgment["failure_kind"] == kind
    with pytest.raises(ValidationError):
        sim_review(example, "after", "pass")


def test_fixture_reviews_cannot_grade_live_traces_or_invent_human_reviewers(example):
    run, dataset, case, traces = example
    review = sim_review(example, "before")
    with pytest.raises(ValidationError, match="restricted"):
        validate_review(review, run, traces["before"], dataset, case)
    traces["before"]["origin"] = "live"
    with pytest.raises(ValidationError, match="restricted"):
        sim_review(example, "before")
    traces["before"]["origin"] = "fixture"
    with pytest.raises(ValidationError, match="cannot invent"):
        make_review(run, traces["before"], dataset, case, "pass", basis="fixture", rationale="simulation", reviewer="Invented person")


def test_comparison_cannot_mix_runs_or_case_annotations(example):
    run, dataset, case, traces = example
    a = judge_snapshot(run, traces["before"], dataset, case)
    b = judge_snapshot(run, traces["after"], dataset, case)
    wrong = deepcopy(b)
    wrong["binding"]["result_key"]["configuration_name"] = "different"
    with pytest.raises(ValidationError, match="same case"):
        compare_judgments(a, wrong, allow_fixture=True)
    annotation = relation(example)
    annotation["case_hash"] = "stale"
    with pytest.raises(ValidationError, match="different case"):
        compare_judgments(a, b, annotation, allow_fixture=True)


def test_missing_records_remain_in_denominator_and_raw_data_is_immutable(example):
    run, dataset, case, traces = example
    original = deepcopy(run)
    annotations = read_json(ROOT / "examples/mvp/relations.json")
    snapshots = {slot: load_snapshot(ROOT / "examples/mvp" / slot / "manifest.json") for slot in ("before", "after")}
    value = evaluate_run(run, dataset, annotations, snapshots=snapshots, allow_fixture=True)
    assert value["counts"]["planned_answer_records"] == 40
    assert value["counts"]["recorded_answer_records"] == 2
    assert value["counts"]["missing_answer_records"] == 38
    assert value["counts"]["answer_outcomes"]["run_error"] == 38
    assert value["counts"]["human_reviewed_cases"] == value["counts"]["human_answer_reviews"] == 0
    assert run == original


def test_duplicate_results_or_reviews_are_rejected(example):
    run, dataset, case, traces = example
    annotations = read_json(ROOT / "examples/mvp/relations.json")
    run["results"].append(deepcopy(run["results"][0]))
    with pytest.raises(ValidationError, match="Duplicate result"):
        evaluate_run(run, dataset, annotations, snapshots={slot: load_snapshot(ROOT / "examples/mvp" / slot / "manifest.json") for slot in ("before", "after")}, allow_fixture=True)


def test_default_version_cannot_be_redefined_by_imported_run_metadata(example):
    run, dataset, case, traces = example
    default_case = next(item for item in dataset["cases"] if item["target"] == "snapshot_default")
    trace = deepcopy(traces["after"])
    trace["case_id"] = default_case["case_id"]
    trace["question"] = asdict(QuestionInput.from_case(default_case, "after"))
    trace["effective_version"] = "1"
    run["snapshot_defaults"]["after"] = "1"
    snapshots = {slot: load_snapshot(ROOT / "examples/mvp" / slot / "manifest.json") for slot in ("before", "after")}
    with pytest.raises(ValidationError, match="version"):
        binding(run, trace, dataset, default_case, snapshots=snapshots)
    with pytest.raises(ValidationError, match="trusted"):
        evaluate_run(run, dataset, read_json(ROOT / "examples/mvp/relations.json"), snapshots=snapshots, allow_fixture=True)


def test_citation_in_retrieval_but_absent_from_prompt_is_a_trace_error(example):
    run, dataset, case, traces = example
    request = json.loads(traces["after"]["prompt"]["messages"][1]["content"])
    request["evidence"] = []
    traces["after"]["prompt"]["messages"][1]["content"] = json.dumps(request)
    value = judge_snapshot(run, traces["after"], dataset, case)
    assert value["outcome"] == "run_error"
    assert "prompt evidence differs" in value["checks"][0]["detail"]


@pytest.mark.parametrize("change", ["missing_snapshots", "null_results", "null_trace", "list_case_id", "list_origin", "false_live_origin"])
def test_malformed_imports_and_misleading_origin_labels_are_actionable(example, change):
    run, dataset, case, traces = example
    if change == "missing_snapshots":
        del run["snapshots"]
    elif change == "null_results":
        run["results"] = None
    elif change == "null_trace":
        run["results"][0] = None
    elif change == "list_case_id":
        run["results"][0]["case_id"] = []
    elif change == "list_origin":
        run["results"][0]["origin"] = []
    else:
        run["origin"] = "live"
    with pytest.raises(ValidationError):
        evaluate_run(run, dataset, read_json(ROOT / "examples/mvp/relations.json"),
            snapshots={slot: load_snapshot(ROOT / "examples/mvp" / slot / "manifest.json") for slot in ("before", "after")}, allow_fixture=True)
