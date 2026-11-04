"""TEST-ONLY reference/answer annotations live solely in temporary test projects.

No independent audit or human review actually occurred. These payloads exercise
input validation and persistence, not model/evaluator benchmark performance.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from knowledge_delta import review_workflow
from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]
CASE = "request-timeout-change"


@pytest.fixture
def project(tmp_path):
    shutil.copytree(ROOT / "examples/mvp", tmp_path / "examples/mvp")
    return tmp_path


def reference(project):
    session = ReviewSession(project)
    return {"schema_version": 1,
        "binding": deepcopy(session.answer_info(CASE, "basic", "before")["binding"]),
        "reference_outcome": "not_failure", "basis": "independent_human_reference",
        "reviewer": "TEST-ONLY-REFERENCE-PROCEDURE", "reviewed_at": "2026-01-01T00:00:00+00:00",
        "rationale": "Synthetic reference input test; no actual independent audit occurred.",
        "independence_attested": True}


def write_labels(project, labels):
    path = project / "test-reference-labels.json"
    path.write_text(json.dumps(labels), encoding="utf-8")
    return path


def test_default_has_no_reference_labels_or_label_generation_side_effects(project):
    session = ReviewSession(project)
    evaluation = session.evaluate()
    assert evaluation["reference_labels"] == [] and evaluation["reference_labels_path"] is None
    assert evaluation["metrics"]["testing_tool"]["reference_labels_submitted"] == 0
    assert not (project / "runs").exists()
    assert not (project / "test-reference-labels.json").exists()


def test_explicit_fixture_references_are_preserved_without_creating_benchmark_truth(project):
    labels = [reference(project)]
    path = write_labels(project, labels)
    original = path.read_bytes()
    session = ReviewSession(project, reference_labels=path.name)
    evaluation = session.evaluate()
    assert evaluation["reference_labels"] == labels
    assert evaluation["reference_labels_path"] == path.name
    assert evaluation["metrics"]["testing_tool"]["reference_labels_submitted"] == 1
    assert evaluation["metrics"]["testing_tool"]["ineligible_reference_labels"] == 1
    assert evaluation["metrics"]["testing_tool"]["precision"]["value"] is None
    assert evaluation["metrics"]["testing_tool"]["recall"]["value"] is None
    assert evaluation["metrics"]["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None
    assert evaluation["counts"]["human_answer_reviews"] == evaluation["counts"]["human_reviewed_cases"] == 0
    evaluation["reference_labels"][0]["rationale"] = "Edited exported copy"
    assert session.reference_labels == labels and path.read_bytes() == original
    assert not session.store.path.exists()


@pytest.mark.parametrize("fault", ["stale_trace", "stale_dataset", "unknown_result", "duplicate", "answer_review_basis", "unattested", "null_label"])
def test_invalid_references_are_rejected_before_review_actions_or_journal_creation(project, fault):
    label = reference(project)
    labels = [label]
    if fault == "stale_trace":
        label["binding"]["trace_hash"] = "old-trace"
    elif fault == "stale_dataset":
        label["binding"]["dataset_hash"] = "old-dataset"
    elif fault == "unknown_result":
        label["binding"]["result_key"]["case_id"] = "not-in-this-run"
    elif fault == "duplicate":
        labels.append(deepcopy(label))
    elif fault == "answer_review_basis":
        label["basis"] = "human_review"
    elif fault == "unattested":
        label["independence_attested"] = False
    else:
        labels = [None]
    path = write_labels(project, labels)
    with pytest.raises(ValidationError):
        ReviewSession(project, reference_labels=path)
    assert not (project / "runs").exists()


def test_reference_input_path_size_and_container_are_explicitly_constrained(project, monkeypatch):
    path = write_labels(project, [reference(project)])
    with pytest.raises(ValidationError, match="inside this project"):
        ReviewSession(project, reference_labels=project.parent / "outside.json")
    with pytest.raises(ValidationError, match="regular independent-reference"):
        ReviewSession(project, reference_labels=project / "missing.json")
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError, match="must be a list"):
        ReviewSession(project, reference_labels=path)
    write_labels(project, [reference(project)])
    monkeypatch.setattr(review_workflow, "MAX_RUN_BYTES", 1)
    with pytest.raises(ValidationError, match="16 MiB"):
        ReviewSession(project, reference_labels=path)
    assert not (project / "runs").exists()


def test_duplicate_json_fields_and_changed_result_reference_cannot_be_silently_accepted(project):
    path = project / "test-reference-labels.json"
    path.write_text('[{"schema_version":1,"schema_version":1}]', encoding="utf-8")
    with pytest.raises(ValidationError, match="duplicate JSON"):
        ReviewSession(project, reference_labels=path)
    path = write_labels(project, [reference(project)])
    session = ReviewSession(project, reference_labels=path)
    trace = session.answer_info(CASE, "basic", "before")["trace"]
    trace["answer"]["answer"] = "Changed scripted answer after reference import"
    with pytest.raises(ValidationError, match="stale"):
        session.evaluate()
    assert not session.store.path.exists()


def test_explicit_abstention_classification_round_trips_without_upgrading_draft_cases(project):
    session = ReviewSession(project)
    case_id = "backup-cipher-missing"
    info = session.answer_info(case_id, "basic", "before")
    session.save_answer(case_id, "basic", "before", outcome="pass", reviewer="TEST-ONLY-ANSWER-REVIEWER",
        rationale="Synthetic persistence test, not an actual human review.", abstention_judgment="appropriate",
        expected_binding_hash=info["binding_hash"], expected_revision=0)
    evaluation = ReviewSession(project).evaluate()
    record = next(r for r in evaluation["review_records"] if r["binding"]["result_key"]["case_id"] == case_id)
    assert record["abstention_judgment"] == "appropriate"
    assert evaluation["counts"]["human_reviewed_cases"] == 0
    assert evaluation["origin"] == "fixture"
    assert evaluation["metrics"]["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None


@pytest.mark.parametrize("case_id,outcome,classification", [
    (CASE, "pass", "appropriate"),
    ("backup-cipher-missing", "fail", "appropriate"),
    ("backup-cipher-missing", "pass", "unnecessary"),
])
def test_non_abstention_and_contradictory_classifications_never_create_reviews(project, case_id, outcome, classification):
    session = ReviewSession(project)
    info = session.answer_info(case_id, "basic", "before")
    with pytest.raises(ValidationError, match="Abstention"):
        session.save_answer(case_id, "basic", "before", outcome=outcome, reviewer="TEST-ONLY",
            rationale="Injected invalid classification", abstention_judgment=classification,
            expected_binding_hash=info["binding_hash"], expected_revision=0)
    assert not session.store.path.exists()
