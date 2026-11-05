"""Model setup metadata checks are offline and never fetch weights."""
import json

import pytest

from scripts import inspect_model_setup as preflight
from knowledge_delta.embeddings import REQUIRED
from knowledge_delta.validation import ValidationError


def blob(value):
    return json.dumps(value).encode()


def test_qwen_manifest_records_exact_payload_and_rejects_bad_layers():
    part = {"digest": "sha256:" + "a" * 64, "size": 10}
    data = blob({"schemaVersion": 2, "config": part, "layers": [part]})
    result = preflight.qwen_manifest(data)
    assert result["artifact_payload_bytes"] == 20
    assert len(result["manifest_sha256"]) == 64
    part["size"] = True
    with pytest.raises(ValidationError, match="digest/size"):
        preflight.qwen_manifest(blob({"schemaVersion": 2, "config": part, "layers": [part]}))


def test_minilm_inventory_does_not_silently_omit_required_tokenizer_assets():
    entries = [{"type": "file", "path": name, "size": 10, "oid": "a" * 40}
               for name in (*REQUIRED, "README.md")]
    result = preflight.minilm_assets(blob(entries))
    assert len(result["files"]) == len(REQUIRED) + 1
    with pytest.raises(ValidationError, match="assets missing"):
        preflight.minilm_assets(blob(entries[1:]))


def test_metadata_fetch_rejects_weight_and_arbitrary_urls_before_network():
    for url in ("https://example.com/data", "https://huggingface.co/model.safetensors",
                "http://127.0.0.1:11434/api/pull"):
        with pytest.raises(ValidationError, match="explicit metadata"):
            preflight.fetch_metadata(url)


def test_offline_default_does_not_call_network_or_write_report(monkeypatch, capsys):
    def forbidden(*args):
        raise AssertionError("No metadata requests in default mode")
    monkeypatch.setattr(preflight, "inspect", forbidden)
    assert preflight.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "offline_plan"
    assert result["network_requests"] == 0


def test_partial_network_failure_stays_explicit_and_bounded():
    calls = []
    def unavailable(url):
        calls.append(url)
        raise OSError("TEST ONLY network unavailable")
    result = preflight.inspect(unavailable)
    assert len(calls) == 5
    assert len(result["requests"]) == 5
    assert result["status"] == "metadata_partial_or_unavailable"
    assert result["models_installed"] is False
    assert result["installer_authorized_by_report"] is False
    assert result["metadata_payload_bytes"] == 0


def test_metadata_success_still_does_not_claim_ready_to_install(monkeypatch):
    part = {"digest": "sha256:" + "a" * 64, "size": 10}
    responses = {
        "qwen": blob({"schemaVersion": 2, "config": part, "layers": [part]}),
        "minilm": blob([{"type": "file", "path": name, "size": 10}
                        for name in (*REQUIRED, "README.md")]),
        "ollama": blob({"tag_name": "v0.40.14", "assets": [
            {"name": "ollama-windows-amd64.zip", "size": 100,
             "digest": "sha256:" + "b" * 64}]}),
        "cpu_torch": b"TEST ONLY CPU index",
        "sentence_transformers": blob({"info": {"version": "TEST ONLY"}})}
    reverse = {url: key for key, url in preflight.URLS.items()}
    monkeypatch.setattr(preflight, "cpu_candidate", lambda data: {"dependency_closure_verified": False})
    result = preflight.inspect(lambda url: responses[reverse[url]])
    assert result["status"] == "metadata_inspected_setup_still_pending"
    assert result["dependency_closure_verified"] is False
    assert result["artifact_downloads_performed"] is False
    assert result["installer_authorized_by_report"] is False


def test_oversized_metadata_cannot_be_accepted_as_manifest():
    result = preflight.inspect(lambda url: b"x" * (preflight.MAX_RESPONSE + 1))
    assert result["status"] == "metadata_partial_or_unavailable"
    assert all(item["status"] == "error" for item in result["requests"])
