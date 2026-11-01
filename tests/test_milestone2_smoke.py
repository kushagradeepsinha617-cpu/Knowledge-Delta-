"""Hardware harness contracts with doubles; these are never hardware measurements."""
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from knowledge_delta.chunking import chunk_snapshot
from knowledge_delta.ollama import OllamaClient
from knowledge_delta.smoke import parse_smoke_questions, run_smoke
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json

ROOT = Path(__file__).resolve().parents[1]


class TokenizerDouble:
    mode = "test_double"
    identity = "smoke-whitespace-double"

    def offsets(self, text):
        return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]

    def count(self, text):
        return len(self.offsets(text)) + 2


class TransportDouble:
    mode = "test_double"

    def __init__(self, malformed_first=False):
        self.chat_posts = 0
        self.malformed_first = malformed_first

    def request(self, path, payload=None):
        model = {"name": "qwen3:1.7b", "digest": "smoke-double-digest", "context_length": 4096, "size_vram": 0}
        if path == "/api/tags":
            return json.dumps({"models": [model]})
        if path == "/api/version":
            return '{"version":"smoke-double"}'
        if path == "/api/show":
            return '{"thinking":{"values":[false,true]}}'
        if path == "/api/ps":
            return json.dumps({"models": [model] if self.chat_posts else []})
        assert path == "/api/chat"
        self.chat_posts += 1
        content = "malformed" if self.malformed_first and self.chat_posts == 1 else json.dumps({
            "answer": "Fixture-only abstention.", "citations": [], "abstained": True})
        return json.dumps({"model": "qwen3:1.7b", "done": True, "done_reason": "stop",
                           "message": {"role": "assistant", "content": content},
                           "prompt_eval_count": 150, "eval_count": 12, "load_duration": 100})


def setup(empty=False, malformed_first=False):
    snapshot = load_snapshot(ROOT / "examples/constructed/smoke/manifest.json")
    raw = read_json(ROOT / "examples/constructed/smoke_questions.json")
    questions = parse_smoke_questions(raw, snapshot)
    chunks = () if empty else chunk_snapshot(snapshot, TokenizerDouble(), 128, 16)
    class IndexDouble:
        embedder_mode = "test_double"
        index_id = "smoke-double-index"
        chunker_configurations = (("smoke-double", 128, 16, "smoke-whitespace-double", "test_double"),)

        def __init__(self):
            self.chunks = chunks

        def search(self, question, snapshot, embedder, top_k, version_filter):
            assert top_k == 1 and version_filter is False
            return SimpleNamespace(chunks=chunks[:1], scores=(0.75,) if chunks else (), excluded=(), effective_version="1")
    transport = TransportDouble(malformed_first)
    return questions, snapshot, IndexDouble(), SimpleNamespace(mode="test_double", identity="smoke-double"), OllamaClient(transport=transport), transport


def test_ten_double_responses_never_verify_live_measurements_or_peak_ram():
    questions, snapshot, index, embedder, client, transport = setup()
    result = run_smoke(questions, snapshot, index, embedder, client)
    assert transport.chat_posts == 10
    assert result["counts"] == {"planned_questions": 10, "chat_post_attempts": 10,
        "completed_generation_responses": 10, "structured_answers_pending_review": 10,
        "run_errors": 0, "policy_abstentions": 0, "blocked_by_cpu_control": 0}
    assert result["origin"] == "test_double" and result["live_ten_request_measurement_verified"] is False
    assert result["live_cpu_measurement_verified"] is False
    assert result["os_peak_ram_bytes"] is None and result["correctness_measured"] is False
    assert result["results"][0]["loading_observation"] == "observed_not_resident_before_request"
    assert all(row["loading_observation"] == "observed_same_model_and_context_resident" for row in result["results"][1:])


def test_malformed_completed_generation_is_counted_separately_from_valid_answers():
    questions, snapshot, index, embedder, client, transport = setup(malformed_first=True)
    result = run_smoke(questions, snapshot, index, embedder, client)
    assert transport.chat_posts == 10  # max_attempts=1 prevents hidden extra requests.
    assert result["counts"]["completed_generation_responses"] == 10
    assert result["counts"]["structured_answers_pending_review"] == 9
    assert result["counts"]["run_errors"] == 1
    assert result["results"][0]["generation"]["attempts"][0]["error"]


def test_policy_abstentions_are_not_counted_as_inference():
    questions, snapshot, index, embedder, client, transport = setup(empty=True)
    result = run_smoke(questions, snapshot, index, embedder, client)
    assert transport.chat_posts == 0
    assert result["counts"]["policy_abstentions"] == 10
    assert result["counts"]["completed_generation_responses"] == 0
    assert result["live_ten_request_measurement_verified"] is False
    assert all(row["loading_observation"] == "no_generation_request" for row in result["results"])
    assert all(row["ollama_reported_cpu_residency"] is None for row in result["results"])


def test_same_digest_with_a_different_resident_context_is_not_labeled_warm():
    questions, snapshot, index, embedder, client, transport = setup()
    class DifferentContext(TransportDouble):
        def request(self, path, payload=None):
            body = super().request(path, payload)
            if path == "/api/ps":
                value = json.loads(body)
                for item in value["models"]:
                    item["context_length"] = 8192
                return json.dumps(value)
            return body
    client = OllamaClient(transport=DifferentContext())
    result = run_smoke(questions, snapshot, index, embedder, client)
    assert all(row["loading_observation"] == "unknown_or_reload_possible" for row in result["results"][1:])
    assert all(row["ollama_reported_cpu_residency"] is None for row in result["results"])


def test_smoke_command_missing_assets_is_an_error_without_download():
    missing = ROOT / ".tools/models/absent-milestone2-smoke-command-test"
    assert not missing.exists()
    result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/smoke_local_model.py"),
        str(ROOT / "examples/constructed/smoke/manifest.json"),
        str(ROOT / "examples/constructed/smoke_questions.json"),
        "--embedding-directory", str(missing)], cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "run_error" and "missing" in payload["error"]
    assert payload["downloads_performed"] is False and payload["generation_performed"] is False
    assert not missing.exists()


def test_another_alias_for_the_same_digest_is_recognized_as_resident():
    questions, snapshot, index, embedder, client, transport = setup()
    class Aliased(TransportDouble):
        def request(self, path, payload=None):
            body = super().request(path, payload)
            if path == "/api/ps":
                value = json.loads(body)
                for item in value["models"]:
                    item["name"] = "another-local-alias"
                return json.dumps(value)
            return body
    result = run_smoke(questions, snapshot, index, embedder, OllamaClient(transport=Aliased()))
    assert all(row["loading_observation"] == "observed_same_model_and_context_resident" for row in result["results"][1:])
    assert result["cpu_residency_observation"] is True
    assert result["live_cpu_measurement_verified"] is False  # Still an explicit double.


def test_missing_resident_digests_produce_unknowns_instead_of_false_cold_labels():
    questions, snapshot, index, embedder, client, transport = setup()
    class MissingDigests(TransportDouble):
        def request(self, path, payload=None):
            body = super().request(path, payload)
            if path == "/api/ps":
                value = json.loads(body)
                for item in value["models"]:
                    item.pop("digest")
                return json.dumps(value)
            return body
    result = run_smoke(questions, snapshot, index, embedder, OllamaClient(transport=MissingDigests()))
    assert all(row["loading_observation"] == "unknown_or_reload_possible" for row in result["results"][1:])
    assert result["cpu_residency_observation"] is None


def test_reported_gpu_control_violation_stops_and_preserves_remaining_questions():
    questions, snapshot, index, embedder, client, transport = setup()
    class GPUObserved(TransportDouble):
        def request(self, path, payload=None):
            body = super().request(path, payload)
            if path == "/api/ps":
                value = json.loads(body)
                for item in value["models"]:
                    item["size_vram"] = 1000
                return json.dumps(value)
            return body
    transport = GPUObserved()
    result = run_smoke(questions, snapshot, index, embedder, OllamaClient(transport=transport))
    assert transport.chat_posts == 1
    assert result["counts"]["planned_questions"] == len(result["results"]) == 10
    assert result["counts"]["blocked_by_cpu_control"] == 9
    assert result["status"] == "invalid_cpu_control" and result["control_violations"]
    assert result["live_cpu_measurement_verified"] is False
    assert result["cpu_residency_observation"] is False


@pytest.mark.parametrize("change", ["duplicate", "missing", "wrong_snapshot", "gold_leak"])
def test_invalid_smoke_inputs_fail_before_any_service_request(change):
    snapshot = load_snapshot(ROOT / "examples/constructed/smoke/manifest.json")
    raw = deepcopy(read_json(ROOT / "examples/constructed/smoke_questions.json"))
    if change == "duplicate":
        raw["questions"][1] = raw["questions"][0]
    elif change == "missing":
        raw["questions"].pop()
    elif change == "wrong_snapshot":
        raw["snapshot_id"] = "wrong"
    else:
        raw["questions"][0]["expected_answer"] = "must not enter the model input"
    with pytest.raises(ValidationError):
        parse_smoke_questions(raw, snapshot)
