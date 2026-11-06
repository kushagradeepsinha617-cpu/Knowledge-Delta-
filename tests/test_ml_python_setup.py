"""Official-runtime setup contracts tested with inert ZIPs only."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

from scripts import setup_ml_python as runtime
from scripts import setup_embeddings as installer
from scripts.inspect_embedding_setup import Ledger


def archive(entries=None):
    entries = entries or {"python.exe": b"INERT TEST DATA", "Lib/venv/__init__.py": b"# inert"}
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        for name, body in entries.items():
            zipped.writestr(name, body)
    data = stream.getvalue()
    return data, {"filename": "python-test-only.zip", "url": runtime.URL,
                  "sha256": sha256(data).hexdigest(), "compressed_bytes": len(data),
                  "declared_expanded_bytes": sum(len(body) for body in entries.values())}


@pytest.mark.parametrize("missing", [None, "python.exe", "Lib/venv/__init__.py", "all"])
def test_cached_python_receipt_cannot_skip_required_runtime_hashes(tmp_path, missing):
    target=tmp_path/'python';(target/'Lib/venv').mkdir(parents=True)
    contents={'python.exe':b'INERT EXE','Lib/venv/__init__.py':b'# TEST ONLY'}
    files={}
    for name,data in contents.items():
        (target/name).write_bytes(data);files[name]=sha256(data).hexdigest()
    if missing=='all': files={}
    elif missing: files.pop(missing)
    receipt={'version':runtime.VERSION,'url':runtime.URL,'archive_sha256':runtime.ARCHIVE_SHA256,'files':files}
    (target/'KNOWLEDGEDELTA_RUNTIME.json').write_text(json.dumps(receipt),encoding='utf-8')
    if missing:
        with pytest.raises(runtime.SetupError): runtime.verify_cached_runtime(tmp_path,target)
    else: assert runtime.verify_cached_runtime(tmp_path,target)==receipt


@pytest.mark.parametrize("fault", ["unrecorded_file", "omitted_library", "invalid_object"])
def test_cached_python_requires_complete_file_inventory(tmp_path, fault):
    target = tmp_path / "python"
    (target / "Lib/venv").mkdir(parents=True)
    contents = {"python.exe": b"INERT", "Lib/venv/__init__.py": b"# TEST ONLY",
                "python314.dll": b"INERT DLL"}
    files = {}
    for name, data in contents.items():
        (target / name).write_bytes(data)
        files[name] = sha256(data).hexdigest()
    if fault == "unrecorded_file":
        (target / "extra.dll").write_bytes(b"INERT EXTRA")
    elif fault == "omitted_library":
        files.pop("python314.dll")
    receipt = {"version": runtime.VERSION, "url": runtime.URL,
               "archive_sha256": runtime.ARCHIVE_SHA256, "files": files}
    if fault == "invalid_object":
        receipt = []
    (target / "KNOWLEDGEDELTA_RUNTIME.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(runtime.SetupError):
        runtime.verify_cached_runtime(tmp_path, target)


def test_runtime_default_is_offline_and_does_not_execute_native_code(monkeypatch, capsys):
    monkeypatch.setattr(runtime, "perform", lambda *a: pytest.fail("Explicit --setup required"))
    assert runtime.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["network_requests"] == 0
    assert result["system_registration_performed"] is False
    assert result["model_weights_downloaded"] is False


def test_runtime_zip_extraction_preserves_exact_bytes_in_fresh_target(tmp_path):
    body, package = archive()
    path, target = tmp_path / "runtime.zip", tmp_path / "python"
    path.write_bytes(body)
    runtime.extract(path, package, target)
    assert (target / "python.exe").read_bytes() == b"INERT TEST DATA"
    assert (target / "Lib/venv/__init__.py").read_bytes() == b"# inert"


def test_unsafe_archive_rejected_before_target_creation(tmp_path):
    body, package = archive({"../escape.txt": b"unsafe"})
    path, target = tmp_path / "runtime.zip", tmp_path / "python"
    path.write_bytes(body)
    with pytest.raises(installer.SetupError, match="Unsafe"):
        runtime.extract(path, package, target)
    assert not target.exists()
    assert not (tmp_path / "escape.txt").exists()


def test_existing_runtime_target_is_preserved(tmp_path):
    body, package = archive()
    path, target = tmp_path / "runtime.zip", tmp_path / "python"
    path.write_bytes(body)
    target.mkdir()
    (target / "user.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(installer.SetupError, match="Preserve"):
        runtime.extract(path, package, target)
    assert list(target.iterdir()) == [target / "user.txt"]


def test_wrong_runtime_hash_never_extracts(tmp_path):
    body, package = archive()
    path, target = tmp_path / "runtime.zip", tmp_path / "python"
    path.write_bytes(body)
    package["sha256"] = "0" * 64
    with pytest.raises(installer.SetupError, match="SHA256"):
        runtime.extract(path, package, target)
    assert not target.exists()


def test_explicit_archive_verifier_download_keeps_cpu_budget(tmp_path):
    body, package = archive()
    work = tmp_path / ".tools/model-setup"
    work.mkdir(parents=True)
    ledger = Ledger(work / "download-ledger.json")
    class Response:
        status = 200
        headers = {"Content-Length": str(len(body))}
        def __init__(self):
            self.position = 0
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, amount):
            data = body[self.position:self.position + amount]
            self.position += len(data)
            return data
    class Opener:
        def open(self, *args, **kwargs):
            return Response()
    path = installer.download(package, tmp_path, work, ledger, Opener(), verifier=installer.verify_wheel)
    assert path.read_bytes() == body
    assert ledger.total == len(body) + 1


def test_model_candidate_metadata_reserves_its_full_response_bound(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    runtime.reserve_model_metadata(ledger)
    assert Ledger(ledger.path).total == 5 * (runtime.MAX_RESPONSE + 1)
    assert ledger.data["reservations"][-1]["label"].startswith("model:")
