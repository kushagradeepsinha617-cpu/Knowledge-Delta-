"""Offline doubles validate adapters, never model quality or actual ML imports."""
import json
from http.client import BadStatusLine, IncompleteRead
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from knowledge_delta.embeddings import LocalMiniLM, LocalModelUnavailable, inspect_assets, validate_cache_environment
from knowledge_delta.ollama import LocalHTTP, LocalServiceError, OllamaClient
from knowledge_delta.pipeline import RunConfiguration, run_question
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.questions import QuestionInput
from knowledge_delta.snapshots import parse_snapshot
from knowledge_delta.validation import ValidationError


class ScriptedTransport:
    mode = "test_double"

    def __init__(self, replies=None, thinking=None, digest_after="fixture-digest"):
        self.calls = []
        self.replies = list(replies or [successful()])
        self.thinking = thinking if thinking is not None else {"values": [False, True], "default": True}
        self.digest_after = digest_after
        self.inventory_count = 0

    def request(self, path, payload=None):
        self.calls.append((path, payload))
        if path == "/api/tags":
            self.inventory_count += 1
            return json.dumps({"models": [{"name": "qwen3:1.7b", "digest":
                "fixture-digest" if self.inventory_count == 1 else self.digest_after}]})
        if path == "/api/version":
            return '{"version":"test-double-only"}'
        if path == "/api/show":
            return json.dumps({"thinking": self.thinking})
        if path == "/api/chat":
            response = self.replies.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        raise AssertionError("unexpected endpoint")


def successful(**changes):
    response = {"model": "qwen3:1.7b", "done": True, "done_reason": "stop",
                "message": {"role": "assistant", "content": json.dumps({
                    "answer": "Insufficient evidence.", "citations": [], "abstained": True})},
                "eval_count": 12, "prompt_eval_count": 90, "total_duration": 1000}
    response.update(changes)
    return json.dumps(response)


def prompt():
    return {"messages": [{"role": "user", "content": "Fixture only"}], "format": {},
            "context_window": 4096, "max_output_tokens": 128}


def test_successful_double_never_claims_live_inference_or_semantic_pass():
    transport = ScriptedTransport()
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["origin"] == "test_double"
    assert result["status"] == "answered_pending_review"
    assert result["answer"]["abstained"] is True
    assert result["model_digest"] == "fixture-digest"
    assert result["model_provenance_verified"] is False
    assert result["effective_model_context_verified"] is False
    assert result["answer_cache_used"] is False
    sent = next(payload for path, payload in transport.calls if path == "/api/chat")
    assert sent["think"] is False and sent["stream"] is False
    assert sent["options"] == {"temperature": 0, "num_ctx": 4096, "num_predict": 128, "num_gpu": 0}
    assert result["attempts"][0]["response"]["prompt_eval_count"] == 90


def test_malformed_generation_is_preserved_before_bounded_success():
    bad = successful(message={"role": "assistant", "content": "not JSON"})
    result = OllamaClient(transport=ScriptedTransport([bad, successful()])).answer(prompt(), ())
    assert result["status"] == "answered_pending_review"
    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["raw_body"] == bad
    assert result["attempts"][0]["error"]


def test_generation_request_identity_is_distinct_from_shared_configuration():
    first = OllamaClient(transport=ScriptedTransport()).answer(prompt(), ())
    other_prompt = dict(prompt(), messages=[{"role": "user", "content": "A different fixture question"}])
    second = OllamaClient(transport=ScriptedTransport()).answer(other_prompt, ())
    assert first["configuration_id"] == second["configuration_id"]
    assert first["generation_request_id"] != second["generation_request_id"]


@pytest.mark.parametrize("response", [
    successful(done=False), successful(done_reason="length"), successful(model="different"),
    successful(eval_count=True), successful(prompt_eval_count=-1),
    successful(message={"role": "assistant", "content": "{}", "thinking": "unexpected"}),
    successful(message={"role": "assistant", "content": None}),
    '{"model":"qwen3:1.7b","done":true,"done":false}',
])
def test_faulty_generation_is_explicit_run_error(response):
    result = OllamaClient(transport=ScriptedTransport([response])).answer(prompt(), (), max_attempts=1)
    assert result["status"] == "run_error"
    assert result["answer"] is None and result["error"]
    assert result["attempts"][0]["raw_body"] == response


def test_transport_failure_is_not_silently_retried():
    transport = ScriptedTransport([LocalServiceError("timeout", "partial fixture")])
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["status"] == "run_error"
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["raw_body"] == "partial fixture"
    assert result["generation_performed"] is False
    assert result["generation_attempted"] is True


def test_digest_change_invalidates_answer_but_preserves_raw_generation():
    result = OllamaClient(transport=ScriptedTransport(digest_after="changed")).answer(prompt(), ())
    assert result["status"] == "run_error" and result["answer"] is None
    assert "identity changed" in result["error"]
    assert result["attempts"][0]["valid"] is True


def test_missing_model_does_not_generate_or_pull():
    class Missing(ScriptedTransport):
        def request(self, path, payload=None):
            self.calls.append((path, payload))
            assert path == "/api/tags"
            return '{"models":[]}'
    transport = Missing()
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["generation_performed"] is False
    assert result["status"] == "run_error"
    assert "missing" in result["error"]


def test_unsupported_thinking_control_blocks_expensive_generation():
    transport = ScriptedTransport(thinking={"values": ["low", "high"]})
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["generation_performed"] is False
    assert not any(path == "/api/chat" for path, payload in transport.calls)


@pytest.mark.parametrize("model", ["qwen3:1.7b-cloud", "https://host/model", "other"])
def test_model_selection_never_accepts_hosted_or_silent_substitute(model):
    with pytest.raises(ValidationError):
        OllamaClient(model)


@pytest.mark.parametrize("port,timeout", [(True, 3), (0, 3), (65536, 3), (11434, 0), (11434, float("nan"))])
def test_local_endpoint_configuration_is_bounded(port, timeout):
    with pytest.raises(ValidationError):
        LocalHTTP(port, timeout)


def test_local_transport_forbids_pull_and_arbitrary_urls():
    transport = LocalHTTP()
    assert transport.base_url == "http://127.0.0.1:11434"
    for path in ("/api/pull", "https://host/api/chat", "//host/api/chat"):
        with pytest.raises(ValidationError):
            transport.request(path)


@pytest.mark.parametrize("failure", [ConnectionRefusedError("fixture connection refused"), BadStatusLine("fixture bad status")])
def test_missing_local_service_is_actionable_and_never_downloads(failure):
    class RefusingOpener:
        def open(self, request, timeout):
            assert request.full_url == "http://127.0.0.1:11434/api/tags"
            raise failure
    transport = LocalHTTP()
    transport._opener = RefusingOpener()
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["status"] == "run_error"
    assert "no download attempted" in result["error"]
    assert result["generation_performed"] is False


def test_remote_model_metadata_prevents_generation():
    class Remote(ScriptedTransport):
        def request(self, path, payload=None):
            if path == "/api/show":
                return '{"remote_model":"qwen3","remote_host":"https://example.invalid"}'
            return super().request(path, payload)
    result = OllamaClient(transport=Remote()).answer(prompt(), ())
    assert result["status"] == "run_error"
    assert "hosted inference is forbidden" in result["error"]
    assert result["generation_performed"] is False


def test_remote_alias_in_inventory_prevents_even_show_or_generation():
    class Remote(ScriptedTransport):
        def request(self, path, payload=None):
            assert path == "/api/tags"
            return '{"models":[{"name":"qwen3:1.7b","remote_host":"https://example.invalid"}]}'
    result = OllamaClient(transport=Remote()).answer(prompt(), ())
    assert result["status"] == "run_error" and "remote alias" in result["error"]
    assert result["generation_performed"] is False


@pytest.mark.parametrize("field", ["digest", "version"])
def test_invalid_unicode_in_service_identity_becomes_explicit_error(field):
    class InvalidIdentity(ScriptedTransport):
        def request(self, path, payload=None):
            if field == "digest" and path == "/api/tags":
                return '{"models":[{"name":"qwen3:1.7b","digest":"\\ud800"}]}'
            if field == "version" and path == "/api/version":
                return '{"version":"\\ud800"}'
            return super().request(path, payload)
    result = OllamaClient(transport=InvalidIdentity()).answer(prompt(), ())
    assert result["status"] == "run_error" and "UTF-8" in result["error"]
    assert result["generation_performed"] is False


def test_actual_http_adapter_rejects_oversized_body_without_parsing_it():
    class LargeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, maximum):
            assert maximum == 1024 * 1024 + 1
            return b"x" * maximum
    class LargeOpener:
        def open(self, request, timeout):
            return LargeResponse()
    transport = LocalHTTP()
    transport._opener = LargeOpener()
    with pytest.raises(LocalServiceError, match="exceeds"):
        transport.request("/api/tags")


def test_incomplete_success_body_is_bounded_and_preserved_as_service_error():
    class PartialResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, maximum):
            assert maximum == 1024 * 1024 + 1
            raise IncompleteRead(b'partial {"message":', 100)
    class PartialOpener:
        def open(self, request, timeout):
            return PartialResponse()
    transport = LocalHTTP()
    transport._opener = PartialOpener()
    with pytest.raises(LocalServiceError, match="body read failed") as error:
        transport.request("/api/chat", {"model": "qwen3:1.7b"})
    assert error.value.raw_body == 'partial {"message":'


def test_error_body_read_failure_is_also_a_structured_service_error():
    class BrokenErrorBody:
        def read(self, maximum):
            raise ConnectionResetError("fixture error-body reset")

        def close(self):
            pass
    class ErrorOpener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, 500, "fixture", {}, BrokenErrorBody())
    transport = LocalHTTP()
    transport._opener = ErrorOpener()
    result = OllamaClient(transport=transport).answer(prompt(), ())
    assert result["status"] == "run_error"
    assert "body read failed" in result["error"]
    assert result["generation_performed"] is False


def contained_environment(monkeypatch, root):
    for key in ("HF_HOME", "HF_HUB_CACHE", "HF_XET_CACHE", "TORCH_HOME", "TEMP", "TMP"):
        monkeypatch.setenv(key, str(root / key))
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        monkeypatch.setenv(key, "1")


def test_embedding_adapter_rejects_outside_cache_before_import(monkeypatch, tmp_path):
    contained_environment(monkeypatch, tmp_path)
    validate_cache_environment(tmp_path)
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path.parent / "outside"))
    with pytest.raises(LocalModelUnavailable, match="HF_HUB_CACHE"):
        LocalMiniLM(tmp_path / "absent", tmp_path)


def test_embedding_adapter_requires_offline_mode_before_import(monkeypatch, tmp_path):
    contained_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("HF_HUB_OFFLINE")
    with pytest.raises(LocalModelUnavailable, match="HF_HUB_OFFLINE"):
        LocalMiniLM(tmp_path / "absent", tmp_path)


def test_missing_embedding_assets_never_initiate_download(tmp_path):
    with pytest.raises(LocalModelUnavailable, match="missing"):
        inspect_assets(tmp_path / "absent")
    with pytest.raises(LocalModelUnavailable, match="model.safetensors"):
        inspect_assets(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_empty_retrieval_abstains_by_policy_without_claiming_model_inference():
    raw = {"schema_version": 1, "name": "test", "domain": "test", "default_version": "1",
           "provenance": "constructed", "documents": []}
    snap = parse_snapshot(raw, Path.cwd())
    class EmptyIndex:
        embedder_mode = "test_double"
        chunks = ()
        index_id = "test-double-empty-index"
        chunker_configurations = ()

        def search(self, question, snapshot, embedder, top_k, version_filter):
            return SimpleNamespace(effective_version="1", chunks=(), scores=(), excluded=())
    transport = ScriptedTransport()
    result = run_question(QuestionInput("x", "Question?", "explicit_version", "1"), snap,
                          EmptyIndex(), SimpleNamespace(mode="test_double", identity="test-double"),
                          OllamaClient(transport=transport))
    assert result["origin"] == "test_double"
    assert result["status"] == "answered_pending_review"
    assert result["answer_origin"] == "policy_abstention"
    assert result["generation_performed"] is False and result["generation"] is None
    assert result["judgment"] == "needs_human_review"
    assert transport.calls == []


@pytest.mark.parametrize("settings", [
    {"version_filter": 1}, {"top_k": True}, {"top_k": 0}, {"max_attempts": 3},
    {"context_window": 200}, {"max_output_tokens": -1},
])
def test_invalid_pipeline_configuration_fails_before_generation(settings):
    with pytest.raises(ValidationError):
        RunConfiguration(**settings)


def test_offline_environment_is_contained_and_explicit(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    names = ("HF_HOME", "HF_HUB_CACHE", "HF_XET_CACHE", "TORCH_HOME", "XDG_CACHE_HOME",
             "TEMP", "TMP", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY",
             "PYTHONDONTWRITEBYTECODE")
    # Register all environment changes with pytest so this test cannot leak them.
    for name in names:
        monkeypatch.setenv(name, os.environ.get(name, "test-previous-value"))
    paths = configure_offline_environment(tmp_path)
    assert all(Path(value).is_relative_to(tmp_path) and Path(value).is_dir() for value in paths.values())
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
    validate_cache_environment(tmp_path)
    assert sys.dont_write_bytecode is True


def test_malformed_service_error_still_produces_utf8_serializable_trace():
    class BrokenError(ScriptedTransport):
        def request(self, path, payload=None):
            return '{"error":"\\ud800"}'
    result = OllamaClient(transport=BrokenError()).answer(prompt(), ())
    assert result["status"] == "run_error"
    json.dumps(result, ensure_ascii=False).encode("utf-8")


def test_explicit_answer_command_reports_missing_assets_without_download():
    root = Path(__file__).resolve().parents[1]
    missing = root / ".tools/models/absent-milestone2-command-test"
    assert not missing.exists()
    command = [sys.executable, "-B", str(root / "scripts/answer_question.py"),
               str(root / "examples/constructed/before/manifest.json"),
               "--question", "What is the timeout?", "--target", "explicit_version",
               "--requested-version", "1", "--embedding-directory", str(missing)]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "run_error" and "missing" in payload["error"]
    assert payload["generation_performed"] is False and payload["downloads_performed"] is False
    assert not missing.exists()
