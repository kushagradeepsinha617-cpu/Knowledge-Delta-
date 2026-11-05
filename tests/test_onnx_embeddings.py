"""Offline ONNX adapter and downloader contracts; no model weights or ML services."""
from hashlib import sha1, sha256
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_delta import onnx_embeddings as model
from knowledge_delta.validation import ValidationError
from scripts import setup_minilm_onnx as setup
from scripts.inspect_embedding_setup import Ledger


def test_attention_pooling_ignores_padding_and_normalizes_all_attended_tokens():
    result = model.mean_pool_normalize([[1., 2.], [3., 4.], [999., -999.]], [1, 1, 0], dimension=2)
    assert result == pytest.approx([2 / math.sqrt(13), 3 / math.sqrt(13)])
    assert model.mean_pool_normalize([[2., 3.]], [1], dimension=2) == pytest.approx(result)


@pytest.mark.parametrize("vectors,mask", [
    ([], []), ([[1., 2.]], [0]), ([[0., 0.]], [1]), ([[float("nan"), 1.]], [1]),
    ([[1., float("inf")]], [1]), ([[1.]], [1]), ([[1., 2.]], [True]),
    ([[1., 2.]], [2]), ([[1., 2.]], [])])
def test_invalid_numerical_inputs_never_become_dummy_embeddings(vectors, mask):
    with pytest.raises(ValidationError):
        model.mean_pool_normalize(vectors, mask, dimension=2)


def test_raw_tokenizer_disables_serialized_padding_and_truncation():
    class TokenizerDouble:
        def __init__(self):
            self.disabled = []
        def no_truncation(self):
            self.disabled.append("truncate")
        def no_padding(self):
            self.disabled.append("pad")
        def encode(self, text, add_special_tokens):
            return SimpleNamespace(ids=[1, 2] if add_special_tokens else [1],
                                   offsets=[(0, len(text))])
    raw = TokenizerDouble()
    tokenizer = model.OnnxTokenizer(raw, "TEST ONLY")
    assert raw.disabled == ["truncate", "pad"]
    assert tokenizer.count("café") == 2
    assert tokenizer.offsets("café") == [(0, 4)]


def test_overlength_rejected_before_native_session_is_called():
    instance = model.LocalOnnxMiniLM.__new__(model.LocalOnnxMiniLM)
    instance.token_limit = 256
    instance._pad_id = 0
    instance.tokenizer = SimpleNamespace(_tokenizer=SimpleNamespace(
        encode=lambda *a, **k: SimpleNamespace(ids=list(range(257)), type_ids=[0] * 257)))
    with pytest.raises(ValidationError, match="truncation is disabled"):
        instance.encode(["TEST ONLY long text"])


def test_exact_small_asset_git_blob_pin_and_corruption_detection(tmp_path):
    directory = tmp_path / "model"
    directory.mkdir()
    body = b"TEST ONLY inert config"
    path = directory / "config.json"
    path.write_bytes(body)
    identity = sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
    pins = {"config.json": (len(body), "git_blob_sha1", identity)}
    _, hashes = model.inspect_assets(directory, tmp_path, pins=pins)
    assert hashes["config.json"] == sha256(body).hexdigest()
    path.write_bytes(b"x" * len(body))
    with pytest.raises(ValidationError, match="digest mismatch"):
        model.inspect_assets(directory, tmp_path, pins=pins)


def test_asset_directory_cannot_escape_project(tmp_path):
    with pytest.raises(ValidationError, match="inside the project"):
        model.inspect_assets(tmp_path.parent, tmp_path, pins={})


@pytest.mark.parametrize("url", ["http://huggingface.co/model", "https://example.com/model",
                                  "https://u:p@huggingface.co/model", "https://huggingface.co:443/model"])
def test_download_redirect_must_stay_on_approved_public_https_hosts(url):
    with pytest.raises(setup.SetupError):
        setup.validate_url(url)


def test_explicit_download_flag_required_and_default_does_not_import_models(monkeypatch, capsys):
    monkeypatch.setattr(setup, "perform", lambda *a: pytest.fail("No default download"))
    assert setup.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["network_requests"] == 0
    assert result["download_performed"] is False
    assert "model.safetensors" not in result["files"]
    assert model.ASSETS["onnx/model.onnx"][0] == 90_405_214


class Response:
    status = 200
    def __init__(self, data):
        self.data = data
        self.position = 0
        self.headers = {"Content-Length": str(len(data))}
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass
    def geturl(self):
        return setup.BASE + "test-only.txt"
    def read(self, amount):
        result = self.data[self.position:self.position + amount]
        self.position += len(result)
        return result


class Opener:
    def __init__(self, body):
        self.body, self.calls = body, 0
    def open(self, *a, **k):
        self.calls += 1
        return Response(self.body)


def test_verified_download_cached_and_only_real_payload_charged(tmp_path):
    directory = tmp_path / "model"
    ledger = Ledger(tmp_path / "ledger.json")
    body = b"TEST ONLY"
    pin = (len(body), "sha256", sha256(body).hexdigest())
    opener, record = Opener(body), {}
    result = setup.fetch_asset("test-only.txt", pin, directory, tmp_path, ledger, record, opener)
    assert result["status"] == "downloaded_verified"
    assert ledger.total == len(body) + 1
    assert setup.fetch_asset("test-only.txt", pin, directory, tmp_path, ledger, record, opener)["status"] == "existing_verified"
    assert opener.calls == 1


def test_corrupt_asset_is_not_promoted_and_reservation_is_preserved(tmp_path):
    directory = tmp_path / "model"
    directory.mkdir()
    keep = directory / "user-work.txt"
    keep.write_text("preserve", encoding="utf-8")
    ledger = Ledger(tmp_path / "ledger.json")
    pin = (3, "sha256", sha256(b"yes").hexdigest())
    with pytest.raises(ValidationError, match="digest mismatch"):
        setup.fetch_asset("test-only.txt", pin, directory, tmp_path, ledger, {}, Opener(b"bad"))
    assert not (directory / "test-only.txt").exists()
    assert not list(directory.glob("*.part"))
    assert ledger.total == 4
    assert keep.read_text(encoding="utf-8") == "preserve"


def test_download_rejects_wrong_current_environment_before_import_or_network(monkeypatch, tmp_path):
    monkeypatch.setattr(setup.sys, "prefix", str(tmp_path / "wrong-env"))
    with pytest.raises(setup.SetupError, match="project .venv-ml"):
        setup.runtime_ready({"status": "onnx_runtime_imports_verified_model_not_tested"}, tmp_path)


def test_backend_specific_run_error_is_translated_to_pipeline_runtime_error():
    class OnnxFailure(Exception):
        pass
    instance = model.LocalOnnxMiniLM.__new__(model.LocalOnnxMiniLM)
    instance.token_limit = 256
    instance.tokenizer = SimpleNamespace(_tokenizer=SimpleNamespace(
        encode=lambda *a, **k: SimpleNamespace(ids=[101, 102], type_ids=[0, 0])))
    instance._pad_id = 0
    instance._np = SimpleNamespace(int64="TEST ONLY", asarray=lambda v, **k: v)
    instance._input_names = ("input_ids", "attention_mask")
    def failure(*a, **k):
        raise OnnxFailure("TEST ONLY invalid graph")
    instance._session = SimpleNamespace(run=failure)
    with pytest.raises(model.LocalModelUnavailable, match="invalid graph"):
        instance.encode(["TEST ONLY"])


def test_backend_specific_session_failure_is_actionable_without_torch(monkeypatch, tmp_path):
    import sys
    class OnnxFailure(Exception):
        pass
    for name, value in {
        "config.json": {"model_type": "bert", "hidden_size": 384},
        "sentence_bert_config.json": {"max_seq_length": 256},
        "1_Pooling/config.json": {"word_embedding_dimension": 384, "pooling_mode_mean_tokens": True}
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(model, "inspect_assets", lambda *a: (tmp_path, {"TEST ONLY": "injected"}))
    monkeypatch.setattr(model, "validate_cache_environment", lambda *a: None)
    def failure(*a, **k):
        raise OnnxFailure("TEST ONLY session failure")
    fake = SimpleNamespace(disable_telemetry_events=lambda: None, SessionOptions=SimpleNamespace,
        ExecutionMode=SimpleNamespace(ORT_SEQUENTIAL="TEST ONLY"),
        GraphOptimizationLevel=SimpleNamespace(ORT_ENABLE_BASIC="TEST ONLY"), InferenceSession=failure)
    monkeypatch.setitem(sys.modules, "onnxruntime", fake)
    monkeypatch.setitem(sys.modules, "numpy", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(Tokenizer=object))
    with pytest.raises(model.LocalModelUnavailable, match="session failure"):
        model.LocalOnnxMiniLM(tmp_path, tmp_path)


def test_payload_report_accumulates_across_distinct_assets(tmp_path):
    directory = tmp_path / "model"
    ledger = Ledger(tmp_path / "ledger.json")
    pin = (3, "sha256", sha256(b"yes").hexdigest())
    record = {}
    setup.fetch_asset("test-a.txt", pin, directory, tmp_path, ledger, record, Opener(b"yes"))
    setup.fetch_asset("test-b.txt", pin, directory, tmp_path, ledger, record, Opener(b"yes"))
    assert record["asset_payload_written_bytes"] == 6
    assert ledger.total == 8
