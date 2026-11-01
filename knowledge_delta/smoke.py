"""Ten draft hardware probes, with explicit unknowns and no correctness scores."""
from datetime import datetime, timezone
from uuid import uuid4

from .pipeline import RunConfiguration, run_question
from .doctor import readiness
from .questions import QuestionInput
from .validation import ValidationError, fields, digest, schema_version, sequence


def parse_smoke_questions(raw, snapshot):
    fields(raw, ("schema_version", "kind", "snapshot_id", "provenance", "review_status", "questions"), "smoke")
    schema_version(raw["schema_version"], "smoke")
    if (raw["kind"] != "hardware_smoke_questions" or raw["snapshot_id"] != snapshot.snapshot_id
            or raw["provenance"] != "constructed" or snapshot.provenance != "constructed"
            or raw["review_status"] != "draft"):
        raise ValidationError("Smoke inputs must be explicit draft constructed questions bound to this snapshot")
    questions = []
    for item in sequence(raw["questions"], "smoke.questions"):
        fields(item, ("case_id", "question", "target", "requested_version", "target_context"), "smoke question")
        questions.append(QuestionInput(**item))
    if len(questions) != 10 or len({q.case_id for q in questions}) != 10 or len({q.question for q in questions}) != 10:
        raise ValidationError("Hardware smoke requires exactly ten distinct question IDs and questions")
    return tuple(questions)


def _loading_label(observation, generation, context_window):
    if not generation or not generation.get("attempts"):
        return "no_generation_request"
    if observation["status"] != "observed":
        return "unknown"
    identity = generation.get("model_digest")
    if identity is None:
        return "unknown"
    models = observation["models"]
    matching = [model for model in models if model.get("digest") == identity]
    if any(model.get("context_length") == context_window for model in matching):
        return "observed_same_model_and_context_resident"
    if not matching and all(model.get("digest") is not None for model in models):
        return "observed_not_resident_before_request"
    return "unknown_or_reload_possible"


def run_smoke(questions, snapshot, index, embedder, client):
    if len(questions) != 10 or len({q.case_id for q in questions}) != 10 or len({q.question for q in questions}) != 10:
        raise ValidationError("Hardware smoke requires exactly ten distinct questions")
    config = RunConfiguration(top_k=1, max_attempts=1)
    result = {"schema_version": 1, "kind": "hardware_smoke", "run_id": uuid4().hex,
              "started_at": datetime.now(timezone.utc).isoformat(), "snapshot_id": snapshot.snapshot_id,
              "questions_id": digest([q.__dict__ for q in questions]), "review_status": "draft",
              "provenance": snapshot.provenance,
              "correctness_measured": False, "answer_cache_used": False,
              "readiness": readiness(check_ollama=False),
              "os_peak_ram_bytes": None, "os_peak_ram_note": "Not measured; model size is not process peak RAM.",
              "cold_start_note": "Pre-request residency is an observation; OS disk-cache coldness is unverified.",
              "results": [], "control_violations": []}
    cpu_violation = False
    for question in questions:
        if cpu_violation:
            result["results"].append({"case_id": question.case_id, "snapshot_id": snapshot.snapshot_id,
                "origin": result["results"][0]["origin"], "status": "run_error", "generation": None,
                "generation_performed": False, "generation_attempted": False,
                "error_phase": "cpu_control", "error": "Blocked after observed CPU control violation",
                "ollama_reported_cpu_residency": None, "loading_observation": "not_requested_after_cpu_control_violation"})
            continue
        before = client.observe_residency()
        value = run_question(question, snapshot, index, embedder, client, config)
        after = client.observe_residency()
        generation = value.get("generation")
        value["residency_before"], value["residency_after"] = before, after
        value["loading_observation"] = _loading_label(before, generation, config.context_window)
        identity = generation.get("model_digest") if generation and generation["generation_performed"] else None
        matching = [model for model in after.get("models", []) if identity is not None
                    and model.get("digest") == identity and model.get("context_length") == config.context_window]
        vram = [model.get("size_vram") for model in matching]
        cpu = (all(value == 0 for value in vram) if vram and all(type(value) is int for value in vram) else None)
        value["ollama_reported_cpu_residency"] = cpu
        if cpu is False:
            cpu_violation = True
            result["control_violations"].append({"case_id": question.case_id,
                "reason": "Matching resident model reports GPU memory despite requested num_gpu=0"})
        result["results"].append(value)
    records = result["results"]
    generations = [row["generation"] for row in records if row.get("generation")]
    identities = {(g.get("model"), g.get("model_digest"), g.get("configuration_id")) for g in generations}
    result["counts"] = {"planned_questions": 10,
        "chat_post_attempts": sum(len(g["attempts"]) for g in generations),
        "completed_generation_responses": sum(g["generation_performed"] for g in generations),
        "structured_answers_pending_review": sum(row["status"] == "answered_pending_review" and row["generation_performed"] for row in records),
        "run_errors": sum(row["status"] == "run_error" for row in records),
        "policy_abstentions": sum(row.get("answer_origin") == "policy_abstention" for row in records),
        "blocked_by_cpu_control": sum(row.get("error_phase") == "cpu_control" for row in records)}
    origins = {row["origin"] for row in records}
    result["origin"] = next(iter(origins)) if len(origins) == 1 else "mixed"
    result["same_model_and_settings"] = len(identities) == 1 and all(g.get("model_digest") is not None for g in generations)
    result["live_ten_request_measurement_verified"] = bool(result["origin"] == "live"
        and result["counts"]["completed_generation_responses"] == 10 and result["same_model_and_settings"])
    observations = [row["ollama_reported_cpu_residency"] for row in records]
    result["cpu_residency_observation"] = False if False in observations else (True if all(value is True for value in observations) else None)
    result["live_cpu_measurement_verified"] = bool(result["live_ten_request_measurement_verified"]
        and result["cpu_residency_observation"] is True and not result["counts"]["run_errors"])
    result["status"] = ("invalid_cpu_control" if cpu_violation else
        "completed_with_run_errors" if result["counts"]["run_errors"] else "completed_pending_review")
    return result
