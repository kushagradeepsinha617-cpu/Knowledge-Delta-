"""Synthetic control checks only; these are not model benchmark results."""
from copy import deepcopy

import pytest

from scripts.compare_output_budget import compare
from knowledge_delta.validation import ValidationError


def experiments():
    row = {"case_id": "synthetic", "configuration_name": "basic", "snapshot_slot": "before", "repetition": 1,
           "snapshot_id": "snapshot", "question": {"question": "TEST ONLY"},
           "requested_version": "1", "effective_version": "1", "index_id": "index", "embedder_id": "embedder",
           "embedding_configuration": {"backend": "TEST ONLY"}, "retrieved_passages": [{"text": "TEST evidence"}],
           "retrieval_exclusions": [], "configuration": {"max_output_tokens": 128, "max_attempts": 2},
           "prompt": {"messages": ["TEST question"], "format": {"type": "object"}, "prompt_id": "prompt",
                      "prompt_version": "test", "context_window": 4096, "max_output_tokens": 128},
           "generation": {"model": "TEST ONLY", "model_digest": "digest", "model_digest_after": "digest",
                          "server_version": "test", "request": {"think": False, "messages": ["TEST question"],
                          "options": {"num_predict": 128, "num_gpu": 0}},
                          "attempts": [{"response": {"done_reason": "length"}}]}, "status": "run_error"}
    left = {"kind": "local_snapshot_experiment", "origin": "live", "answer_cache_used": False,
            "run_id": "SYNTHETIC baseline; live-origin field is deliberately not authenticated",
            "dataset_hash": "dataset", "snapshots": {"before": "snapshot", "after": "other"},
            "snapshot_defaults": {"before": "1", "after": "1"}, "repeats": 1,
            "configurations": {"basic": {"max_output_tokens": 128, "max_attempts": 2}},
            "counts": {"planned": 1, "recorded": 1}, "results": [row]}
    right = deepcopy(left)
    right["run_id"] = "SYNTHETIC candidate"
    right["configurations"]["basic"]["max_output_tokens"] = 256
    r = right["results"][0]
    r["configuration"]["max_output_tokens"] = r["prompt"]["max_output_tokens"] = 256
    r["generation"]["request"]["options"]["num_predict"] = 256
    r["generation"]["attempts"][0]["response"]["done_reason"] = "stop"
    r["status"] = "answered_pending_review"
    return left, right


def test_completion_change_is_measured_without_semantic_pass():
    result = compare(*experiments())
    assert result["control_checks_passed"] is True
    assert result["checked_rows"] == 1
    assert result["baseline"]["run_errors"] == 1
    assert result["candidate"]["structured_answers_pending_review"] == 1
    assert result["semantic_correctness_measured"] is False


@pytest.mark.parametrize("change", ["question", "evidence", "prompt", "schema", "model", "digest", "runtime",
                                    "extra_request_setting", "retry_limit", "row_budget", "keys", "missing", "duplicate", "cache"])
def test_changed_controls_are_rejected(change):
    left, right = experiments()
    row = right["results"][0]
    if change == "question": row["question"] = {"question": "DIFFERENT"}
    elif change == "evidence": row["retrieved_passages"][0]["text"] = "DIFFERENT"
    elif change == "prompt": row["prompt"]["messages"] = ["DIFFERENT"]
    elif change == "schema": row["prompt"]["format"] = {"type": "string"}
    elif change == "model": row["generation"]["model"] = "OTHER"
    elif change == "digest": row["generation"]["model_digest_after"] = "OTHER"
    elif change == "runtime": row["generation"]["server_version"] = "OTHER"
    elif change == "extra_request_setting": row["generation"]["request"]["options"]["temperature"] = 1
    elif change == "retry_limit": right["configurations"]["basic"]["max_attempts"] = 1
    elif change == "row_budget": row["configuration"]["max_output_tokens"] = 128
    elif change == "keys": row["case_id"] = "OTHER"
    elif change == "missing": right["results"] = []
    elif change == "duplicate": right["results"].append(deepcopy(row))
    elif change == "cache": right["answer_cache_used"] = True
    with pytest.raises(ValidationError):
        compare(left, right)
