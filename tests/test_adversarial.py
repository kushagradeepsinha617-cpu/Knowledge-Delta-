"""Adverse inputs and verification failures; simulated outputs are test fixtures."""
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_delta import doctor
from knowledge_delta.snapshots import document_path, parse_snapshot
from knowledge_delta.validation import ValidationError, read_json
from scripts import run_checks


@pytest.mark.parametrize("name", ["CON .md", "NUL .txt", "dir/COM1 .md", "LPT¹ .txt"])
def test_device_aliases_fail_before_resolution_or_read(name):
    with pytest.raises(ValidationError, match="unsafe Windows"):
        document_path(Path("/virtual"), name)


def test_nonregular_document_is_not_opened(monkeypatch):
    import stat
    raw = {"schema_version": 1, "name": "test", "domain": "test", "default_version": None,
           "provenance": "constructed", "documents": [{
               "document_id": "pipe", "path": "pipe.md", "source_reference": "constructed://pipe",
               "source_revision": None, "software_versions": [], "title": "Pipe"}]}
    special = SimpleNamespace(stat=lambda: SimpleNamespace(st_mode=stat.S_IFIFO),
                              read_bytes=lambda: pytest.fail("special file must not be opened"))
    monkeypatch.setattr("knowledge_delta.snapshots.document_path", lambda *args: special)
    with pytest.raises(ValidationError, match="regular file"):
        parse_snapshot(raw, Path.cwd())


def test_huge_json_integer_has_an_actionable_error(monkeypatch):
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: StringIO("9" * 5000))
    with pytest.raises(ValidationError, match="synthetic.json"):
        read_json(Path("synthetic.json"))


@pytest.mark.parametrize("error", [ValueError("integer limit"), RecursionError("deep input")])
def test_decoder_resource_errors_are_validation_errors(monkeypatch, error):
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: StringIO("{}"))
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr("knowledge_delta.validation.json.load", fail)
    with pytest.raises(ValidationError, match="synthetic.json"):
        read_json(Path("synthetic.json"))


@pytest.mark.parametrize("payload", [
    [], {"models": [3]}, {"models": [{"name": None}]},
    {"models": [{"name": "qwen3:1.7b", "digest": 3}]}, {"models": [{}]},
])
def test_malformed_inventory_is_not_model_availability(monkeypatch, payload):
    fake = SimpleNamespace(open=lambda *args, **kwargs: BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr(doctor, "build_opener", lambda *args: fake)
    result = doctor.readiness(check_ollama=True)["ollama"]
    assert result["status"] == "unavailable_or_invalid_response"
    assert result["inference_verified"] is False


def test_inventory_cannot_redirect_off_localhost(monkeypatch):
    def opener(*handlers):
        redirects = [h for h in handlers if isinstance(h, doctor.NoRedirects)]
        assert len(redirects) == 1
        assert redirects[0].redirect_request(None, None, 302, "moved", {}, "https://example.com") is None
        return SimpleNamespace(open=lambda *args, **kwargs: BytesIO(b'{"models":[]}'))
    monkeypatch.setattr(doctor, "build_opener", opener)
    assert doctor.readiness(check_ollama=True)["ollama"]["status"] == "model_missing"


def test_inventory_read_is_bounded(monkeypatch):
    class LargeInventory(BytesIO):
        def read(self, size=-1):
            assert size == doctor.MAX_INVENTORY_BYTES + 1
            return super().read(size)
    fake = SimpleNamespace(open=lambda *args, **kwargs: LargeInventory(b"x" * (doctor.MAX_INVENTORY_BYTES + 2)))
    monkeypatch.setattr(doctor, "build_opener", lambda *args: fake)
    assert "response limit" in doctor.readiness(True)["ollama"]["error"]


def test_inventory_decoder_recursion_is_an_explicit_error(monkeypatch):
    fake = SimpleNamespace(open=lambda *args, **kwargs: BytesIO(b"{}"))
    monkeypatch.setattr(doctor, "build_opener", lambda *args: fake)
    def too_deep(body):
        raise RecursionError("simulated deeply nested inventory")
    monkeypatch.setattr(doctor.json, "loads", too_deep)
    assert "deeply nested" in doctor.readiness(True)["ollama"]["error"]


@pytest.fixture
def sample_project(tmp_path):
    for name in ("knowledge_delta", "scripts", "tests", "examples"):
        (tmp_path / name).mkdir()
    (tmp_path / "knowledge_delta" / "base.py").write_text("# original\n", encoding="utf-8")
    for name in ("pyproject.toml", "requirements-test.txt", ".gitattributes"):
        (tmp_path / name).write_text("", encoding="utf-8")
    return tmp_path


def fake_commands(root, mode, seen=None):
    """Known simulated process records, never benchmark results."""
    def run(arguments, **kwargs):
        if seen is not None:
            seen.append((arguments, kwargs["env"]))
        is_pytest = "pytest" in arguments
        if is_pytest and mode == "timeout":
            raise run_checks.subprocess.TimeoutExpired(arguments, 120, output=b"partial", stderr=b"timeout")
        if is_pytest and mode != "missing_junit":
            path = Path(next(arg.split("=", 1)[1] for arg in arguments if arg.startswith("--junitxml=")))
            if mode == "collection_only":
                path.write_text("<testsuites><testsuite tests='0'/></testsuites>", encoding="utf-8")
            elif mode == "junit_failure":
                path.write_text("<testsuites><testsuite tests='1'><testcase name='simulated'><failure/></testcase></testsuite></testsuites>", encoding="utf-8")
            else:
                path.write_text("<testsuites><testsuite tests='1'><testcase name='simulated'/></testsuite></testsuites>", encoding="utf-8")
        if is_pytest and mode == "failure":
            return SimpleNamespace(returncode=1, stdout="simulated failing test", stderr="test failure")
        if not is_pytest and mode == "cli_failure":
            return SimpleNamespace(returncode=2, stdout="", stderr="simulated CLI failure")
        if not is_pytest and mode == "source_change":
            (root / "knowledge_delta" / "base.py").write_text("# changed\n", encoding="utf-8")
        output = "." if is_pytest else json.dumps({"kind": "foundation_cli_verification", "result": "passed"})
        if not is_pytest and mode == "bad_cli":
            output = '{"result":"failed"}'
        return SimpleNamespace(returncode=0, stdout=output, stderr="")
    return run


@pytest.mark.parametrize("mode", [
    "failure", "timeout", "dependency_error", "source_change",
    "collection_only", "missing_junit", "bad_cli", "junit_failure", "cli_failure",
])
def test_unsuccessful_attempt_replaces_stale_success(sample_project, monkeypatch, mode):
    evidence = sample_project / "evidence"
    evidence.mkdir()
    (evidence / "checks.json").write_text('{"result":"passed","run_id":"previous"}', encoding="utf-8")
    for name in ("cli.json", "source-manifest.json", "pytest.xml"):
        (evidence / name).write_text("stale artifact", encoding="utf-8")
    monkeypatch.setattr(run_checks.subprocess, "run", fake_commands(sample_project, mode))
    if mode == "dependency_error":
        def invalid_sources(root):
            raise ValueError("simulated dependency hash mismatch")
        monkeypatch.setattr(run_checks, "source_dependencies", invalid_sources)
    code, result = run_checks.verification(sample_project, Path("evidence"), mode == "dependency_error")
    saved = json.loads((evidence / "checks.json").read_text(encoding="utf-8"))
    assert code != 0
    assert saved["result"] in ("failed", "error")
    assert saved["run_id"] == result["run_id"] != "previous"
    assert not (evidence / "source-manifest.json").exists()
    if mode in ("failure", "timeout", "dependency_error"):
        assert not (evidence / "cli.json").exists()
    if mode == "timeout":
        assert saved["commands"][0]["result"] == "timeout"
        assert saved["commands"][0]["stdout"] == "partial"
    if mode == "failure":
        assert saved["commands"][0]["returncode"] == 1


def test_inherited_collection_and_plugin_settings_are_ignored(sample_project, monkeypatch):
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONOPTIMIZE", "PYTHONINSPECT"):
        monkeypatch.setenv(key, "--collect-only")
    seen = []
    monkeypatch.setattr(run_checks.subprocess, "run", fake_commands(sample_project, "success", seen))
    code, result = run_checks.verification(sample_project, Path("evidence"))
    assert code == 0 and result["result"] == "passed"
    assert result["junit"]["executed"] == 1
    for args, env in seen:
        assert all(key not in env for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONOPTIMIZE", "PYTHONINSPECT"))
    assert str(sample_project / "tests") in seen[0][0]
    assert "-c" in seen[0][0]


@pytest.mark.parametrize("directory", ["tests/evidence", "examples/results", "scripts/logs", "knowledge_delta/results"])
def test_evidence_cannot_modify_hashed_source_directories(sample_project, directory):
    with pytest.raises(ValueError, match="hashed source"):
        run_checks.verification(sample_project, Path(directory))
    assert not (sample_project / directory).exists()


def test_packaging_copy_must_match_recorded_hash(sample_project):
    vendor = sample_project / ".tools" / "vendor"
    package = vendor / "pip-vendor" / "packaging"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"tampered")
    pins = {}
    for name in ("pytest", "pluggy", "iniconfig", "colorama", "pygments"):
        pins[name] = {"name": name, "release_tag": "test", "commit": "test",
                      "files": [], "generated_files": []}
    pins["packaging"] = {"version": "test", "method": "constructed fixture", "files": [{
        "path": "packaging/__init__.py", "sha256": hashlib.sha256(b"expected").hexdigest()}]}
    (sample_project / "tests" / "dependency-sources.json").write_text(json.dumps(pins), encoding="utf-8")
    with pytest.raises(ValueError, match="Packaging source hash mismatch"):
        run_checks.source_dependencies(sample_project)


@pytest.mark.parametrize("body", [
    "<unexpected><testcase/></unexpected>",
    "<testsuite tests='1' errors='1'><testcase/></testsuite>",
    "<testsuite tests='80'><testcase/></testsuite>",
    "<testsuite skipped='1'><testcase/></testsuite>",
    "<testsuite><testcase/><error/></testsuite>",
    "<testsuite tests='-1'><testcase/></testsuite>",
])
def test_junit_cannot_hide_errors_or_invent_test_counts(tmp_path, body):
    path = tmp_path / "constructed.xml"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError):
        run_checks.junit_summary(path)


def test_nested_junit_counts_are_not_double_counted(tmp_path):
    path = tmp_path / "constructed.xml"
    path.write_text("<testsuites tests='2'><testsuite tests='2'><testcase/><testsuite tests='1'><testcase/></testsuite></testsuite></testsuites>", encoding="utf-8")
    assert run_checks.junit_summary(path)["executed"] == 2


def test_second_writer_is_rejected_without_touching_active_evidence(sample_project, monkeypatch):
    evidence = run_checks.evidence_directory(sample_project, Path("evidence"))
    state = evidence / "checks.json"
    state.write_text('{"result":"running","run_id":"owner"}', encoding="utf-8")
    monkeypatch.setattr(run_checks.subprocess, "run", fake_commands(sample_project, "success"))
    with run_checks.evidence_lock(sample_project, evidence):
        with pytest.raises(ValueError, match="locked"):
            run_checks.verification(sample_project, Path("evidence"))
        assert json.loads(state.read_text(encoding="utf-8"))["run_id"] == "owner"
    # An existing lock file alone does not block a run once its OS handle closes.
    code, result = run_checks.verification(sample_project, Path("evidence"))
    assert code == 0 and result["result"] == "passed"


def test_related_status_fixture_cases_cannot_cross_splits():
    from knowledge_delta.cases import validate_dataset
    from knowledge_delta.snapshots import load_snapshot
    example = Path(__file__).resolve().parents[1] / "examples" / "constructed"
    cases = json.loads((example / "cases.json").read_text(encoding="utf-8"))
    selected = {case["case_id"]: case for case in cases["cases"]}
    assert selected["status-unrelated"]["family_id"] == selected["old-version"]["family_id"]
    selected["old-version"]["split"] = "held_out"
    before = load_snapshot(example / "before" / "manifest.json")
    after = load_snapshot(example / "after" / "manifest.json")
    with pytest.raises(ValidationError, match="crosses development and held-out"):
        validate_dataset(cases, before, after)
