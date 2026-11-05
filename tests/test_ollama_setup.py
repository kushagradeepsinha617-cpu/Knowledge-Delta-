"""Portable runtime preparation contracts with inert ZIPs; no native execution."""
from hashlib import sha256
from io import BytesIO
import json
import zipfile

import pytest

from scripts import setup_ollama_runtime as runtime
from scripts.inspect_embedding_setup import Ledger, cpu_dependency_reserved


def archive(entries=None):
    entries = entries or {"ollama.exe": b"TEST ONLY inert binary", "lib/ollama/test.dll": b"TEST ONLY"}
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        for name, body in entries.items():
            zipped.writestr(name, body)
    data = stream.getvalue()
    return data, {"compressed_bytes": len(data), "declared_expanded_bytes": sum(map(len, entries.values())),
                  "sha256": sha256(data).hexdigest()}


def test_default_runtime_plan_does_not_download_or_execute(monkeypatch, capsys):
    monkeypatch.setattr(runtime, "prepare", lambda *a: pytest.fail("Explicit --prepare required"))
    assert runtime.main([]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["network_requests"] == 0
    assert value["server_started"] is False
    assert value["model_weights_downloaded"] is False


@pytest.mark.parametrize("url", ["http://github.com/file", "https://example.com/file",
                                 "https://user:secret@github.com/file"])
def test_runtime_redirects_reject_unapproved_transport_or_hosts(url):
    with pytest.raises(runtime.SetupError):
        runtime.validate_url(url)


def test_runtime_payload_uses_global_allowance_without_consuming_embedding_subbudget(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.reserve(1_000_000_000, "previous-cpu-dependencies")
    runtime.RuntimeBudget(ledger).reserve(123, "test-runtime-payload")
    assert cpu_dependency_reserved(ledger) == 1_000_000_000
    assert Ledger(ledger.path).total == 1_000_000_123


def test_runtime_extraction_uses_one_owned_copy_and_preserves_exact_bytes(tmp_path):
    body, package = archive()
    source, target = tmp_path / "runtime.zip", tmp_path / "runtime"
    source.write_bytes(body)
    runtime.extract(source, package, target)
    assert (target / "ollama.exe").read_bytes() == b"TEST ONLY inert binary"
    assert (target / "lib/ollama/test.dll").read_bytes() == b"TEST ONLY"
    with pytest.raises(runtime.SetupError, match="already exists"):
        runtime.extract(source, package, target)


def test_runtime_path_traversal_fails_before_any_extraction(tmp_path):
    body, package = archive({"../escape.exe": b"bad"})
    source, target = tmp_path / "runtime.zip", tmp_path / "runtime"
    source.write_bytes(body)
    with pytest.raises(runtime.SetupError, match="Unsafe"):
        runtime.extract(source, package, target)
    assert not target.exists()
    assert not (tmp_path / "escape.exe").exists()


def test_runtime_directory_metadata_uses_explicit_global_reservation_scope(tmp_path):
    from scripts.inspect_embedding_setup import Reader
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.reserve(1_000_000_000, "previous-cpu-dependencies")
    class Response:
        status = 206
        headers = {"Content-Length": "4", "Content-Range": "bytes 0-3/100"}
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def read(self, amount):
            return b"test"
    class Opener:
        def open(self, *a, **k):
            return Response()
    reader = Reader(runtime.URL, ledger, Opener(),
                    reserve=lambda l,n,label: runtime.RuntimeBudget(l).reserve(n,label))
    assert reader.request(runtime.URL, limit=4, byte_range=(0,3,100)) == b"test"
    assert ledger.total == 1_000_000_005
    assert cpu_dependency_reserved(ledger) == 1_000_000_000
