"""CLI measurement inputs with synthetic annotations in temporary projects only."""
import json
from pathlib import Path
import shutil

import pytest

from knowledge_delta.review_workflow import ReviewSession
from scripts import fixture_demo, review_fixture

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "examples/mvp", tmp_path / "examples/mvp")
    monkeypatch.setattr(review_fixture, "ROOT", tmp_path)
    monkeypatch.setattr(fixture_demo, "ROOT", tmp_path)
    return tmp_path


def test_cli_records_explicit_abstention_assessment_without_promoting_fixture(project, capsys):
    args = ["--case-id", "backup-cipher-missing", "--slot", "before"]
    assert review_fixture.main(args) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["trace"]["answer"]["abstained"] is True
    assert review_fixture.main([*args, "--save", "--outcome", "pass", "--abstention-judgment", "appropriate",
        "--reviewer", "TEST-ONLY-CLI", "--rationale", "Synthetic command test; no actual human review.",
        "--expected-binding", info["binding_hash"], "--expected-revision", "0"]) == 0
    capsys.readouterr()
    report = ReviewSession(project).evaluate()
    assert report["review_records"][0]["abstention_judgment"] == "appropriate"
    assert report["origin"] == "fixture" and report["counts"]["human_reviewed_cases"] == 0
    assert report["metrics"]["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None


def test_cli_rejects_abstention_classification_for_nonabstaining_answer(project, capsys):
    args = ["--case-id", "request-timeout-change", "--slot", "before"]
    assert review_fixture.main(args) == 0
    info = json.loads(capsys.readouterr().out)
    assert review_fixture.main([*args, "--save", "--outcome", "pass", "--abstention-judgment", "appropriate",
        "--reviewer", "TEST-ONLY", "--rationale", "Injected invalid classification",
        "--expected-binding", info["binding_hash"], "--expected-revision", "0"]) == 2
    assert "actual abstention" in json.loads(capsys.readouterr().out)["error"]
    assert not (project / "runs/manual_reviews.sqlite3").exists()


def test_cli_reference_import_is_preserved_escaped_and_does_not_score_fixtures(project, capsys):
    session = ReviewSession(project)
    labels = [{"schema_version": 1, "binding": session.answer_info("request-timeout-change", "basic", "before")["binding"],
        "reference_outcome": "not_failure", "basis": "independent_human_reference", "reviewer": "TEST-ONLY",
        "reviewed_at": "2026-01-01T00:00:00+00:00", "rationale": "<script>TEST-ONLY</script>", "independence_attested": True}]
    path = project / "test-only-labels.json"
    path.write_text(json.dumps(labels), encoding="utf-8")
    assert review_fixture.main(["--case-id", "request-timeout-change", "--slot", "before", "--reference-labels", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["writes_performed"] is False
    assert fixture_demo.main(["--before", str(project / "examples/mvp/before/manifest.json"),
        "--after", str(project / "examples/mvp/after/manifest.json"), "--dataset", str(project / "examples/mvp/cases.json"),
        "--relations", str(project / "examples/mvp/relations.json"), "--reference-labels", str(path),
        "--output-dir", "runs/test-reference-export"]) == 0
    capsys.readouterr()
    report = json.loads((project / "runs/test-reference-export/report.json").read_text(encoding="utf-8"))
    assert report["reference_labels"] == labels
    assert report["metrics"]["testing_tool"]["reference_labels_submitted"] == 1
    assert report["metrics"]["testing_tool"]["eligible_reference_labels"] == 0
    assert report["metrics"]["testing_tool"]["precision"]["value"] is None
    html = (project / "runs/test-reference-export/report.html").read_text(encoding="utf-8")
    assert "&lt;script&gt;TEST-ONLY&lt;/script&gt;" in html and "<script>TEST-ONLY</script>" not in html
    assert not session.store.path.exists()


def test_invalid_reference_input_prevents_cli_inspection_and_export(project, capsys):
    path = project / "invalid-labels.json"
    path.write_text("[null]", encoding="utf-8")
    assert review_fixture.main(["--case-id", "request-timeout-change", "--reference-labels", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert not (project / "runs").exists()
