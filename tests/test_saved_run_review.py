"""Import recorded fixtures unchanged; TEST-ONLY reviews stay in temporary projects."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from knowledge_delta import review_workflow
from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError
from scripts import fixture_demo, review_fixture

ROOT = Path(__file__).resolve().parents[1]
CASE = "request-timeout-change"


@pytest.fixture
def saved(tmp_path):
    shutil.copytree(ROOT / "examples/mvp", tmp_path / "examples/mvp")
    run = deepcopy(ReviewSession(tmp_path).run)
    path = tmp_path / "recorded.json"
    path.write_text(json.dumps(run), encoding="utf-8")
    return tmp_path, path, run


def test_import_never_regenerates_answers_or_creates_oracle_reviews(saved, monkeypatch):
    root, path, run = saved
    original = path.read_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError("Import must not replay or generate answers")
    monkeypatch.setattr(review_workflow, "replay", forbidden)
    session = ReviewSession(root, run_path=path)
    report = session.evaluate()
    assert session.input_mode == "existing_run"
    assert report["raw_run"] == run and path.read_bytes() == original
    assert report["review_records"] == []
    assert report["counts"]["simulated_answer_judgments"] == 0
    assert report["counts"]["human_answer_reviews"] == 0
    assert report["origin"] == "fixture" and report["inference_performed_during_review"] is False
    assert "self-reported" in report["import_notice"]
    assert not session.store.path.exists()


def test_import_keeps_repetition_reviews_separate(saved):
    root, path, run = saved
    repeated = deepcopy(run["results"])
    for trace in repeated:
        trace["repetition"] = 2
    run["results"].extend(repeated)
    run["repeats"] = 2
    path.write_text(json.dumps(run), encoding="utf-8")
    session = ReviewSession(root, run_path=path)
    first = session.answer_info(CASE, "basic", "before", 1)
    second = session.answer_info(CASE, "basic", "before", 2)
    assert first["subject"] != second["subject"]
    session.save_answer(CASE, "basic", "before", repetition=2, outcome="pass", reviewer="TEST-ONLY",
        rationale="Synthetic persistence check, not a real human label.",
        expected_binding_hash=second["binding_hash"], expected_revision=0)
    report = ReviewSession(root, run_path=path).evaluate()
    selected = [r for r in report["rows"] if r["case_id"] == CASE and r["configuration_name"] == "basic"]
    assert [r["snapshots"]["before"]["judgment"]["outcome"] for r in selected] == ["needs_human_review", "pass"]
    assert report["counts"]["planned_answer_records"] == 160
    assert report["counts"]["human_answer_reviews"] == 1


@pytest.mark.parametrize("mutation", ["dataset", "snapshot", "default", "origin", "duplicate", "kind", "version"])
def test_invalid_import_is_rejected_before_review_journal(saved, mutation):
    root, path, run = saved
    if mutation == "dataset": run["dataset_hash"] = "wrong"
    elif mutation == "snapshot": run["snapshots"]["after"] = "wrong"
    elif mutation == "default": run["snapshot_defaults"]["after"] = "wrong"
    elif mutation == "origin": run["origin"] = "live"
    elif mutation == "duplicate": run["results"].append(deepcopy(run["results"][0]))
    elif mutation == "kind": run["kind"] = "knowledge_delta_evaluation"
    else: run["schema_version"] = True
    path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValidationError):
        ReviewSession(root, run_path=path)
    assert not (root / "runs/manual_reviews.sqlite3").exists()


def test_import_cannot_add_simulated_grades_or_escape_size_and_path_limits(saved, monkeypatch):
    root, path, _ = saved
    with pytest.raises(ValidationError, match="oracle"):
        ReviewSession(root, run_path=path, simulate_judgments=True)
    with pytest.raises(ValidationError, match="inside this project"):
        ReviewSession(root, run_path=root.parent / "outside.json")
    monkeypatch.setattr(review_workflow, "MAX_RUN_BYTES", 1)
    with pytest.raises(ValidationError, match="16 MiB"):
        ReviewSession(root, run_path=path)


def test_missing_import_record_is_retained_as_error(saved):
    root, path, run = saved
    run["results"].pop()
    path.write_text(json.dumps(run), encoding="utf-8")
    report = ReviewSession(root, run_path=path).evaluate()
    assert report["counts"]["planned_answer_records"] == 80
    assert report["counts"]["recorded_answer_records"] == 79
    assert report["counts"]["missing_answer_records"] == 1


def test_cli_inspects_and_exports_saved_records_without_inference(saved, monkeypatch, capsys):
    root, path, run = saved
    monkeypatch.setattr(review_fixture, "ROOT", root)
    monkeypatch.setattr(fixture_demo, "ROOT", root)
    assert review_fixture.main(["--run", str(path), "--case-id", CASE, "--slot", "before"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["mode"] == "existing_run" and info["writes_performed"] is False
    args = ["--run", str(path), "--before", str(root / "examples/mvp/before/manifest.json"),
        "--after", str(root / "examples/mvp/after/manifest.json"), "--dataset", str(root / "examples/mvp/cases.json"),
        "--relations", str(root / "examples/mvp/relations.json"), "--output-dir", "runs/imported"]
    assert fixture_demo.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "IMPORTED RUN" and result["live_inference_performed"] is False
    exported = json.loads((root / "runs/imported/report.json").read_text(encoding="utf-8"))
    assert exported["raw_run"] == run and exported["counts"]["human_answer_reviews"] == 0
    assert not (root / "runs/manual_reviews.sqlite3").exists()
