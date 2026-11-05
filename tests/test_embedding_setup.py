"""CPU installer tests use inert synthetic wheels and HTTP doubles, never pip."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

from scripts import setup_embeddings as setup
from scripts.inspect_embedding_setup import Ledger
from knowledge_delta.validation import ValidationError


def wheel(name="torch", version="2.15.0+cpu", url=None):
    metadata = f"Name: {name}\nVersion: {version}\nRequires-Python: >=3.11\n\n".encode()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{name}-{version}.dist-info/METADATA", metadata)
        archive.writestr(name + "/inert.txt", b"TEST ONLY; never executed")
    data = buffer.getvalue()
    filename = f"{name}-{version}-py3-none-any.whl"
    return data, {"name": name.replace("_", "-"), "version": version, "filename": filename,
                  "url": url or "https://download-r2.pytorch.org/whl/cpu/" + filename,
                  "compressed_bytes": len(data), "declared_expanded_bytes": len(metadata) + len(b"TEST ONLY; never executed"),
                  "archive": {"declared_expanded_bytes": len(metadata) + len(b"TEST ONLY; never executed")},
                  "sha256": sha256(data).hexdigest(), "metadata_sha256": sha256(metadata).hexdigest(),
                  "requires_python": ">=3.11", "requires_dist": []}


def inspection():
    _, torch = wheel()
    _, numpy = wheel("numpy", "2.5.4")
    _, sentence = wheel("sentence_transformers", "6.2.0")
    for p in (numpy, sentence):
        p["url"] = "https://files.pythonhosted.org/test-only/" + p["filename"]
    return {"kind": "cpu_embedding_dependency_inspection", "status": "dependency_metadata_inspected",
            "dependency_closure_metadata_verified": True,
            "roots": ["torch==2.15.0+cpu", "numpy==2.5.4", "sentence-transformers==6.2.0"],
            "packages": [torch, numpy, sentence]}


def test_validated_closure_does_not_accept_host_substitution_or_gpu_wheel():
    report = inspection()
    assert len(setup.validate_packages(report)) == 3
    report["packages"][0]["url"] = "https://example.com/" + report["packages"][0]["filename"]
    with pytest.raises(setup.SetupError, match="identity/URL"):
        setup.validate_packages(report)
    report = inspection()
    report["packages"][0]["requires_dist"] = ["numpy<2"]
    with pytest.raises(setup.SetupError, match="closure mismatch"):
        setup.validate_packages(report)


def test_full_wheel_metadata_must_match_dependency_preflight(tmp_path):
    body, package = wheel()
    path = tmp_path / package["filename"]
    path.write_bytes(body)
    setup.verify_package(path, package)
    package["metadata_sha256"] = "0" * 64
    with pytest.raises(setup.SetupError, match="METADATA differs"):
        setup.verify_package(path, package)


def test_cpu_payload_ceiling_counts_prior_metadata_and_retries(tmp_path):
    ledger = Ledger(tmp_path / "download-ledger.json", previous=100)
    ledger.reserve(setup.CPU_LIMIT - 10, "earlier-cpu-metadata")
    budget = setup.DependencyBudget(ledger)
    budget.reserve(10, "first-transfer")
    with pytest.raises(setup.SetupError, match="1 GB"):
        budget.reserve(1, "retry")
    assert ledger.total == setup.CPU_LIMIT + 100


def test_default_plan_never_invokes_install(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "plan", lambda *a: ([], {"status": "plan_ready", "network_requests_performed": False}))
    monkeypatch.setattr(setup, "install", lambda *a: pytest.fail("Explicit --install required"))
    assert setup.main([]) == 0
    assert json.loads(capsys.readouterr().out)["network_requests_performed"] is False
    assert list(tmp_path.iterdir()) == []


def test_interrupted_download_preserves_reservation_and_removes_only_its_partial(tmp_path):
    body, package = wheel()
    root, work = tmp_path, tmp_path / ".tools/model-setup"
    work.mkdir(parents=True)
    preserved = work / "user-work.txt"
    preserved.write_text("preserve", encoding="utf-8")
    ledger = Ledger(work / "download-ledger.json")
    class Response:
        status = 200
        headers = {"Content-Length": str(len(body))}
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def read(self, amount):
            assert Ledger(ledger.path).total >= amount
            raise OSError("TEST ONLY interrupted response")
    class Opener:
        def open(self, *a, **k):
            return Response()
    with pytest.raises(OSError, match="interrupted"):
        setup.download(package, root, work, ledger, Opener())
    assert ledger.total == len(body)
    assert not list(work.glob("*.part"))
    assert preserved.read_text(encoding="utf-8") == "preserve"


def test_download_requires_exact_response_length_before_read(tmp_path):
    body, package = wheel()
    work = tmp_path / ".tools/model-setup"
    work.mkdir(parents=True)
    ledger = Ledger(work / "download-ledger.json")
    class Response:
        status = 200
        headers = {"Content-Length": "1"}
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def read(self, *a):
            pytest.fail("Bad response headers must be rejected before body")
    class Opener:
        def open(self, *a, **k):
            return Response()
    with pytest.raises(setup.SetupError, match="differs"):
        setup.download(package, tmp_path, work, ledger, Opener())
    assert ledger.total == 0


def test_vendored_distribution_metadata_does_not_look_like_a_duplicate_wheel_root(tmp_path):
    metadata = b"Name: setuptools\nVersion: 84.2.1\nRequires-Python: >=3.11\n\n"
    vendor = b"Name: packaging\nVersion: 26.3\n\n"
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("setuptools-84.2.1.dist-info/METADATA", metadata)
        archive.writestr("setuptools/_vendor/packaging-26.3.dist-info/METADATA", vendor)
    data = output.getvalue()
    path = tmp_path / "setuptools-test-only.whl"
    path.write_bytes(data)
    package = {"name": "setuptools", "version": "84.2.1",
               "compressed_bytes": len(data), "declared_expanded_bytes": len(metadata) + len(vendor),
               "sha256": sha256(data).hexdigest(), "metadata_sha256": sha256(metadata).hexdigest(),
               "requires_dist": [], "requires_python": ">=3.11"}
    setup.verify_package(path, package)


def test_multiple_top_level_wheel_metadata_roots_remain_invalid(tmp_path):
    metadata = b"Name: demo\nVersion: 1.0\n\n"
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("demo-1.0.dist-info/METADATA", metadata)
        archive.writestr("other-1.0.dist-info/METADATA", metadata)
    data = output.getvalue()
    path = tmp_path / "invalid-test-only.whl"
    path.write_bytes(data)
    package = {"compressed_bytes": len(data), "declared_expanded_bytes": 2 * len(metadata),
               "sha256": sha256(data).hexdigest(), "metadata_sha256": sha256(metadata).hexdigest()}
    with pytest.raises(setup.SetupError, match="METADATA missing"):
        setup.verify_package(path, package)


def test_failed_download_report_keeps_latest_persistent_reservation(monkeypatch, tmp_path):
    work = tmp_path / ".tools/model-setup"
    work.mkdir(parents=True)
    monkeypatch.setattr(setup, "bootstrap_pip", lambda *a: work / "test-only-pip.whl")
    monkeypatch.setattr(setup, "child_environment", lambda *a: {})
    monkeypatch.setattr(setup, "existing_version", lambda *a: None)
    monkeypatch.setattr(setup, "check_space", lambda *a: 0)
    def interrupted(package, root, work, ledger):
        ledger.reserve(17, "TEST ONLY failed payload")
        raise OSError("TEST ONLY interrupted")
    monkeypatch.setattr(setup, "download", interrupted)
    record = {"steps": []}
    with pytest.raises(OSError, match="interrupted"):
        setup.install(tmp_path, [{"name": "demo", "version": "1", "compressed_bytes": 100,
                                  "declared_expanded_bytes": 100}], record)
    assert record["transfer_reserved_bytes"] == 17
    assert Ledger(work / "download-ledger.json").total == 17
