"""Controlled full-dataset runs. No automatic correctness scores or answer caching."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import time
from uuid import uuid4

from .cases import validate_dataset
from .chunking import chunk_snapshot
from .pipeline import RunConfiguration, run_question
from .questions import QuestionInput
from .retrieval import build_index
from .validation import ValidationError, digest


def run_dataset(dataset, before, after, embedder, client, *, repeats=1, token_limit=128,
                overlap_tokens=16, configuration=None, index_factory=build_index):
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValidationError("repeats must be an integer in 1..5")
    summary = validate_dataset(dataset, before, after)
    common = configuration if configuration is not None else RunConfiguration()
    started = time.perf_counter()
    result = {"schema_version": 1, "kind": "local_snapshot_experiment", "run_id": uuid4().hex,
              "started_at": datetime.now(timezone.utc).isoformat(), "dataset": summary,
              "snapshots": {"before": before.snapshot_id, "after": after.snapshot_id},
              "snapshot_defaults": {"before": before.default_version, "after": after.default_version},
              "dataset_hash": digest(dataset),
              "configurations": {"basic": asdict(replace(common, version_filter=False)),
                                 "version_filtered": asdict(replace(common, version_filter=True))},
              "repeats": repeats, "answer_cache_used": False, "results": [],
              "status": "run_error", "origin": "unverified", "errors": [],
              "correctness_measured": False}
    indexes = {}
    for slot, snapshot in (("before", before), ("after", after)):
        try:
            chunks = chunk_snapshot(snapshot, embedder.tokenizer, token_limit, overlap_tokens)
            indexes[slot] = index_factory(snapshot, chunks, embedder)
        except (ValidationError, RuntimeError, OSError) as exc:
            result["errors"].append({"snapshot": slot, "phase": "index", "error": str(exc)})
    # A case's explicit requested version is never rewritten between snapshots.
    for repetition in range(1, repeats + 1):
        for name, filtered in (("basic", False), ("version_filtered", True)):
            for case in dataset["cases"]:
                for slot, snapshot in (("before", before), ("after", after)):
                    if slot not in indexes:
                        result["results"].append({"case_id": case["case_id"], "snapshot_slot": slot,
                            "configuration_name": name, "repetition": repetition,
                            "case_review_status": case["review"]["status"], "case_split": case["split"],
                            "case_provenance": case["provenance"],
                            "status": "run_error", "error_phase": "index",
                            "error": "Snapshot index unavailable; see run errors", "origin": "unverified"})
                        continue
                    value = run_question(QuestionInput.from_case(case, slot), snapshot, indexes[slot],
                                         embedder, client, replace(common, version_filter=filtered))
                    value.update(snapshot_slot=slot, configuration_name=name, repetition=repetition,
                                 case_review_status=case["review"]["status"], case_split=case["split"],
                                 case_provenance=case["provenance"])
                    result["results"].append(value)
    records = result["results"]
    result["counts"] = {"planned": len(dataset["cases"]) * 4 * repeats,
                        "recorded": len(records),
                        "run_errors": sum(item["status"] == "run_error" for item in records),
                        "awaiting_semantic_review": sum(item["status"] == "answered_pending_review" for item in records)}
    origins = {item["origin"] for item in records}
    result["origin"] = next(iter(origins)) if len(origins) == 1 else "mixed"
    result["status"] = "completed_with_run_errors" if result["counts"]["run_errors"] else "completed_pending_review"
    result["elapsed_seconds"] = time.perf_counter() - started
    return result
