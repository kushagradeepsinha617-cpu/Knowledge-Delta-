"""Real localhost HTTP tests; TEST-ONLY reviews use copied temporary projects."""
from contextlib import contextmanager
from http.client import HTTPConnection
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

import pytest

from knowledge_delta.web_app import create_server

ROOT = Path(__file__).resolve().parents[1]
CASE = "request-timeout-change"


@pytest.fixture
def project(tmp_path):
    shutil.copytree(ROOT / "examples/mvp", tmp_path / "examples/mvp")
    return tmp_path


@contextmanager
def serving(project):
    server = create_server(project, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def request(server, path, body=None, headers=None, method=None):
    connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=15)
    supplied = {"Content-Type": "application/json", "X-KnowledgeDelta-Token": server.app.csrf}
    supplied.update(headers or {})
    raw = json.dumps(body).encode() if isinstance(body, dict) else body
    try:
        connection.request(method or ("POST" if body is not None else "GET"), path, body=raw, headers=supplied)
        response = connection.getresponse()
        content = response.read()
        mime = response.getheader("Content-Type", "")
        return response.status, json.loads(content) if mime.startswith("application/json") else content, dict(response.getheaders())
    finally:
        connection.close()


def load(server, options=None):
    status, result, _ = request(server, "/api/load", options or {})
    assert status == 200, result
    return result["state"]


def row(state, case=CASE, configuration="basic", repetition=1):
    return next(r for r in state["evaluation"]["rows"] if r["case_id"] == case
                and r["configuration_name"] == configuration and r["repetition"] == repetition)


def review_body(state):
    tokens = row(state)["snapshots"]["before"]["review_form"]
    return {"case_id": CASE, "configuration": "basic", "slot": "before", "repetition": 1,
        "outcome": "pass", "reviewer": "TEST-ONLY-HTTP", "rationale": "Synthetic request test, no actual human review.",
        "expected_binding_hash": tokens["binding_hash"], "expected_revision": tokens["revision"]}


def test_startup_and_readiness_are_local_and_do_not_create_review_state(project):
    with serving(project) as server:
        assert server.server_address[0] == "127.0.0.1"
        status, state, headers = request(server, "/api/state")
        assert status == 200 and state["loaded"] is False and len(state["csrf"]) > 30
        assert state["readiness"]["interface"] == "Python standard library"
        assert "no-store" in headers["Cache-Control"] and "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        assert not (project / "runs").exists()


def test_real_http_loads_complete_labeled_fixture_and_forms(project):
    with serving(project) as server:
        state = load(server)
        report = state["evaluation"]
        assert report["counts"]["recorded_answer_records"] == 80 and len(report["rows"]) == 40
        assert "SIMULATED FIXTURE" in state["notice"] and report["origin"] == "fixture"
        assert report["counts"]["human_answer_reviews"] == 0
        assert report["metrics"]["assistant"]["accuracy_resolved_human_judgments_only"]["value"] is None
        assert len(state["snapshots"]) == 2 and len(state["relation_forms"]) == 20
        assert row(state)["snapshots"]["before"]["review_form"]["revision"] == 0
        assert not (project / "runs").exists()


def test_reviews_persist_and_stale_displayed_revision_cannot_overwrite(project):
    with serving(project) as server:
        state = load(server)
        body = review_body(state)
        status, saved, _ = request(server, "/api/review-answer", body)
        assert status == 200 and saved["state"]["evaluation"]["counts"]["human_answer_reviews"] == 1
        status, error, _ = request(server, "/api/review-answer", body)
        assert status == 409 and "error" in error
        status, current, _ = request(server, "/api/state")
        assert status == 200 and row(current)["snapshots"]["before"]["review_form"]["revision"] == 1
        assert current["evaluation"]["counts"]["human_reviewed_cases"] == 0


def test_actual_abstention_and_expected_change_reviews_remain_separate(project):
    with serving(project) as server:
        state = load(server)
        body = review_body(state)
        body.update(case_id="backup-cipher-missing", abstention_judgment="appropriate")
        tokens = row(state, case=body["case_id"])["snapshots"]["before"]["review_form"]
        body.update(expected_binding_hash=tokens["binding_hash"], expected_revision=tokens["revision"])
        assert request(server, "/api/review-answer", body)[0] == 200
        tokens = state["relation_forms"][CASE]
        status, result, _ = request(server, "/api/review-relation", {"case_id": CASE, "relation": "should_change",
            "reviewer": "TEST-ONLY", "rationale": "Synthetic expected-change review", "expected_binding_hash": tokens["binding_hash"],
            "expected_revision": tokens["revision"]})
        assert status == 200 and row(result["state"])["relation"]["basis"] == "human_review"
        assert result["state"]["evaluation"]["counts"]["human_reviewed_cases"] == 0


def test_mechanical_failure_cannot_be_approved_as_a_pass(project):
    with serving(project) as server:
        state = load(server)
        tokens = row(state, case="installation-rewording")["snapshots"]["after"]["review_form"]
        body = review_body(state)
        body.update(case_id="installation-rewording", slot="after", expected_binding_hash=tokens["binding_hash"])
        status, result, _ = request(server, "/api/review-answer", body)
        assert status == 400 and "cannot override" in result["error"]
        assert not (project / "runs/manual_reviews.sqlite3").exists()


@pytest.mark.parametrize("headers", [{"Host": "evil.example"}, {"Origin": "https://evil.example"},
    {"X-KnowledgeDelta-Token": ""}, {"X-KnowledgeDelta-Token": "\u00e9"}, {"Sec-Fetch-Site": "cross-site"}])
def test_cross_site_and_missing_token_requests_do_not_change_state(project, headers):
    with serving(project) as server:
        assert request(server, "/api/load", {}, headers)[0] == 403
        assert server.app.inputs is None and not (project / "runs").exists()


def test_action_bounds_types_and_duplicate_json_fields_are_rejected(project):
    with serving(project) as server:
        assert request(server, "/api/load", b"{}", {"Content-Type": "text/plain"})[0] == 415
        assert request(server, "/api/load", b'{"simulate_judgments":false,"simulate_judgments":true}')[0] == 400
        assert request(server, "/api/load", {"simulate_judgments": "yes"})[0] == 400
        assert request(server, "/api/load", {"dataset": "../outside.json"})[0] == 400
        assert request(server, "/api/load", {"unknown": "bad"})[0] == 400
        assert request(server, "/api/load", b"", {"Content-Length": str(2 * 1024 * 1024 + 1)})[0] == 413
        assert server.app.inputs is None and not (project / "runs").exists()


def test_real_static_assets_are_served_without_exposing_other_files(project):
    with serving(project) as server:
        status, page, _ = request(server, "/")
        assert status == 200 and b'/assets/app.js' in page and b'id="load-form"' in page
        for route, mime in (("/assets/app.js", "text/javascript"), ("/assets/app.css", "text/css")):
            status, content, headers = request(server, route)
            assert status == 200 and content and headers["Content-Type"].startswith(mime)
        assert request(server, "/assets/../../PROJECT_SPEC.md")[0] == 404


def test_export_opens_only_saved_project_files_and_preserves_existing_content(project):
    with serving(project) as server:
        assert request(server, "/download/report.json")[0] == 404
        load(server)
        status, result, _ = request(server, "/api/export", {"directory": "runs/http-report"})
        assert status == 200 and set(result["files"]) == {"report.json", "report.html"}
        status, saved, _ = request(server, "/download/report.json")
        assert status == 200 and saved["origin"] == "fixture"
        status, html, headers = request(server, "/download/report.html")
        assert status == 200 and b"SIMULATED FIXTURE" in html
        assert "Content-Disposition" not in headers and "script-src" not in headers["Content-Security-Policy"]
        (project / "runs/http-report/report.html").write_text("Preserve this existing content", encoding="utf-8")
        assert request(server, "/api/export", {"directory": "runs/http-report"})[0] == 400
        assert (project / "runs/http-report/report.html").read_text() == "Preserve this existing content"
        assert request(server, "/api/export", {"directory": "../outside"})[0] == 400
        assert request(server, "/.venv/pyvenv.cfg")[0] == 404


def test_saved_run_import_never_manufactures_simulated_judgments(project):
    with serving(project) as server:
        state = load(server)
        path = project / "recorded.json"
        path.write_text(json.dumps(state["evaluation"]["raw_run"]), encoding="utf-8")
        original = path.read_bytes()
        state = load(server, {"run_path": "recorded.json"})
        assert state["evaluation"]["input_mode"] == "existing_run"
        assert state["evaluation"]["counts"]["simulated_answer_judgments"] == 0
        assert path.read_bytes() == original
        assert request(server, "/api/load", {"run_path": "recorded.json", "simulate_judgments": True})[0] == 400


def test_fixture_controller_works_with_third_party_imports_disabled(project):
    code = ("import sys;sys.path.insert(0," + repr(str(ROOT)) + ");"
        "sys.modules.update({n:None for n in ['pandas','numpy','pyarrow','streamlit']});"
        "from knowledge_delta.web_app import Application;"
        "a=Application(" + repr(str(project)) + ");"
        "r=a.action('/api/load',{});assert r['state']['evaluation']['counts']['recorded_answer_records']==80")
    process = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code], capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stderr
