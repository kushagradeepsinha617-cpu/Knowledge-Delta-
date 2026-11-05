"""Offline cache importer contracts. Synthetic bytes are not model results."""
from contextlib import nullcontext
from hashlib import sha256
from io import BytesIO
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from scripts import setup_qwen_cache as qwen
from scripts.inspect_embedding_setup import Ledger, Reader, cpu_dependency_reserved


def synthetic_manifest():
    bodies = [b"synthetic config", b"synthetic model"]
    descriptors = [{"digest": "sha256:" + sha256(b).hexdigest(), "size": len(b)} for b in bodies]
    raw = json.dumps({"schemaVersion": 2, "config": descriptors[0], "layers": descriptors[1:]}).encode()
    return raw, descriptors, bodies


def parse_test_manifest(raw, total=31):
    return qwen.manifest_parts(raw, sha256(raw).hexdigest(), total)


def test_default_plan_never_downloads_or_starts_server(monkeypatch, capsys):
    monkeypatch.setattr(qwen, "prepare", lambda *a: pytest.fail("Explicit download required"))
    assert qwen.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["network_requests"] == 0
    assert result["server_started"] is result["inference_performed"] is False


def test_raw_manifest_digest_is_not_reserialized():
    raw, descriptors, bodies = synthetic_manifest()
    assert parse_test_manifest(raw, sum(map(len, bodies))) == descriptors
    with pytest.raises(qwen.SetupError, match="pinned manifest"):
        qwen.manifest_parts(raw + b"\n", sha256(raw).hexdigest(), sum(map(len, bodies)))


@pytest.mark.parametrize("mutation", ["list", "bad_layer", "duplicate", "bool_size", "negative", "digest_type", "bad_digest", "manifest_list", "wrong_total"])
def test_malformed_or_unexpected_manifest_rejected(mutation):
    raw, _, bodies = synthetic_manifest()
    data = json.loads(raw)
    if mutation == "list":
        data = []
    elif mutation == "bad_layer":
        data["layers"] = [None]
    elif mutation == "duplicate":
        data["layers"] = [data["config"]]
    elif mutation == "bool_size":
        data["config"]["size"] = True
    elif mutation == "negative":
        data["config"]["size"] = -1
    elif mutation == "digest_type":
        data["config"]["digest"] = None
    elif mutation == "bad_digest":
        data["config"]["digest"] = "sha256:../escape"
    elif mutation == "manifest_list":
        data["manifests"] = []
    raw = json.dumps(data).encode()
    with pytest.raises(qwen.SetupError):
        parse_test_manifest(raw, sum(map(len, bodies)) + (mutation == "wrong_total"))


@pytest.mark.parametrize("url", ["http://registry.ollama.ai/a", "https://example.com/a", "https://user:secret@ollama.com/a", "https://ollama.com:443/a", "https://registry.ollama.ai.evil.test/a"])
def test_registry_url_boundary(url):
    with pytest.raises(qwen.SetupError):
        qwen.validate_url(url)


def test_blob_reuse_checks_size_and_hash(tmp_path):
    path = tmp_path / "blob"
    path.write_bytes(b"good")
    package = {"compressed_bytes": 4, "sha256": sha256(b"good").hexdigest()}
    qwen.verify_blob(path, package)
    path.write_bytes(b"evil")
    with pytest.raises(qwen.SetupError):
        qwen.verify_blob(path, package)
    path.write_bytes(b"bad")
    with pytest.raises(qwen.SetupError):
        qwen.verify_blob(path, package)


def test_atomic_manifest_preserves_existing_different_file(tmp_path):
    target = tmp_path / "manifest"
    qwen.write_exact(target, b"original")
    qwen.write_exact(target, b"original")
    with pytest.raises(qwen.SetupError):
        qwen.write_exact(target, b"different")
    assert target.read_bytes() == b"original"
    assert list(tmp_path.glob("*.part")) == []


def importer_fixture(tmp_path, monkeypatch, fail_blob=False):
    raw, descriptors, bodies = synthetic_manifest()
    original_parse = qwen.manifest_parts
    monkeypatch.setattr(qwen, "manifest_parts", lambda value: original_parse(value, sha256(raw).hexdigest(), sum(map(len, bodies))))
    monkeypatch.setattr(qwen, "MANIFEST_SHA256", sha256(raw).hexdigest())
    monkeypatch.setattr(qwen, "PAYLOAD_BYTES", sum(map(len, bodies)))
    monkeypatch.setattr(qwen, "stopped_server_guard", nullcontext)
    named = tmp_path / ".tools/models/ollama" / qwen.NAMED_MANIFEST
    responses = {qwen.MANIFEST_URL: raw, **{qwen.BLOB_BASE + p["digest"]: b for p, b in zip(descriptors, bodies)}}
    requests = []
    class Response(BytesIO):
        status = 200
        def __init__(self, data):
            super().__init__(data)
            self.headers = {"Content-Length": str(len(data))}
    class Opener:
        def open(self, request, **kwargs):
            url = request.full_url
            requests.append(url)
            if url != qwen.MANIFEST_URL:
                assert not named.exists(), "Named manifest must be promoted last"
                if fail_blob and url.endswith(descriptors[-1]["digest"]):
                    raise OSError("synthetic interrupted transfer")
            return Response(responses[url])
    monkeypatch.setattr(qwen, "build_opener", lambda *a: Opener())
    ledger_path = tmp_path / ".tools/model-setup/download-ledger.json"
    Ledger(ledger_path).reserve(1, "earlier-model-metadata")
    return raw, descriptors, bodies, requests, named, ledger_path


def test_complete_import_promotes_exact_v2_manifest_last(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("q")
    raw, descriptors, bodies, requests, named, ledger_path = importer_fixture(tmp_path, monkeypatch)
    record = {"blobs": []}
    qwen.prepare(tmp_path, record)
    assert named.read_bytes() == raw
    assert named.relative_to(tmp_path).as_posix() == ".tools/models/ollama/manifests-v2/ollama.com/library/qwen3/1.7b"
    cache = named.parents[4] / "blobs"
    assert (cache / ("sha256-" + sha256(raw).hexdigest())).read_bytes() == raw
    for p, body in zip(descriptors, bodies):
        assert (cache / p["digest"].replace(":", "-")).read_bytes() == body
    ledger = Ledger(ledger_path)
    assert ledger.total == 1 + len(raw) + 1 + sum(len(b) + 1 for b in bodies)
    assert cpu_dependency_reserved(ledger) == 0
    assert record["model_cache_verified"] is True
    assert len(requests) == 3


def test_interruption_never_advertises_partial_model(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("q")
    _, descriptors, _, _, named, ledger_path = importer_fixture(tmp_path, monkeypatch, fail_blob=True)
    record = {"blobs": []}
    with pytest.raises(OSError, match="interrupted"):
        qwen.prepare(tmp_path, record)
    assert not named.exists()
    assert len(record["blobs"]) == 1
    assert record["transfer_reserved_bytes"] == Ledger(ledger_path).total
    assert not record.get("model_cache_verified", False)
    assert list(tmp_path.rglob("*.part")) == []


def test_corrupt_reused_blob_is_preserved_and_stops_import(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("q")
    _, parts, bodies, requests, named, _ = importer_fixture(tmp_path, monkeypatch)
    blob = tmp_path / ".tools/models/ollama/blobs" / parts[0]["digest"].replace(":", "-")
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"x" * len(bodies[0]))
    with pytest.raises(qwen.SetupError, match="SHA256"):
        qwen.prepare(tmp_path, {"blobs": []})
    assert blob.read_bytes() == b"x" * len(bodies[0])
    assert requests == [qwen.MANIFEST_URL]
    assert not named.exists()


def test_existing_different_named_manifest_preserved_before_blob_transfer(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("q")
    _, _, _, requests, named, _ = importer_fixture(tmp_path, monkeypatch)
    named.parent.mkdir(parents=True)
    named.write_bytes(b"preserve")
    with pytest.raises(qwen.SetupError, match="preserve"):
        qwen.prepare(tmp_path, {"blobs": []})
    assert named.read_bytes() == b"preserve"
    assert requests == [qwen.MANIFEST_URL]


def test_insufficient_remaining_payload_budget_stops_before_blobs(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("q")
    raw, _, _, requests, named, ledger_path = importer_fixture(tmp_path, monkeypatch)
    Ledger(ledger_path).reserve(5_000_000_000 - 1 - len(raw) - 1 - 1, "model:earlier-transfer")
    with pytest.raises(qwen.SetupError, match="allowance"):
        qwen.prepare(tmp_path, {"blobs": []})
    assert requests == [qwen.MANIFEST_URL]
    assert not named.exists()


def test_stopped_guard_holds_exclusive_bind_until_exit(monkeypatch):
    events = []
    class Socket:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            events.append("closed")
        def setsockopt(self, *a):
            assert a[-1] == 1
            events.append("exclusive")
        def bind(self, address):
            assert address == ("127.0.0.1", 11434)
            events.append("bound")
    monkeypatch.setattr(qwen.socket, "socket", lambda *a: Socket())
    monkeypatch.setattr(qwen.socket, "SO_EXCLUSIVEADDRUSE", 1234, raising=False)
    with qwen.stopped_server_guard():
        assert events == ["exclusive", "bound"]
    assert events == ["exclusive", "bound", "closed"]


def test_manifest_reader_does_not_relax_cpu_wheel_guard(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    Reader(qwen.MANIFEST_URL, ledger).validate_url(qwen.MANIFEST_URL, head=True)
    with pytest.raises(ValueError, match="Full CPU wheel"):
        Reader(qwen.MANIFEST_URL, ledger).validate_url(qwen.MANIFEST_URL)
    qwen.ManifestReader(qwen.MANIFEST_URL, ledger).validate_url(qwen.MANIFEST_URL)
    with pytest.raises(qwen.SetupError):
        qwen.ManifestReader(qwen.MANIFEST_URL, ledger).validate_url(qwen.BLOB_BASE + "anything")


def test_model_scope_uses_global_cap_and_persists_reservation(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.reserve(1_000_000_000, "cpu-dependencies")
    qwen.ModelBudget(ledger).reserve(3_999_999_999, "synthetic-model")
    assert cpu_dependency_reserved(ledger) == 1_000_000_000
    with pytest.raises(ValueError, match="exhausted"):
        qwen.ModelBudget(ledger).reserve(2, "over-limit")
    assert Ledger(ledger.path).total == 4_999_999_999


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_redirect_bodies_are_closed_without_unaccounted_reads(code):
    class Body:
        closed = False
        def read(self, *a):
            pytest.fail("Redirect body must never be consumed")
        def close(self):
            self.closed = True
    body = Body()
    handler = qwen.RegistryRedirects()
    class Parent:
        def open(self, request, **kwargs):
            assert body.closed
            assert request.full_url == "https://bucket.r2.cloudflarestorage.com/blob"
            return "synthetic response"
    handler.parent = Parent()
    req = Request(qwen.MANIFEST_URL)
    req.timeout = 1
    follow = getattr(handler, "http_error_" + str(code))
    assert follow(req, body, code, "redirect", {"location": "https://bucket.r2.cloudflarestorage.com/blob"}) == "synthetic response"


def test_redirect_loop_and_host_limits_remain_effective():
    class Body(BytesIO):
        def read(self, *a):
            pytest.fail("No redirect-body read")
    handler = qwen.RegistryRedirects()
    req = Request(qwen.MANIFEST_URL)
    req.timeout = 1
    req.redirect_dict = {qwen.MANIFEST_URL: handler.max_repeats}
    with pytest.raises(HTTPError):
        handler.http_error_302(req, Body(), 302, "loop", {"location": qwen.MANIFEST_URL})
    with pytest.raises(qwen.SetupError):
        handler.http_error_302(req, Body(), 302, "unsafe", {"location": "https://evil.test/blob"})
