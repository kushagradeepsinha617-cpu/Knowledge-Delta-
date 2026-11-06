"""Fixture replay/export contracts; simulated outcomes are not benchmark results."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path

import pytest

from knowledge_delta.reports import html_report
from knowledge_delta.workflow import export_report, fixture_report
from knowledge_delta.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def sample(simulated=True):
    directory = ROOT / "examples/mvp"
    return fixture_report(directory / "before/manifest.json", directory / "after/manifest.json",
                          directory / "cases.json", directory / "relations.json", simulate_judgments=simulated)


def test_fixture_demo_preserves_all_statuses_without_human_or_live_claims():
    evaluation = sample()
    assert evaluation["origin"] == "fixture" and evaluation["fixture_mode"] is True
    assert evaluation["counts"]["planned_answer_records"] == evaluation["counts"]["recorded_answer_records"] == 80
    assert evaluation["counts"]["human_reviewed_cases"] == evaluation["counts"]["human_answer_reviews"] == 0
    assert {row["comparison"]["status"] for row in evaluation["rows"]} == {
        "pass", "expected_answer_change", "failure_to_adopt_expected_change", "previously_correct_now_incorrect",
        "incorrect_in_both_snapshots", "needs_human_review", "run_error"}
    assert all(trace["generation_performed"] is False and trace["model"] is None for trace in evaluation["raw_run"]["results"])
    assert all(record["basis"] == "fixture" and record["reviewer"] is None for record in evaluation["review_records"])


def test_default_fixture_mode_never_supplies_simulated_semantic_passes():
    evaluation = sample(simulated=False)
    assert evaluation["counts"]["answer_outcomes"]["pass"] == 0
    assert evaluation["counts"]["simulated_answer_judgments"] == 0
    assert not evaluation["review_records"]
    assert all(row["relation"]["basis"] == "draft" for row in evaluation["rows"])


def test_html_is_self_contained_and_escapes_source_answer_and_rubric_markup():
    evaluation = sample()
    marker = '<script>alert("source")</script><img src="https://example.invalid/leak" onerror="alert(1)">'
    row = evaluation["rows"][0]
    row["case"]["question"] = marker
    row["snapshots"]["before"]["trace"]["answer"]["answer"] = marker
    row["snapshots"]["before"]["trace"]["retrieved_passages"][0]["text"] = marker
    row["snapshots"]["before"]["expectation"]["rubric"] = marker
    output = html_report(evaluation)
    class Inspector(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tags = []
            self.external = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)
            self.external.extend(value for name, value in attrs if name in ("src", "href") and value and not value.startswith("#"))
    inspector = Inspector()
    inspector.feed(output)
    assert "script" not in inspector.tags and "img" not in inspector.tags
    assert inspector.external == []
    assert "&lt;script&gt;" in output and "SIMULATED FIXTURE" in output
    assert "Content-Security-Policy" in output


def test_report_distinguishes_retrieval_from_attempted_generation_context():
    evaluation = sample()
    trace = evaluation["rows"][0]["snapshots"]["before"]["trace"]
    assert "Scripted evidence — simulated" in html_report(evaluation)
    trace["origin"] = "live"  # Synthetic renderer input only, never a live result.
    trace["generation_attempted"] = False
    assert "Retrieved passages — no model request" in html_report(evaluation)
    trace["generation_attempted"] = True
    assert "Recorded request passages — effective model context unverified" in html_report(evaluation)


def test_html_preserves_stale_review_warning_and_escaped_history():
    evaluation = sample()
    evaluation["stale_reviews"] = [{"reason": "Answer changed", "payload": "<script>old review</script>"}]
    evaluation["review_history"] = [{"rationale": "<img src=x>"}]
    rendered = html_report(evaluation)
    assert "Stale review records" in rendered and "do not grade the current answers" in rendered
    assert "Manual review history" in rendered
    assert "&lt;script&gt;old review&lt;/script&gt;" in rendered and "&lt;img src=x&gt;" in rendered


def test_export_is_portable_idempotent_and_does_not_overwrite_changed_files(tmp_path):
    evaluation = sample()
    outputs = export_report(tmp_path, "exports/demo", evaluation)
    assert json.loads(Path(outputs["report.json"]).read_text(encoding="utf-8"))["run_id"] == evaluation["run_id"]
    assert "<!doctype html>" in Path(outputs["report.html"]).read_text(encoding="utf-8")
    assert export_report(tmp_path, "exports/demo", evaluation) == outputs
    Path(outputs["report.html"]).write_text("user-edited report", encoding="utf-8")
    with pytest.raises(ValidationError, match="different content"):
        export_report(tmp_path, "exports/demo", evaluation)
    assert Path(outputs["report.html"]).read_text(encoding="utf-8") == "user-edited report"


@pytest.mark.parametrize("directory", ["../outside", "knowledge_delta/results", "examples/reports", ".tools/reports", "."])
def test_export_cannot_escape_project_or_overwrite_sources(tmp_path, directory):
    with pytest.raises(ValidationError):
        export_report(tmp_path, directory, {"kind": "unused"})


@pytest.mark.parametrize("environment", [".venv", ".venv-ml"])
def test_export_does_not_create_reports_inside_active_python_environments(tmp_path, environment):
    site_packages = tmp_path / environment / "Lib/site-packages"
    site_packages.mkdir(parents=True)
    marker = site_packages / "preserve.txt"
    marker.write_text("existing environment contents", encoding="utf-8")
    for target in (environment, f"{environment}/Lib/site-packages/report-output"):
        with pytest.raises(ValidationError, match="environment"):
            export_report(tmp_path, target, {"kind": "unused"})
    assert marker.read_text(encoding="utf-8") == "existing environment contents"
    assert not (site_packages / "report-output").exists()
    assert not (tmp_path / environment / "report.json").exists()
