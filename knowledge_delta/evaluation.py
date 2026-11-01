"""Evidence-bound judgments. Successful mechanical checks never imply semantic pass."""
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from .cases import validate_dataset
from .questions import QuestionInput
from .responses import parse_answer
from .snapshots import Snapshot
from .validation import ValidationError, choice, digest, fields, text, _unique_object, _reject_constant

OUTCOMES = ("pass", "fail", "needs_human_review", "run_error")
RELATIONS = ("should_change", "should_remain", "undetermined")
FAILURE_KINDS = ("incorrect_answer", "retained_previous_behavior", "wrong_version",
                 "unsupported_answer", "unnecessary_abstention", "invalid_response",
                 "citation_version_mismatch", "other")


def _require(value, names, label):
    if not isinstance(value, dict) or any(name not in value for name in names):
        raise ValidationError(f"{label}: expected an object containing {', '.join(names)}")


def result_key(run, trace):
    _require(run, ("run_id",), "run")
    _require(trace, ("case_id", "configuration_name", "repetition", "snapshot_slot"), "trace identity")
    repetition = trace["repetition"]
    if type(repetition) is not int or repetition < 1:
        raise ValidationError("Result repetition must be a positive integer")
    return {"run_id": text(run["run_id"], "run_id"),
            "case_id": text(trace["case_id"], "case_id"),
            "configuration_name": text(trace["configuration_name"], "configuration_name"),
            "repetition": repetition,
            "snapshot_slot": choice(trace["snapshot_slot"], ("before", "after"), "snapshot_slot")}


def binding(run, trace, dataset, case, *, snapshots=None):
    _require(dataset, ("cases", "snapshot_ids"), "dataset")
    _require(case, ("case_id", "expectations", "target", "requested_version"), "case")
    if not isinstance(dataset["cases"], list):
        raise ValidationError("Dataset cases must be a list")
    key = result_key(run, trace)
    if key["case_id"] != case["case_id"] or case not in dataset["cases"]:
        raise ValidationError("Review case does not belong to this result/dataset")
    dataset_hash = digest(dataset)
    if run.get("dataset_hash") is not None and run["dataset_hash"] != dataset_hash:
        raise ValidationError("Run was produced for a different dataset revision")
    slot = key["snapshot_slot"]
    _require(run.get("snapshots"), ("before", "after"), "run snapshots")
    _require(dataset["snapshot_ids"], ("before", "after"), "dataset snapshots")
    snapshot_id = run["snapshots"][slot]
    if dataset["snapshot_ids"][slot] != snapshot_id or trace.get("snapshot_id", snapshot_id) != snapshot_id:
        raise ValidationError("Result snapshot does not match the dataset")
    if snapshots is not None and trace.get("status") != "run_error":
        snapshot = snapshots[slot]
        if snapshot.snapshot_id != snapshot_id:
            raise ValidationError("Loaded source snapshot differs from the trace")
        if not isinstance(trace.get("retrieved_passages"), list):
            raise ValidationError("Answered trace requires its supplied source passages")
        for passage in trace["retrieved_passages"]:
            _require(passage, ("document_id", "software_versions", "source_reference", "source_revision", "text"), "source passage")
            document = snapshot.document(text(passage["document_id"], "source document ID"))
            if (not isinstance(passage["software_versions"], (list, tuple))
                    or tuple(passage["software_versions"]) != document.software_versions
                    or passage["source_reference"] != document.source_reference
                    or passage["source_revision"] != document.source_revision
                    or text(passage["text"], "source text") not in document.content):
                raise ValidationError("Trace evidence does not match its document contents/applicability/source metadata")
    if trace.get("status") != "run_error" and "question" not in trace:
        raise ValidationError("Answered trace is missing its question/version/context")
    if "question" in trace and trace["question"] != QuestionInput.from_case(case, slot).__dict__:
        raise ValidationError("Trace question/version/context differs from the fixed case input")
    if trace.get("status") != "run_error":
        expected_version = case["requested_version"] if case["target"] == "explicit_version" else None
        if case["target"] == "snapshot_default":
            if snapshots is None:
                raise ValidationError("Snapshot-default judgments require loaded, trusted snapshot manifests")
            expected_version = snapshots[slot].default_version
            if snapshots[slot].snapshot_id != snapshot_id:
                raise ValidationError("Loaded snapshot differs from this result")
            if expected_version is None:
                raise ValidationError("Snapshot-default trace lacks the manifest's declared default")
        if "effective_version" not in trace or trace["effective_version"] != expected_version:
            raise ValidationError("Trace silently changed the requested software-version target")
    return {"result_key": key, "dataset_hash": dataset_hash, "case_hash": digest(case),
            "expectation_hash": digest(case["expectations"][slot]),
            "snapshot_id": snapshot_id, "trace_hash": digest(trace)}


def _context_check(trace, passages):
    if trace.get("answer_origin") == "policy_abstention":
        if (passages or trace.get("generation_attempted") is not False
                or trace.get("generation_performed") is not False
                or trace.get("generation") is not None
                or not isinstance(trace.get("answer"), dict) or trace["answer"].get("abstained") is not True):
            return "Policy abstention must have no supplied evidence or generation and must abstain"
        return None
    try:
        messages = trace["prompt"]["messages"]
        if not isinstance(messages, list) or len(messages) != 2 or messages[0]["role"] != "system" or messages[1]["role"] != "user":
            return "Recorded answering messages have an invalid shape"
        request = json.loads(messages[1]["content"], object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        expected = [{name: passage[name] for name in ("chunk_id", "document_id", "software_versions",
                     "source_reference", "source_revision", "text")} for passage in passages]
        if digest(request["evidence"]) != digest(expected):
            return "Recorded prompt evidence differs from retrieved/supplied passages"
        q = trace["question"]
        if any(request[name] != q[name] for name in ("question", "target", "requested_version", "target_context")):
            return "Recorded prompt question/context differs from the case input"
        if request["snapshot_id"] != trace["snapshot_id"] or request["effective_version"] != trace["effective_version"]:
            return "Recorded prompt snapshot/version differs from the trace"
        if trace["origin"] == "fixture":
            if trace.get("prompt_origin") != "fixture_simulated" or trace.get("generation_performed") is not False or trace.get("generation_attempted") is not False:
                return "Fixture prompts must be explicitly simulated, with no generation"
        else:
            generation = trace["generation"]
            if (generation["request"]["messages"] != messages or generation["answer"] != trace["answer"]
                    or generation["request"]["format"] != trace["prompt"]["format"]):
                return "Actual generation request/answer differs from the recorded prompt/answer"
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        return f"Missing or invalid supplied-context trace: {exc}"
    return None


def mechanical_checks(trace, case, slot):
    """Only schema/citation/applicability checks; no word matching or semantic grader."""
    if trace["status"] == "run_error":
        return [{"check_id": "run_status", "status": "error", "detail": trace.get("error") or "Run error"}]
    if trace["status"] != "answered_pending_review":
        return [{"check_id": "trace_integrity", "status": "error", "detail": "Unknown raw answering status"}]
    passages = trace.get("retrieved_passages")
    if not isinstance(passages, list):
        return [{"check_id": "trace_integrity", "status": "error", "detail": "Retrieved context is missing"}]
    context_error = _context_check(trace, passages)
    if context_error:
        return [{"check_id": "trace_integrity", "status": "error", "detail": context_error}]
    chunks, seen = [], set()
    for passage in passages:
        if not isinstance(passage, dict) or not isinstance(passage.get("chunk_id"), str):
            return [{"check_id": "trace_integrity", "status": "error", "detail": "Invalid chunk identity"}]
        identity = passage["chunk_id"]
        scope = passage.get("software_versions")
        if (identity in seen or not isinstance(scope, (tuple, list))
                or any(not isinstance(version, str) or not version for version in scope)):
            return [{"check_id": "trace_integrity", "status": "error", "detail": "Duplicate chunk or invalid applicability metadata"}]
        if passage.get("snapshot_id") != trace.get("snapshot_id"):
            return [{"check_id": "trace_integrity", "status": "error", "detail": "Evidence belongs to a different snapshot"}]
        seen.add(identity)
        chunks.append(SimpleNamespace(chunk_id=identity, software_versions=scope))
    try:
        answer = parse_answer(json.dumps(trace.get("answer"), ensure_ascii=False, allow_nan=False), chunks)
    except (ValidationError, ValueError, TypeError, RecursionError) as exc:
        return [{"check_id": "answer_schema_and_citations", "status": "fail", "failure_kind": "invalid_response", "detail": str(exc)}]
    checks = [{"check_id": "answer_schema_and_citations", "status": "pass", "detail": "Valid structure and citation membership only; semantic correctness unjudged"}]
    effective = case["requested_version"] if case["target"] == "explicit_version" else trace.get("effective_version")
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for identity in answer.citations:
        scope = by_id[identity].software_versions
        status = "unknown" if effective is None or not scope else "pass" if effective in scope else "fail"
        checks.append({"check_id": "citation_version:" + identity, "status": status,
                       "failure_kind": "citation_version_mismatch" if status == "fail" else None,
                       "detail": "Citation applicability: " + status})
    return checks


def _review_time(value):
    text(value, "reviewed_at")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            raise ValueError("timezone required")
    except ValueError as exc:
        raise ValidationError("Review timestamp must be ISO8601 with a timezone") from exc


def make_review(run, trace, dataset, case, outcome, *, basis, rationale,
                reviewer=None, failure_kind=None, abstention_judgment=None, snapshots=None):
    value = {"schema_version": 1, "binding": binding(run, trace, dataset, case, snapshots=snapshots),
             "outcome": outcome, "basis": basis, "reviewer": reviewer,
             "reviewed_at": datetime.now(timezone.utc).isoformat() if basis == "human_review" else None,
             "rationale": rationale, "failure_kind": failure_kind,
             "abstention_judgment": abstention_judgment}
    validate_review(value, run, trace, dataset, case, allow_fixture=basis == "fixture", snapshots=snapshots)
    return value


def validate_review(review, run, trace, dataset, case, *, allow_fixture=False, snapshots=None):
    fields(review, ("schema_version", "binding", "outcome", "basis", "reviewer", "reviewed_at",
                    "rationale", "failure_kind", "abstention_judgment"), "review")
    if type(review["schema_version"]) is not int or review["schema_version"] != 1:
        raise ValidationError("Unsupported review schema version")
    if review["binding"] != binding(run, trace, dataset, case, snapshots=snapshots):
        raise ValidationError("Stale or mismatched review: run, trace, case or expectations changed")
    outcome = choice(review["outcome"], OUTCOMES[:3], "review outcome")
    basis = choice(review["basis"], ("human_review", "deterministic_check", "fixture"), "review basis")
    text(review["rationale"], "review rationale")
    if review["failure_kind"] is not None:
        choice(review["failure_kind"], FAILURE_KINDS, "failure kind")
        if outcome != "fail":
            raise ValidationError("Failure kind requires a failed judgment")
    if basis == "human_review":
        text(review["reviewer"], "human reviewer")
        _review_time(review["reviewed_at"])
    elif review["reviewer"] is not None or review["reviewed_at"] is not None:
        raise ValidationError("Simulated/mechanical judgments cannot invent a human reviewer or review time")
    if basis == "fixture" and (not allow_fixture or trace.get("origin") not in ("fixture", "test_double")):
        raise ValidationError("Fixture judgments are restricted to explicitly simulated traces and reports")
    checks = mechanical_checks(trace, case, trace["snapshot_slot"])
    failures = [check for check in checks if check["status"] == "fail"]
    if outcome == "pass" and any(check["status"] in ("fail", "error") for check in checks):
        raise ValidationError("A pass cannot override an observed mechanical failure or run error")
    if failures and outcome != "fail":
        raise ValidationError("An unresolved semantic review cannot erase an observed mechanical failure")
    if basis == "deterministic_check":
        if outcome != "fail" or not failures or review["failure_kind"] not in {check["failure_kind"] for check in failures}:
            raise ValidationError("Deterministic reviews can only record justified mechanical failures, never semantic passes")
    abstention = review["abstention_judgment"]
    if abstention is not None:
        choice(abstention, ("appropriate", "unnecessary"), "abstention judgment")
        if not isinstance(trace.get("answer"), dict) or trace["answer"].get("abstained") is not True:
            raise ValidationError("Abstention judgment requires an actual abstention")
        if (abstention == "appropriate" and outcome != "pass") or (abstention == "unnecessary" and outcome != "fail"):
            raise ValidationError("Abstention judgment contradicts correctness outcome")
    return review


def judge_snapshot(run, trace, dataset, case, review=None, *, allow_fixture=False, snapshots=None):
    bound = binding(run, trace, dataset, case, snapshots=snapshots)
    checks = mechanical_checks(trace, case, trace["snapshot_slot"])
    errors = [check for check in checks if check["status"] == "error"]
    failures = [check for check in checks if check["status"] == "fail"]
    value = {"binding": bound, "outcome": "run_error" if errors else "fail" if failures else "needs_human_review",
             "basis": "run_error" if errors else "deterministic_check" if failures else "unresolved",
             "failure_kind": failures[0]["failure_kind"] if failures else None,
             "checks": checks, "review": None, "origin": trace.get("origin", "unverified"),
             "case_review_status": case["review"]["status"]}
    if review is not None:
        validate_review(review, run, trace, dataset, case, allow_fixture=allow_fixture, snapshots=snapshots)
        value["review"] = review
        if not errors:
            value.update(outcome=review["outcome"], basis=review["basis"], failure_kind=review["failure_kind"])
    return value


def validate_relation(annotation, dataset, case, *, allow_fixture=False):
    fields(annotation, ("schema_version", "case_id", "case_hash", "relation", "basis", "reviewer", "reviewed_at", "rationale"), "relation")
    if type(annotation["schema_version"]) is not int or annotation["schema_version"] != 1:
        raise ValidationError("Unsupported relation schema version")
    if annotation["case_id"] != case["case_id"] or annotation["case_hash"] != digest(case) or case not in dataset["cases"]:
        raise ValidationError("Stale or mismatched expected-change annotation")
    choice(annotation["relation"], RELATIONS, "expected relation")
    basis = choice(annotation["basis"], ("draft", "human_review", "fixture"), "relation basis")
    text(annotation["rationale"], "relation rationale")
    if basis == "human_review":
        text(annotation["reviewer"], "relation reviewer")
        _review_time(annotation["reviewed_at"])
    elif annotation["reviewer"] is not None or annotation["reviewed_at"] is not None:
        raise ValidationError("Draft/simulated relations cannot invent human reviews")
    if basis == "fixture" and not allow_fixture:
        raise ValidationError("Simulated relation requires explicit fixture mode")
    return annotation


def compare_judgments(before, after, relation=None, *, allow_fixture=False):
    """Compare judge_snapshot outputs and a validated relation, never answer text."""
    for item in (before, after):
        _require(item, ("binding", "outcome", "basis", "origin", "failure_kind"), "judgment")
    left, right = before["binding"], after["binding"]
    lk, rk = left["result_key"], right["result_key"]
    if (lk["snapshot_slot"] != "before" or rk["snapshot_slot"] != "after"
            or any(lk[name] != rk[name] for name in ("run_id", "case_id", "configuration_name", "repetition"))
            or any(left[name] != right[name] for name in ("dataset_hash", "case_hash"))):
        raise ValidationError("Comparison requires the same case/run/configuration/repetition in before/after order")
    if relation is not None:
        if relation["case_id"] != lk["case_id"] or relation["case_hash"] != left["case_hash"]:
            raise ValidationError("Expected-change annotation belongs to a different case revision")
        choice(relation["relation"], RELATIONS, "expected relation")
        choice(relation["basis"], ("draft", "human_review", "fixture"), "relation basis")
        if relation["basis"] == "human_review":
            text(relation["reviewer"], "relation reviewer")
            _review_time(relation["reviewed_at"])
    a, b = before["outcome"], after["outcome"]
    if a not in OUTCOMES or b not in OUTCOMES:
        raise ValidationError("Unknown per-snapshot judgment")
    simulated = (before["origin"] in ("fixture", "test_double") or after["origin"] in ("fixture", "test_double")
                 or before["basis"] == "fixture" or after["basis"] == "fixture"
                 or (relation is not None and relation["basis"] == "fixture"))
    if simulated and (not allow_fixture or any(item["origin"] not in ("fixture", "test_double")
            and item["outcome"] != "run_error" for item in (before, after))):
        raise ValidationError("Simulated judgments cannot grade live results")
    expected_change = relation is not None and relation["relation"] == "should_change" and relation["basis"] in ("human_review", "fixture")
    status = "needs_human_review"
    recovery = False
    if "run_error" in (a, b):
        status = "run_error"
    elif "needs_human_review" in (a, b):
        pass
    elif a == b == "fail":
        status = "incorrect_in_both_snapshots"
    elif a == "pass" and b == "fail":
        retained = after["failure_kind"] == "retained_previous_behavior" and after["basis"] in ("human_review", "fixture")
        status = "failure_to_adopt_expected_change" if expected_change and retained else "previously_correct_now_incorrect"
    elif a == b == "pass":
        status = "expected_answer_change" if expected_change else "pass"
    elif a == "fail" and b == "pass":
        status, recovery = "pass", True
    return {"status": status, "before_outcome": a, "after_outcome": b, "recovered": recovery,
            "simulated": simulated, "expected_relation": relation["relation"] if relation else "undetermined",
            "relation_basis": relation["basis"] if relation else "missing"}


def validate_relations(bundle, dataset, *, allow_fixture=False):
    fields(bundle, ("schema_version", "dataset_hash", "relations"), "relations bundle")
    if type(bundle["schema_version"]) is not int or bundle["schema_version"] != 1:
        raise ValidationError("Unsupported relations bundle version")
    if bundle["dataset_hash"] != digest(dataset):
        raise ValidationError("Expected-change annotations belong to an older dataset revision")
    if not isinstance(bundle["relations"], list):
        raise ValidationError("Relations must be a list")
    cases = {case["case_id"]: case for case in dataset["cases"]}
    result = {}
    for item in bundle["relations"]:
        if not isinstance(item, dict) or item.get("case_id") not in cases or item["case_id"] in result:
            raise ValidationError("Unknown or duplicate expected-change case")
        result[item["case_id"]] = validate_relation(item, dataset, cases[item["case_id"]], allow_fixture=allow_fixture)
    return result


def evaluate_run(run, dataset, relation_bundle, reviews=(), *, snapshots, allow_fixture=False):
    """Full matrix accounting, including missing records. Raw run data is never edited."""
    _require(run, ("run_id", "snapshots", "snapshot_defaults", "repeats", "configurations", "results", "origin"), "run")
    fields(snapshots, ("before", "after"), "loaded snapshots")
    if any(not isinstance(snapshot, Snapshot) for snapshot in snapshots.values()):
        raise ValidationError("Load actual snapshot manifests before evaluating imported runs")
    validate_dataset(dataset, snapshots["before"], snapshots["after"])
    if run["snapshots"] != dataset["snapshot_ids"] or run["snapshot_defaults"] != {slot: snapshot.default_version for slot, snapshot in snapshots.items()}:
        raise ValidationError("Run snapshot IDs/defaults differ from the trusted manifests")
    if not isinstance(run["results"], list) or not isinstance(reviews, (list, tuple)):
        raise ValidationError("Results and reviews must be lists")
    relation_map = validate_relations(relation_bundle, dataset, allow_fixture=allow_fixture)
    repetitions = run["repeats"]
    if type(repetitions) is not int or not 1 <= repetitions <= 5:
        raise ValidationError("Experiment repetitions must be 1..5")
    if not isinstance(run["configurations"], dict) or not run["configurations"]:
        raise ValidationError("Experiment must declare its configurations")
    configurations = [text(name, "configuration name") for name in run["configurations"]]
    cases = {case["case_id"]: case for case in dataset["cases"]}
    if len(cases) != len(dataset["cases"]) or not cases:
        raise ValidationError("Dataset requires distinct cases")
    traces = {}
    for trace in run["results"]:
        key = result_key(run, trace)
        compact = (key["case_id"], key["configuration_name"], key["repetition"], key["snapshot_slot"])
        if key["case_id"] not in cases or key["configuration_name"] not in configurations or key["repetition"] > repetitions:
            raise ValidationError("Trace is outside the declared experiment matrix")
        if compact in traces:
            raise ValidationError("Duplicate result record")
        choice(trace.get("origin", "unverified"), ("live", "fixture", "test_double", "unverified"), "trace origin")
        traces[compact] = trace
    origins = {trace.get("origin", "unverified") for trace in traces.values()}
    for origin in origins:
        choice(origin, ("live", "fixture", "test_double", "unverified"), "trace origin")
    derived_origin = next(iter(origins)) if len(origins) == 1 else "mixed" if origins else "unverified"
    if origins and run["origin"] != derived_origin:
        raise ValidationError("Run origin label contradicts its actual result records")
    if "live" in origins and origins.intersection(("fixture", "test_double")):
        raise ValidationError("Keep fixture and live experiments separate")
    review_map = {}
    for review in reviews:
        _require(review, ("binding",), "review")
        _require(review["binding"], ("result_key",), "review binding")
        key = review["binding"]["result_key"]
        _require(key, ("run_id", "case_id", "configuration_name", "repetition", "snapshot_slot"), "review key")
        result_key({"run_id": key["run_id"]}, key)
        compact = (key["case_id"], key["configuration_name"], key["repetition"], key["snapshot_slot"])
        if key["run_id"] != run["run_id"] or compact not in traces or compact in review_map:
            raise ValidationError("Orphaned, cross-run or duplicate review record")
        review_map[compact] = review
    rows, judgments, missing = [], [], 0
    for case in dataset["cases"]:
        for configuration in configurations:
            for repetition in range(1, repetitions + 1):
                pair, details = {}, {}
                for slot in ("before", "after"):
                    compact = (case["case_id"], configuration, repetition, slot)
                    trace = traces.get(compact)
                    if trace is None:
                        missing += 1
                        trace = {"case_id": case["case_id"], "configuration_name": configuration,
                            "repetition": repetition, "snapshot_slot": slot,
                            "snapshot_id": run["snapshots"][slot], "origin": "unverified",
                            "status": "run_error", "error": "Expected result record is missing",
                            "synthetic_missing_record": True}
                    pair[slot] = judge_snapshot(run, trace, dataset, case, review_map.get(compact), allow_fixture=allow_fixture, snapshots=snapshots)
                    judgments.append(pair[slot])
                    details[slot] = {"trace": trace, "judgment": pair[slot], "expectation": case["expectations"][slot]}
                comparison = compare_judgments(pair["before"], pair["after"], relation_map.get(case["case_id"]), allow_fixture=allow_fixture)
                rows.append({"case_id": case["case_id"], "configuration_name": configuration,
                             "repetition": repetition, "case": case, "snapshots": details,
                             "relation": relation_map.get(case["case_id"]), "comparison": comparison})
    planned = len(cases) * len(configurations) * repetitions * 2
    counts = {"cases": len(cases), "planned_answer_records": planned,
              "recorded_answer_records": len(traces), "missing_answer_records": missing,
              "comparison_records": len(rows), "human_reviewed_cases": sum(case["review"]["status"] == "human_reviewed" for case in cases.values()),
              "draft_cases": sum(case["review"]["status"] == "draft" for case in cases.values()),
              "answer_outcomes": {outcome: sum(item["outcome"] == outcome for item in judgments) for outcome in OUTCOMES},
              "human_answer_reviews": sum(item["basis"] == "human_review" for item in judgments),
              "simulated_answer_judgments": sum(item["basis"] == "fixture" for item in judgments)}
    return {"schema_version": 1, "kind": "knowledge_delta_evaluation", "run_id": run["run_id"],
            "dataset_hash": digest(dataset), "origin": derived_origin,
            "fixture_mode": allow_fixture, "counts": counts, "rows": rows,
            "semantic_note": "Mechanical success is not a semantic pass. Draft expectations and simulated judgments are not benchmark ground truth."}
