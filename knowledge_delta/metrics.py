"""Counts and explicitly conditional metrics; no model grading or inferred labels.

An independent reference label is a separate annotation, not an answer review:
schema_version, binding, reference_outcome ('failure'/'not_failure'),
basis='independent_human_reference', reviewer, reviewed_at, rationale,
independence_attested=True. Independence describes the review procedure; the
same person may perform both reviews. It is not proof of blinding or identity.
"""
from collections import Counter
from datetime import datetime
import math
from statistics import median

from .validation import ValidationError, choice, digest, fields, text


def _require(value, names, label):
    if not isinstance(value, dict) or any(name not in value for name in names):
        raise ValidationError(f"{label}: expected an object containing {', '.join(names)}")


def _ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def _timestamp(value):
    text(value, "reference/review timestamp")
    try:
        if datetime.fromisoformat(value).utcoffset() is None:
            raise ValueError("timezone required")
    except ValueError as exc:
        raise ValidationError("Reference/review timestamp requires an ISO8601 timezone") from exc


def _records(evaluation):
    _require(evaluation, ("kind", "run_id", "dataset_hash", "counts", "rows"), "evaluation")
    if evaluation["kind"] != "knowledge_delta_evaluation" or not isinstance(evaluation["rows"], list):
        raise ValidationError("Metrics require evaluated rows, not a raw experiment or answer key")
    text(evaluation["run_id"], "run_id")
    text(evaluation["dataset_hash"], "dataset_hash")
    records, seen = [], set()
    for row in evaluation["rows"]:
        _require(row, ("case_id", "configuration_name", "repetition", "case", "snapshots"), "evaluation row")
        case = row["case"]
        _require(case, ("case_id", "review", "provenance", "split", "expectations"), "case")
        _require(case["review"], ("status",), "case review")
        choice(case["review"]["status"], ("draft", "human_reviewed"), "case review status")
        choice(case["provenance"], ("constructed", "genuine"), "case provenance")
        choice(case["split"], ("development", "held_out"), "case split")
        if row["case_id"] != case["case_id"]:
            raise ValidationError("Metric row refers to a different case")
        if type(row["repetition"]) is not int or row["repetition"] < 1:
            raise ValidationError("Metric repetition must be a positive integer")
        text(row["configuration_name"], "configuration name")
        fields(row["snapshots"], ("before", "after"), "metric snapshots")
        for slot, detail in row["snapshots"].items():
            _require(detail, ("trace", "judgment", "expectation"), "snapshot detail")
            trace, judgment = detail["trace"], detail["judgment"]
            _require(trace, ("status", "origin"), "trace")
            _require(judgment, ("binding", "outcome", "basis", "checks", "review"), "judgment")
            bound = judgment["binding"]
            fields(bound, ("result_key", "dataset_hash", "case_hash", "expectation_hash", "snapshot_id", "trace_hash"), "judgment binding")
            expected_key = {"run_id": evaluation["run_id"], "case_id": row["case_id"],
                "configuration_name": row["configuration_name"], "repetition": row["repetition"], "snapshot_slot": slot}
            if (bound["result_key"] != expected_key or bound["dataset_hash"] != evaluation["dataset_hash"]
                    or bound["case_hash"] != digest(case) or bound["trace_hash"] != digest(trace)
                    or bound["expectation_hash"] != digest(detail["expectation"])
                    or detail["expectation"] != case["expectations"][slot]
                    or trace.get("snapshot_id", bound["snapshot_id"] if trace["status"] == "run_error" else None) != bound["snapshot_id"]):
                raise ValidationError("Stale or mismatched evaluated trace/case/expectation binding")
            identity = digest(expected_key)
            if identity in seen:
                raise ValidationError("Duplicate evaluated result would inflate metric denominators")
            seen.add(identity)
            choice(trace["origin"], ("live", "fixture", "test_double", "unverified"), "trace origin")
            choice(judgment["outcome"], ("pass", "fail", "needs_human_review", "run_error"), "judgment outcome")
            if not isinstance(judgment["checks"], list):
                raise ValidationError("Mechanical checks must remain available for tool metrics")
            for check in judgment["checks"]:
                _require(check, ("status",), "mechanical check")
                choice(check["status"], ("pass", "fail", "error", "unknown"), "check status")
            review = judgment["review"]
            human = False
            if review is not None:
                _require(review, ("binding", "basis", "outcome"), "answer review")
                if review["binding"] != bound:
                    raise ValidationError("Answer review is stale for this evaluated trace")
                if review["basis"] == "human_review":
                    text(review.get("reviewer"), "human reviewer")
                    text(review.get("rationale"), "human review rationale")
                    _timestamp(review.get("reviewed_at"))
                    human = (judgment["basis"] == "human_review" and review["outcome"] == judgment["outcome"]
                             and judgment["outcome"] in ("pass", "fail"))
            records.append({"id": identity, "case": case, "trace": trace, "judgment": judgment,
                            "human": human, "flagged": any(c["status"] == "fail" for c in judgment["checks"])})
    _require(evaluation["counts"], ("planned_answer_records", "recorded_answer_records", "missing_answer_records"), "run accounting")
    missing = sum(r["trace"].get("synthetic_missing_record") is True for r in records)
    expected = {"planned_answer_records": len(records), "recorded_answer_records": len(records) - missing,
                "missing_answer_records": missing}
    if any(type(evaluation["counts"][k]) is not int or evaluation["counts"][k] != v for k, v in expected.items()):
        raise ValidationError("Metric denominators differ from the evaluated full result matrix")
    origins = {r["trace"]["origin"] for r in records}
    if "live" in origins and origins.intersection(("fixture", "test_double")):
        raise ValidationError("Do not combine live and simulated measurements")
    return records


def validate_reference_label(label, expected_binding):
    """Validate an independent audit label; it may contradict the tool's flag."""
    fields(label, ("schema_version", "binding", "reference_outcome", "basis", "reviewer",
                   "reviewed_at", "rationale", "independence_attested"), "independent reference")
    if type(label["schema_version"]) is not int or label["schema_version"] != 1:
        raise ValidationError("Unsupported independent-reference schema version")
    if label["binding"] != expected_binding:
        raise ValidationError("Independent reference is stale or belongs to another result")
    choice(label["reference_outcome"], ("failure", "not_failure"), "reference outcome")
    if label["basis"] != "independent_human_reference" or label["independence_attested"] is not True:
        raise ValidationError("Tool metrics require a separate independently assessed reference annotation")
    text(label["reviewer"], "reference reviewer")
    text(label["rationale"], "reference rationale")
    _timestamp(label["reviewed_at"])
    return label


def summarize_metrics(evaluation, reference_labels=()):
    """Summarize a validated evaluation without promoting drafts or fixture labels.

    A live-origin cohort excludes fixture/test-double experiments. Its conservative
    confirmed-correct denominator includes ALL planned human-reviewed-case records,
    including missing results, run errors and unresolved reviews. Conditional
    accuracy is named explicitly and accompanied by that denominator and coverage.
    """
    records = _records(evaluation)
    if not isinstance(reference_labels, (list, tuple)):
        raise ValidationError("Independent references must be a list")
    by_id = {r["id"]: r for r in records}
    references = {}
    for label in reference_labels:
        _require(label, ("binding",), "independent reference")
        _require(label["binding"], ("result_key",), "reference binding")
        identity = digest(label["binding"]["result_key"])
        if identity not in by_id or identity in references:
            raise ValidationError("Unknown or duplicate independent reference result")
        validate_reference_label(label, by_id[identity]["judgment"]["binding"])
        references[identity] = label
    live_cohort = any(r["trace"]["origin"] == "live" for r in records)
    reviewed_case_records = [r for r in records if live_cohort and r["case"]["review"]["status"] == "human_reviewed"]
    eligible = [r for r in reviewed_case_records if r["trace"]["origin"] == "live" and r["human"]]
    correct = sum(r["judgment"]["outcome"] == "pass" for r in eligible)
    exclusions = Counter()
    for r in records:
        if r["trace"]["origin"] != "live":
            exclusions["not_live_origin"] += 1
        if r["case"]["review"]["status"] != "human_reviewed":
            exclusions["draft_case"] += 1
        if r["judgment"]["outcome"] == "run_error":
            exclusions["run_error"] += 1
        if not r["human"]:
            exclusions["no_resolved_human_answer_review"] += 1
    abstentions = [r for r in reviewed_case_records if isinstance(r["trace"].get("answer"), dict)
                   and r["trace"]["answer"].get("abstained") is True]
    assessed_abstentions = [r for r in eligible if r in abstentions
                            and r["judgment"]["review"].get("abstention_judgment") in ("appropriate", "unnecessary")]
    tool_eligible = [r for r in reviewed_case_records if r["trace"]["origin"] == "live"
                     and r["judgment"]["outcome"] != "run_error"]
    reference_eligible = {r["id"]: r for r in tool_eligible if r["id"] in references}
    confusion = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
    for identity, r in reference_eligible.items():
        actual = references[identity]["reference_outcome"] == "failure"
        key = ("true_positive" if actual else "false_positive") if r["flagged"] else ("false_negative" if actual else "true_negative")
        confusion[key] += 1
    latency, missing_latency = [], 0
    for r in records:
        if r["trace"]["origin"] != "live":
            continue
        value = r["trace"].get("elapsed_seconds")
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            missing_latency += 1
        else:
            latency.append(value)
    partition_fields = {"origin": lambda r: r["trace"]["origin"], "case_review_status": lambda r: r["case"]["review"]["status"],
        "source_provenance": lambda r: r["case"]["provenance"], "split": lambda r: r["case"]["split"],
        "configuration": lambda r: r["judgment"]["binding"]["result_key"]["configuration_name"]}
    return {"schema_version": 1, "kind": "knowledge_delta_metrics", "run_id": evaluation["run_id"],
        "dataset_hash": evaluation["dataset_hash"],
        "provenance_note": "Live origin and reviewer identities are recorded claims, not authenticated execution or identities. Independent reference means a separately attested procedure, not necessarily another person or a blind review.",
        "accounting": {"planned_answer_records": len(records),
            "recorded_answer_records": evaluation["counts"]["recorded_answer_records"],
            "missing_answer_records": evaluation["counts"]["missing_answer_records"],
            "run_errors": sum(r["judgment"]["outcome"] == "run_error" for r in records),
            "needs_human_review": sum(r["judgment"]["outcome"] == "needs_human_review" for r in records),
            "without_resolved_human_answer_review": sum(not r["human"] for r in records),
            "simulated_judgments": sum(r["judgment"]["basis"] == "fixture" for r in records),
            "automatic_failure_flags": sum(r["flagged"] for r in records)},
        "partitions": {name: dict(Counter(key(r) for r in records)) for name, key in partition_fields.items()},
        "assistant": {"availability": "available" if eligible else "unavailable_no_eligible_human_judgments",
            "planned_reviewed_case_answer_records": len(reviewed_case_records),
            "resolved_eligible_human_judgments": len(eligible),
            "accuracy_resolved_human_judgments_only": _ratio(correct, len(eligible)),
            "confirmed_correct_per_planned_reviewed_case_answer": _ratio(correct, len(reviewed_case_records)),
            "review_coverage": _ratio(len(eligible), len(reviewed_case_records)),
            "reviewed_case_run_errors": sum(r["judgment"]["outcome"] == "run_error" for r in reviewed_case_records),
            "reviewed_case_missing_records": sum(r["trace"].get("synthetic_missing_record") is True for r in reviewed_case_records),
            "exclusion_reasons_nonexclusive": dict(exclusions),
            "primary_wrong_version_failure_labels": _ratio(sum(r["judgment"]["review"].get("failure_kind") == "wrong_version" for r in eligible), len(eligible)),
            "primary_unsupported_answer_failure_labels": _ratio(sum(r["judgment"]["review"].get("failure_kind") == "unsupported_answer" for r in eligible), len(eligible)),
            "diagnostic_note": "Failure-label fractions count explicit primary human classifications; they do not exhaustively assess overlapping failure causes.",
            "abstention": {"records_in_reviewed_cases": len(abstentions), "unassessed_records": len(abstentions) - len(assessed_abstentions),
                "appropriate_among_assessed": _ratio(sum(r["judgment"]["review"]["abstention_judgment"] == "appropriate" for r in assessed_abstentions), len(assessed_abstentions)),
                "unnecessary_among_assessed": _ratio(sum(r["judgment"]["review"]["abstention_judgment"] == "unnecessary" for r in assessed_abstentions), len(assessed_abstentions))},
            "answer_pipeline_latency_seconds": {"observed_records": len(latency), "missing_records": missing_latency,
                "mean": sum(latency) / len(latency) if latency else None,
                "median": median(latency) if latency else None, "minimum": min(latency) if latency else None,
                "maximum": max(latency) if latency else None,
                "note": "Live-marked trace elapsed time includes retrieval and generation/error handling; it is not peak memory or isolated model inference time."}},
        "testing_tool": {"flag_policy": "At least one failed original mechanical check; post-review correctness does not define the flag.",
            "reference_labels_submitted": len(references), "eligible_reference_labels": len(reference_eligible),
            "ineligible_reference_labels": len(references) - len(reference_eligible),
            "eligible_records_without_reference": len(tool_eligible) - len(reference_eligible),
            "run_errors_excluded_from_semantic_reference_scoring": sum(r["judgment"]["outcome"] == "run_error" for r in records),
            "confusion": confusion,
            "precision": _ratio(confusion["true_positive"], confusion["true_positive"] + confusion["false_positive"]),
            "recall": _ratio(confusion["true_positive"], confusion["true_positive"] + confusion["false_negative"]),
            "reference_coverage": _ratio(len(reference_eligible), len(tool_eligible)),
            "needs_human_review": sum(r["judgment"]["outcome"] == "needs_human_review" for r in records)}}
