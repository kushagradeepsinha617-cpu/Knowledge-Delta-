"""Explicit REAL Streamlit AppTest checks, excluded from ordinary tests/.

Requires an already installed project-local Streamlit environment. No downloads.
All TEST-ONLY review actions use a temporary copied project, never the real journal.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

from knowledge_delta.review_workflow import ReviewSession

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(monkeypatch, tmp_path):
    if importlib.util.find_spec("streamlit") is None:
        pytest.fail("Real Streamlit integration unavailable: explicitly install the project-local UI dependencies first", pytrace=False)
    project = tmp_path / "project"
    shutil.copytree(ROOT / "examples/mvp", project / "examples/mvp")
    for key, relative in {"USERPROFILE": "profile", "LOCALAPPDATA": "profile/AppData/Local",
                          "APPDATA": "profile/AppData/Roaming", "XDG_CACHE_HOME": "cache",
                          "TEMP": "tmp", "TMP": "tmp"}.items():
        path = tmp_path / relative
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(key, str(path))
    monkeypatch.setenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    monkeypatch.setenv("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    from streamlit.testing.v1 import AppTest
    code = "from scripts.streamlit_app import main\nmain(" + json.dumps(str(project)) + ")\n"
    return AppTest.from_string(code, default_timeout=30), project


def button(at, label):
    return next(item for item in at.button if item.label == label)


def test_real_interface_loads_complete_fixture_without_model_calls(app):
    at, project = app
    at.run()
    assert not at.exception
    button(at, "Load records").click().run()
    assert not at.exception
    assert any("SIMULATED FIXTURE" in item.value for item in at.warning)
    assert {item.label: item.value for item in at.metric}["Answer records"] == "80"
    assert not (project / "runs/manual_reviews.sqlite3").exists()


def test_real_interface_saves_explicit_test_review_in_temporary_project(app):
    at, project = app
    at.run()
    button(at, "Load records").click().run()
    next(item for item in at.text_input if item.label == "Your reviewer name").input("TEST-ONLY-APPTEST")
    next(item for item in at.selectbox if item.label == "Answer judgment").select("pass")
    next(item for item in at.text_area if item.label.startswith("Reason, referring")).input("Injected AppTest review of the scripted before answer; no real human review.")
    button(at, "Save answer review").click().run()
    assert not at.exception
    evaluation = ReviewSession(project).evaluate()
    assert evaluation["counts"]["human_answer_reviews"] == 1
    assert evaluation["counts"]["human_reviewed_cases"] == 0 and evaluation["origin"] == "fixture"


def test_real_interface_rejects_input_path_outside_project(app):
    at, project = app
    at.run()
    next(item for item in at.text_input if item.label == "Case dataset").input("../outside.json")
    button(at, "Load records").click().run()
    assert not at.exception and at.error
    assert not (project / "runs/manual_reviews.sqlite3").exists()
