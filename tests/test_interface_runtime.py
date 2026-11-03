"""Launcher and display-token tests; all positive Streamlit execution is mocked."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_delta import interface_runtime
from knowledge_delta.interface_state import displayed_tokens, tokens_changed
from knowledge_delta.validation import ValidationError


def environment(monkeypatch, root, installed):
    (root / "scripts").mkdir()
    (root / "scripts/streamlit_app.py").write_text("# inert test fixture\n", encoding="utf-8")
    monkeypatch.setattr(interface_runtime.sys, "prefix", str(root / ".venv"))
    monkeypatch.setattr(interface_runtime.sys, "base_prefix", str(root.parent / "base-python"))
    monkeypatch.setattr(interface_runtime.sys, "executable", str(root / ".venv/Scripts/python.exe"))
    original = interface_runtime.importlib.util.find_spec
    monkeypatch.setattr(interface_runtime.importlib.util, "find_spec", lambda name: SimpleNamespace() if name == "streamlit" and installed else None if name == "streamlit" else original(name))
    metadata = interface_runtime.importlib.metadata.version
    monkeypatch.setattr(interface_runtime.importlib.metadata, "version", lambda name: "TEST-ONLY-VERSION" if name == "streamlit" else metadata(name))


def test_missing_ui_package_is_read_only_and_never_installed(tmp_path, monkeypatch):
    environment(monkeypatch, tmp_path, False)
    plan = interface_runtime.interface_plan(tmp_path)
    assert plan["status"] == "missing_streamlit" and plan["streamlit_version"] is None
    assert plan["downloads_performed"] is False and plan["ui_launched"] is False
    assert not (tmp_path / ".tools").exists()
    with pytest.raises(ValidationError, match="missing_streamlit"):
        interface_runtime.start_interface(tmp_path)
    assert not (tmp_path / ".tools").exists()


def test_global_environment_is_not_accepted_as_project_ui_setup(tmp_path, monkeypatch):
    environment(monkeypatch, tmp_path, True)
    monkeypatch.setattr(interface_runtime.sys, "prefix", interface_runtime.sys.base_prefix)
    assert interface_runtime.interface_plan(tmp_path)["status"] == "wrong_environment"


def test_explicit_ui_start_is_local_and_only_changes_child_environment(tmp_path, monkeypatch):
    environment(monkeypatch, tmp_path, True)
    class Probe:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def setsockopt(self, *args):
            pass

        def bind(self, endpoint):
            assert endpoint == ("127.0.0.1", 8501)
    monkeypatch.setattr(interface_runtime.socket, "socket", lambda *args: Probe())
    before = dict(os.environ)
    def run(command, *, cwd, env, check):
        assert "--server.address=127.0.0.1" in command and "--browser.gatherUsageStats=false" in command
        assert "--server.headless=true" in command and "--server.fileWatcherType=none" in command
        assert cwd == tmp_path and check is False
        for key in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "XDG_CACHE_HOME"):
            assert Path(env[key]).is_relative_to(tmp_path) and Path(env[key]).is_dir()
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(interface_runtime.subprocess, "run", run)
    assert interface_runtime.start_interface(tmp_path) == 0
    assert os.environ.keys() == before.keys()
    assert all(os.environ[key] == value for key, value in before.items())


def test_displayed_binding_and_revision_are_not_refreshed_implicitly():
    state = {}
    first = displayed_tokens(state, "form", {"binding_hash": "first-answer", "revision": 0})
    later = {"binding_hash": "changed-answer", "revision": 3}
    assert displayed_tokens(state, "form", later) == first
    assert tokens_changed(first, later) is True
    refreshed = displayed_tokens(state, "form", later, refresh=True)
    assert refreshed["binding_hash"] == "changed-answer" and refreshed["revision"] == 3
    assert refreshed["epoch"] == first["epoch"] + 1 and not tokens_changed(refreshed, later)


def test_contained_ui_launcher_does_not_claim_posix_profile_support(tmp_path, monkeypatch):
    monkeypatch.setattr(interface_runtime, "WINDOWS_SUPPORTED", False)
    with pytest.raises(ValidationError, match="Windows-only"):
        interface_runtime.interface_plan(tmp_path)
