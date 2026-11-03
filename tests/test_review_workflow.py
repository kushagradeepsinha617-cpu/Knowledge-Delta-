"""Controller tests use TEST-ONLY reviewers in temporary databases, never real reviews."""
from copy import deepcopy
from pathlib import Path
import json
import shutil

import pytest

from knowledge_delta.review_store import ReviewConflict
from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError
from scripts import review_fixture

ROOT = Path(__file__).resolve().parents[1]
CASE = "request-timeout-change"


@pytest.fixture
def project(tmp_path):
    shutil.copytree(ROOT / "examples/mvp", tmp_path / "examples/mvp")
    return tmp_path


def save(session, *, outcome="pass", slot="before", failure_kind=None):
    info = session.answer_info(CASE, "basic", slot)
    return session.save_answer(CASE, "basic", slot, outcome=outcome, failure_kind=failure_kind,
        reviewer="TEST-ONLY-REVIEWER", rationale="Injected controller test review, not a real human judgment.",
        expected_binding_hash=info["binding_hash"], expected_revision=info["revision"])


def test_explicit_review_persists_and_reopens_without_upgrading_case_labels(project):
    session = ReviewSession(project)
    original = deepcopy(session.dataset)
    assert not session.store.path.exists()
    revision = save(session)
    reopened = ReviewSession(project, simulate_judgments=True)
    info = reopened.answer_info(CASE, "basic", "before")
    assert info["revision"] == revision
    evaluation = reopened.evaluate()
    assert evaluation["origin"] == "fixture" and evaluation["counts"]["human_answer_reviews"] == 1
    assert evaluation["counts"]["human_reviewed_cases"] == 0
    assert reopened.dataset == original
    assert all(trace["model"] is None and trace["generation_performed"] is False for trace in evaluation["raw_run"]["results"])


def test_stale_answer_review_is_visible_and_cannot_fall_back_to_simulated_pass(project):
    session = ReviewSession(project, simulate_judgments=True)
    save(session)
    info = session.answer_info(CASE, "basic", "before")
    info["trace"]["answer"]["answer"] = "Changed after the injected review."
    evaluation = session.evaluate()
    row = next(row for row in evaluation["rows"] if row["case_id"] == CASE and row["configuration_name"] == "basic")
    assert row["snapshots"]["before"]["judgment"]["outcome"] == "needs_human_review"
    assert evaluation["stale_reviews"][0]["kind"] == "answer"
    assert len(evaluation["review_history"]) == 1
    assert evaluation["counts"]["human_answer_reviews"] == 0


def test_outdated_displayed_binding_and_database_revision_are_distinct_conflicts(project):
    session = ReviewSession(project)
    info = session.answer_info(CASE, "basic", "before")
    save(session)
    with pytest.raises(ReviewConflict, match="another session"):
        session.save_answer(CASE, "basic", "before", outcome="pass", reviewer="TEST-ONLY", rationale="stale tab",
            expected_binding_hash=info["binding_hash"], expected_revision=0)
    with pytest.raises(ReviewConflict, match="displayed"):
        session.save_answer(CASE, "basic", "before", outcome="pass", reviewer="TEST-ONLY", rationale="stale evidence",
            expected_binding_hash="old-answer-hash", expected_revision=1)
    assert len(session.store.history(session.run["run_id"])) == 1


def test_mechanically_invalid_pass_is_rejected_before_database_creation(project):
    session = ReviewSession(project)
    info = session.answer_info("installation-rewording", "basic", "after")
    with pytest.raises(ValidationError, match="cannot override"):
        session.save_answer("installation-rewording", "basic", "after", outcome="pass", reviewer="TEST-ONLY",
            rationale="Injected invalid override", expected_binding_hash=info["binding_hash"], expected_revision=0)
    assert not session.store.path.exists()


def test_relation_review_is_separate_and_stale_relation_reverts_to_draft_not_fixture(project):
    session = ReviewSession(project, simulate_judgments=True)
    info = session.relation_info(CASE)
    revision = session.save_relation(CASE, relation="should_change", reviewer="TEST-ONLY", rationale="Injected relation review",
        expected_binding_hash=info["binding_hash"], expected_revision=0)
    evaluation = session.evaluate()
    row = next(row for row in evaluation["rows"] if row["case_id"] == CASE)
    assert row["relation"]["basis"] == "human_review"
    assert evaluation["counts"]["human_answer_reviews"] == 0
    payload = deepcopy(session.store.latest("relation", session.run["run_id"])[CASE]["payload"])
    payload["case_hash"] = "stale-case"
    session.store.append("relation", session.run["run_id"], CASE, payload, expected_revision=revision)
    evaluation = session.evaluate()
    row = next(row for row in evaluation["rows"] if row["case_id"] == CASE)
    assert row["relation"]["basis"] == "draft"
    assert evaluation["stale_reviews"][0]["kind"] == "relation"
    assert len(evaluation["review_history"]) == 2


def test_loading_and_evaluating_has_no_review_write_side_effect(project):
    session = ReviewSession(project)
    assert session.evaluate()["counts"]["human_answer_reviews"] == 0
    assert not session.store.path.exists()


def test_review_input_paths_cannot_escape_project(project):
    with pytest.raises(ValidationError, match="inside this project"):
        ReviewSession(project, dataset=project.parent / "outside.json")


def test_human_can_review_a_case_without_an_existing_relation_annotation(project):
    path = project / "examples/mvp/relations.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["relations"] = [item for item in bundle["relations"] if item["case_id"] != CASE]
    path.write_text(json.dumps(bundle), encoding="utf-8")
    session = ReviewSession(project)
    info = session.relation_info(CASE)
    revision = session.save_relation(CASE, relation="should_change", reviewer="TEST-ONLY",
        rationale="Injected relation for previously unannotated case", expected_binding_hash=info["binding_hash"], expected_revision=0)
    row = next(row for row in session.evaluate()["rows"] if row["case_id"] == CASE)
    assert row["relation"]["basis"] == "human_review"
    old = deepcopy(session.store.latest("relation", session.run["run_id"])[CASE]["payload"])
    old["case_hash"] = "stale"
    session.store.append("relation", session.run["run_id"], CASE, old, expected_revision=revision)
    value = session.evaluate()
    row = next(row for row in value["rows"] if row["case_id"] == CASE)
    assert row["relation"] is None and row["comparison"]["expected_relation"] == "undetermined"
    assert len(value["stale_reviews"]) == 1


def test_cli_inspection_then_explicit_test_review_uses_displayed_tokens(project, monkeypatch, capsys):
    monkeypatch.setattr(review_fixture, "ROOT", project)
    assert review_fixture.main(["--case-id", CASE, "--slot", "before"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["writes_performed"] is False and not (project / "runs/manual_reviews.sqlite3").exists()
    assert review_fixture.main(["--case-id", CASE, "--slot", "before", "--save", "--outcome", "pass",
        "--reviewer", "TEST-ONLY-CLI", "--rationale", "Injected CLI review in a temporary copied project",
        "--expected-binding", info["binding_hash"], "--expected-revision", str(info["revision"])]) == 0
    saved = json.loads(capsys.readouterr().out)
    assert saved["status"] == "saved" and saved["origin"] == "fixture"
    evaluation = ReviewSession(project).evaluate()
    assert evaluation["counts"]["human_answer_reviews"] == 1 and evaluation["counts"]["human_reviewed_cases"] == 0


def test_cli_save_without_displayed_binding_never_creates_a_review(project, monkeypatch, capsys):
    monkeypatch.setattr(review_fixture, "ROOT", project)
    assert review_fixture.main(["--case-id", CASE, "--save", "--outcome", "pass",
        "--reviewer", "TEST-ONLY-CLI", "--rationale", "Missing inspection tokens"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert not (project / "runs/manual_reviews.sqlite3").exists()
