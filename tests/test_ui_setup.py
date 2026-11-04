"""Approved-installer contracts with inert synthetic wheels and process doubles.

No network, pip installation, model download or real native process is executed.
"""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import zipfile

import pytest

from scripts import setup_ui as setup

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    work = tmp_path / ".tools/ui-setup"
    work.mkdir(parents=True)
    return tmp_path, work


def wheel(name="demo/__init__.py", content=b"# TEST-ONLY inert source\n"):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)
    body = output.getvalue()
    if "\\" in name:
        # Windows ZipInfo normalizes backslashes while writing; explicitly place
        # the unsafe original name into both synthetic ZIP headers instead.
        body = body.replace(name.replace("\\", "/").encode(), name.encode())
    package = {"name": "demo", "version": "1.0", "filename": "demo-1.0-py3-none-any.whl",
        "url": "https://files.pythonhosted.org/test-only/demo-1.0-py3-none-any.whl",
        "compressed_bytes": len(body), "declared_expanded_bytes": len(content), "sha256": sha256(body).hexdigest()}
    return body, package


class Response:
    def __init__(self, body, package, ledger, fail_read=None):
        self.status = 200
        self.headers = {"Content-Length": str(package["compressed_bytes"])}
        self.body, self.ledger, self.fail_read = body, ledger, fail_read
        self.position = self.reads = self.requested = 0
        self.base = ledger.data["reserved_bytes"]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, amount):
        self.reads += 1
        self.requested += amount
        persisted = json.loads(self.ledger.path.read_text())
        assert persisted["reserved_bytes"] == self.base + self.requested, "Persist reservations BEFORE reads"
        if self.reads == self.fail_read:
            raise OSError("TEST-ONLY interrupted transfer")
        value = self.body[self.position:self.position + amount]
        self.position += len(value)
        return value


def opener(response):
    return SimpleNamespace(open=lambda request, timeout: response)


def test_plan_uses_approved34_lock_without_network_or_writes(project, monkeypatch):
    root, work = project
    metadata = root / "docs/readiness"
    metadata.mkdir(parents=True)
    for filename in ("ui-wheel-candidates.json", "requirements-ui.lock.txt"):
        shutil.copyfile(ROOT / "docs/readiness" / filename, metadata / filename)
    monkeypatch.setattr(setup, "runtime_check", lambda root: None)
    monkeypatch.setattr(setup, "installed_version", lambda package, root: None)
    def forbidden(*args):
        raise AssertionError("A plan must never open the network")
    monkeypatch.setattr(setup.urllib.request, "build_opener", forbidden)
    before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    packages, report = setup.plan(root)
    assert len(packages) == report["pending_packages"] == 34
    assert report["conservative_planning_bytes"] < setup.FOLDER_LIMIT
    assert report["network_requests_performed"] is report["packages_installed_by_this_plan"] is False
    assert before == sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    lock = metadata / "requirements-ui.lock.txt"
    lock.write_text(lock.read_text().replace("--hash=sha256:", "--hash=sha256:0", 1))
    with pytest.raises(setup.SetupError, match="unsupported|mismatch"):
        setup.load_packages(root)


def test_download_persists_every_read_reservation_and_reuses_verified_wheel(project):
    root, work = project
    body, package = wheel()
    ledger = setup.DownloadLedger(work)
    response = Response(body, package, ledger)
    path = setup.download_wheel(package, root, work, ledger, opener(response))
    assert path.read_bytes() == body
    assert setup.DownloadLedger(work).data["reserved_bytes"] == len(body) + 1
    forbidden = SimpleNamespace(open=lambda *args, **kwargs: pytest.fail("Verified staged wheels need no redownload"))
    assert setup.download_wheel(package, root, work, ledger, forbidden) == path
    assert ledger.data["reserved_bytes"] == len(body) + 1
    assert not list(work.glob("*.part"))


def test_interruption_and_retry_never_refund_or_reset_payload_ledger(project, monkeypatch):
    root, work = project
    body, package = wheel()
    monkeypatch.setattr(setup, "CHUNK", 16)
    ledger = setup.DownloadLedger(work)
    with pytest.raises(OSError, match="interrupted"):
        setup.download_wheel(package, root, work, ledger, opener(Response(body, package, ledger, fail_read=2)))
    assert ledger.data["reserved_bytes"] == 32 and not list(work.glob("*.part"))
    ledger = setup.DownloadLedger(work)
    setup.download_wheel(package, root, work, ledger, opener(Response(body, package, ledger)))
    assert ledger.data["reserved_bytes"] == 32 + len(body) + 1


def test_exhausted_budget_stops_before_response_read_and_preserves_prior_files(project):
    root, work = project
    body, package = wheel()
    ledger = setup.DownloadLedger(work)
    ledger.reserve(setup.DOWNLOAD_LIMIT - 5, "TEST-ONLY prior reservations")
    response = Response(body, package, ledger)
    other = work / "user-preserved.txt"
    other.write_bytes(b"preserve")
    with pytest.raises(setup.SetupError, match="allowance"):
        setup.download_wheel(package, root, work, ledger, opener(response))
    assert response.reads == 0 and other.read_bytes() == b"preserve"
    assert setup.DownloadLedger(work).data["reserved_bytes"] == setup.DOWNLOAD_LIMIT - 5


@pytest.mark.parametrize("bad_entries", [[{"bytes": -1, "filename": "x"}, {"bytes": 2, "filename": "x"}],
    [{"bytes": True, "filename": "x"}], [{"bytes": 1, "filename": None}]])
def test_invalid_ledger_entries_cannot_hide_consumed_budget(project, bad_entries):
    root, work = project
    data = {"schema_version": 1, "ceiling_bytes": setup.DOWNLOAD_LIMIT, "reserved_bytes": 1, "reservations": bad_entries}
    (work / "download-ledger.json").write_text(json.dumps(data))
    with pytest.raises(setup.SetupError, match="ledger"):
        setup.DownloadLedger(work)


@pytest.mark.parametrize("name", ["../escape.py", "demo\\escape.py", "demo/CON.txt", "demo/file. ", "demo/./same.py"])
def test_full_hash_does_not_override_unsafe_zip_entry_rejection(project, name):
    root, work = project
    body, package = wheel(name)
    path = work / package["filename"]
    path.write_bytes(body)
    with pytest.raises(setup.SetupError, match="Unsafe"):
        setup.verify_wheel(path, package)


def test_size_hash_and_expanded_manifest_mismatch_are_rejected(project):
    root, work = project
    body, package = wheel()
    path = work / package["filename"]
    path.write_bytes(body)
    wrong = dict(package, sha256="0" * 64)
    with pytest.raises(setup.SetupError, match="SHA256"):
        setup.verify_wheel(path, wrong)
    with pytest.raises(setup.SetupError, match="expanded"):
        setup.verify_wheel(path, dict(package, declared_expanded_bytes=1))


def test_child_environment_and_pip_command_are_local_offline_and_hash_locked(project, monkeypatch):
    root, work = project
    body, package = wheel()
    path = work / package["filename"]
    path.write_bytes(body)
    monkeypatch.setenv("PIP_TARGET", "C:/TEST-ONLY-global-target")
    monkeypatch.setenv("PYTHONPATH", "C:/TEST-ONLY-outside")
    env = setup.child_environment(root, work)
    assert "PIP_TARGET" not in env and "PYTHONPATH" not in env
    assert env["PIP_CONFIG_FILE"] == setup.os.devnull
    for name in ("USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "PIP_CACHE_DIR"):
        assert Path(env[name]).resolve().is_relative_to(root)
    commands = []
    monkeypatch.setattr(setup, "monitored_process", lambda command, *args: commands.append(command))
    setup.install_wheel(package, path, root, work, work / setup.PIP_NAME, env)
    command = commands[0]
    for flag in ("-I", "-B", "--isolated", "--no-index", "--no-deps", "--no-compile", "--require-hashes", "--only-binary=:all:"):
        assert flag in command
    requirement = (work / "current-wheel.txt").read_text()
    assert path.as_uri() in requirement and "--hash=sha256:" + package["sha256"] in requirement
    assert setup.os.environ["PIP_TARGET"] == "C:/TEST-ONLY-global-target"


def test_existing_local_bundled_pip_is_copied_and_verified_without_installing(project, monkeypatch):
    root, work = project
    fake = root / "base-python/ensurepip"
    source = fake / "_bundled" / setup.PIP_NAME
    source.parent.mkdir(parents=True)
    source.write_bytes(b"TEST-ONLY local bootstrap bytes")
    monkeypatch.setattr(setup.ensurepip, "__file__", str(fake / "__init__.py"))
    monkeypatch.setattr(setup, "PIP_SHA256", sha256(source.read_bytes()).hexdigest())
    target = setup.bootstrap_pip(root, work)
    assert target.read_bytes() == source.read_bytes() and target.parent == work
    target.write_bytes(b"changed")
    with pytest.raises(setup.SetupError, match="differs"):
        setup.bootstrap_pip(root, work)


def test_running_pip_is_terminated_when_folder_guard_fails(project, monkeypatch):
    root, work = project
    env = setup.child_environment(root, work)
    class Process:
        returncode = None
        terminated = False
        def poll(self):
            return self.returncode
        def terminate(self):
            self.terminated = True
        def wait(self, timeout):
            self.returncode = -1
    child = Process()
    monkeypatch.setattr(setup.subprocess, "Popen", lambda *args, **kwargs: child)
    checks = []
    def guard(*args, **kwargs):
        checks.append(True)
        if len(checks) > 1:
            raise setup.SetupError("TEST-ONLY folder guard")
    monkeypatch.setattr(setup, "check_space", guard)
    with pytest.raises(setup.SetupError, match="folder guard"):
        setup.monitored_process(["TEST-ONLY-PROCESS"], root, work, env, work / "test-process.log")
    assert child.terminated


def test_default_main_does_not_install_or_write_and_failed_install_reports_partial_state(project, monkeypatch, capsys):
    root, work = project
    monkeypatch.setattr(setup, "ROOT", root)
    monkeypatch.setattr(setup, "plan", lambda root: ([], {"status": "plan_ready"}))
    def failed(root, packages, record):
        record["steps"].append({"name": "TEST-ONLY", "status": "pending"})
        raise setup.SetupError("Injected TEST-ONLY install failure")
    monkeypatch.setattr(setup, "perform_install", failed)
    assert setup.main([]) == 0 and not (root / "runs").exists()
    capsys.readouterr()
    assert setup.main(["--install"]) == 2
    capsys.readouterr()
    report = json.loads(next((root / "runs/ui-setup").glob("*.json")).read_text())
    assert report["status"] == "partial_or_unavailable" and report["steps"][0]["status"] == "pending"
    assert report["models_downloaded"] is report["server_started"] is report["os_quota_enforced"] is False
