"""Check an output-cap experiment's controls; never grade answer meaning."""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.validation import ValidationError, read_json


def keyed(run):
    if (run.get("kind") != "local_snapshot_experiment" or run.get("origin") != "live"
            or run.get("answer_cache_used") is not False):
        raise ValidationError("Require recorded live experiments with answer caching disabled")
    rows = {}
    for row in run["results"]:
        key = (row["case_id"], row["configuration_name"], row["snapshot_slot"], row["repetition"])
        if key in rows:
            raise ValidationError("Duplicate experiment row")
        rows[key] = row
    if len(rows) != run["counts"]["planned"] or len(rows) != run["counts"]["recorded"]:
        raise ValidationError("All planned records must be present")
    return rows


def summary(run):
    rows = run["results"]
    attempts = [a for row in rows for a in (row.get("generation") or {}).get("attempts", [])]
    return {"run_id": run["run_id"], "planned_records": run["counts"]["planned"],
            "recorded_records": len(rows),
            "structured_answers_pending_review": sum(r["status"] == "answered_pending_review" for r in rows),
            "run_errors": sum(r["status"] == "run_error" for r in rows),
            "chat_attempts": len(attempts),
            "attempt_stop_reasons": dict(Counter(a.get("response", {}).get("done_reason", "unavailable") for a in attempts))}


def compare(baseline, candidate):
    left, right = keyed(baseline), keyed(candidate)
    if left.keys() != right.keys():
        raise ValidationError("Experiments must contain identical case/configuration/snapshot/repetition keys")
    for field in ("dataset_hash", "snapshots", "snapshot_defaults", "repeats"):
        if baseline[field] != candidate[field]:
            raise ValidationError("Experiment control changed: " + field)
    configs = deepcopy(baseline["configurations"])
    for config in configs.values():
        if config["max_output_tokens"] != 128:
            raise ValidationError("Baseline output cap must be128")
        config["max_output_tokens"] = 256
    if configs != candidate["configurations"]:
        raise ValidationError("Only output cap128 to256 may change")
    identities = set()
    for key, a in left.items():
        b = right[key]
        for field in ("snapshot_id", "question", "requested_version", "effective_version", "index_id",
                      "embedder_id", "embedding_configuration", "retrieved_passages", "retrieval_exclusions"):
            if a[field] != b[field]:
                raise ValidationError(f"Row control changed: {key}: {field}")
        expected_config = dict(a["configuration"], max_output_tokens=256)
        if a["configuration"]["max_output_tokens"] != 128 or b["configuration"] != expected_config:
            raise ValidationError("Row output cap/configuration differs")
        for field in ("messages", "format", "prompt_id", "prompt_version", "context_window"):
            if a["prompt"][field] != b["prompt"][field]:
                raise ValidationError(f"Prompt control changed: {key}: {field}")
        if a["prompt"]["max_output_tokens"] != 128 or b["prompt"]["max_output_tokens"] != 256:
            raise ValidationError("Prompt output cap differs")
        ga, gb = a["generation"], b["generation"]
        for field in ("model", "model_digest", "model_digest_after", "server_version"):
            if not ga.get(field) or ga[field] != gb.get(field):
                raise ValidationError(f"Model/runtime control changed: {key}: {field}")
        if ga["model_digest"] != ga["model_digest_after"]:
            raise ValidationError("Model digest changed within a request")
        identities.add((ga["model"], ga["model_digest"], ga["server_version"]))
        expected_request = deepcopy(ga["request"])
        if expected_request["options"]["num_predict"] != 128:
            raise ValidationError("Baseline generation output cap differs")
        expected_request["options"]["num_predict"] = 256
        if expected_request != gb["request"]:
            raise ValidationError(f"Generation request changed beyond output cap: {key}")
        if ga["request"].get("think") is not False or ga["request"]["options"].get("num_gpu") != 0:
            raise ValidationError("Require thinking disabled and requested CPU operation")
    if len(identities) != 1:
        raise ValidationError("One fixed model/digest/runtime is required throughout")
    return {"kind": "output_budget_control_comparison", "control_checks_passed": True,
            "checked_rows": len(left), "intended_change": "output cap128 to256",
            "baseline": summary(baseline), "candidate": summary(candidate),
            "semantic_correctness_measured": False,
            "note": "Controls are compared against recorded traces, not authenticated execution. Completion is not correctness; latency is not a causal performance estimate."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = (ROOT / args.output).resolve()
        if (not output.is_relative_to(ROOT / "runs") or output.suffix != ".json"
                or output.exists() or args.output.is_symlink()):
            raise ValidationError("Choose a new project-local runs/*.json output")
        inputs = []
        for path in (args.baseline, args.candidate):
            full = (ROOT / path).resolve()
            if path.is_symlink() or not full.is_relative_to(ROOT) or not full.is_file() or full.stat().st_size > 16 * 1024 * 1024:
                raise ValidationError("Select regular project-local experiment JSON files within16MiB")
            inputs.append(read_json(full))
        result = compare(*inputs)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
        print(json.dumps(result, indent=2))
        return 0
    except (ValidationError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "control_checks_passed": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
