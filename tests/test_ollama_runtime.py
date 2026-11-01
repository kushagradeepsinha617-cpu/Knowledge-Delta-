"""Contained launch contracts. Native execution is always mocked in this suite."""
from hashlib import sha256
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_delta import ollama_runtime
from knowledge_delta.validation import ValidationError


def test_missing_runtime_plan_is_read_only_and_keeps_child_state_inside_project(tmp_path):
    before = dict(os.environ)
    plan = ollama_runtime.runtime_plan(tmp_path)
    assert plan["status"] == "missing_runtime"
    assert plan["native_execution_performed"] is False and plan["downloads_performed"] is False
    assert list(tmp_path.iterdir()) == []
    assert os.environ.keys() == before.keys()
    assert all(os.environ[key] == value for key, value in before.items())
    for key in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "OLLAMA_MODELS"):
        assert Path(plan["environment_overrides"][key]).is_relative_to(tmp_path)
    assert plan["environment_overrides"]["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert plan["environment_overrides"]["OLLAMA_NO_CLOUD"] == "1"
    assert plan["environment_overrides"]["OLLAMA_NUM_PARALLEL"] == "1"
    assert plan["environment_overrides"]["OLLAMA_MAX_LOADED_MODELS"] == "1"


@pytest.mark.parametrize("name", ["../outside.exe", "inside.bat"])
def test_runtime_outside_project_or_wrong_executable_type_is_rejected(tmp_path, name):
    with pytest.raises(ValidationError, match="inside the project"):
        ollama_runtime.runtime_plan(tmp_path, name)


def test_missing_runtime_never_starts_or_creates_profile(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("must not execute any binary")
    monkeypatch.setattr(ollama_runtime.subprocess, "run", forbidden)
    with pytest.raises(ValidationError, match="missing"):
        ollama_runtime.start_runtime(tmp_path, None, "0" * 64)
    assert list(tmp_path.iterdir()) == []


def fixture_executable(root):
    path = root / "ollama.exe"
    body = b"test-only inert bytes: never execute"
    path.write_bytes(body)
    return path, sha256(body).hexdigest()


def test_hash_mismatch_prevents_state_creation_and_native_execution(tmp_path, monkeypatch):
    executable, checksum = fixture_executable(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("hash mismatch must prevent native execution")
    monkeypatch.setattr(ollama_runtime.subprocess, "run", forbidden)
    with pytest.raises(ValidationError, match="hash mismatch"):
        ollama_runtime.start_runtime(tmp_path, executable, "0" * 64)
    assert not (tmp_path / ".tools").exists()


class ProbeDouble:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def setsockopt(self, *args):
        pass

    def bind(self, endpoint):
        assert endpoint == ("127.0.0.1", 11434)


def test_explicit_start_passes_only_child_overrides_without_global_changes(tmp_path, monkeypatch):
    executable, checksum = fixture_executable(tmp_path)
    monkeypatch.setattr(ollama_runtime.socket, "socket", lambda *args: ProbeDouble())
    before = dict(os.environ)
    seen = []
    def run_double(command, *, cwd, env, check):
        seen.append(command)
        assert command == [str(executable), "serve"] and cwd == tmp_path
        assert check is False
        assert env["OLLAMA_NO_CLOUD"] == "1"
        for key in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "OLLAMA_MODELS"):
            assert Path(env[key]).is_relative_to(tmp_path) and Path(env[key]).is_dir()
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(ollama_runtime.subprocess, "run", run_double)
    assert ollama_runtime.start_runtime(tmp_path, executable, checksum) == 0
    assert len(seen) == 1
    assert os.environ.keys() == before.keys()
    assert all(os.environ[key] == value for key, value in before.items())


def test_occupied_port_prevents_start_and_profile_creation(tmp_path, monkeypatch):
    executable, checksum = fixture_executable(tmp_path)
    class Occupied(ProbeDouble):
        def bind(self, endpoint):
            raise OSError("fixture port already occupied")
    monkeypatch.setattr(ollama_runtime.socket, "socket", lambda *args: Occupied())
    def forbidden(*args, **kwargs):
        raise AssertionError("occupied endpoint must prevent execution")
    monkeypatch.setattr(ollama_runtime.subprocess, "run", forbidden)
    with pytest.raises(OSError, match="occupied"):
        ollama_runtime.start_runtime(tmp_path, executable, checksum)
    assert not (tmp_path / ".tools").exists()
