"""Reproduce final study accounting; semantic AI proposals stay separate from truth."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.evaluation_study import inventory, verify_protocol, verify_result
from knowledge_delta.evaluation import evaluate_run, result_key
from knowledge_delta.metrics import summarize_metrics
from knowledge_delta.validation import ValidationError, digest, read_json


def summarize(root, study_path, protocol_path):
    folder = (root / study_path).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise ValidationError("Study must remain project-local")
    execution = read_json(folder / "summary.json")
    if execution["status"] not in ("completed_ungraded", "completed_with_run_errors_ungraded"):
        raise ValidationError("Study is not complete; do not turn partial execution into final results")
    protocol = verify_protocol(root, protocol_path)
    entries, definitions, _ = inventory(root)
    if len(execution["runs"]) != len(entries) or execution["protocol_id"] != protocol["protocol_id"]:
        raise ValidationError("Study bundle/protocol matrix differs")
    totals = Counter(planned=240, recorded=0, run_errors=0, structured=0, policy_abstentions=0,
                     chat_attempts=0, completed_model_responses=0, human_answer_reviews=0)
    by_configuration = defaultdict(Counter)
    run_rows, traces, expectations = [], {}, {}
    for entry, recorded in zip(entries, execution["runs"]):
        if entry["path"] != recorded["path"]:
            raise ValidationError("Bundle order/identity changed")
        raw_path = root / recorded["raw"].replace("\\", "/")
        if not raw_path.resolve().is_relative_to(root.resolve()):
            raise ValidationError("Raw run path escapes project")
        raw = raw_path.read_bytes()
        if sha256(raw).hexdigest() != recorded["raw_sha256"]:
            raise ValidationError("Retained raw run hash changed")
        run = json.loads(raw)
        planned = len(entry["dataset"]["cases"]) * 4
        verify_result(run, planned, protocol["model_digest"])
        evaluation = evaluate_run(run, entry["dataset"], entry["relations"], snapshots=entry["snapshots"])
        cases = {c["case_id"]: c for c in entry["dataset"]["cases"]}
        totals["recorded"] += len(run["results"])
        totals["human_answer_reviews"] += evaluation["counts"]["human_answer_reviews"]
        latency = defaultdict(list)
        for row in run["results"]:
            key = digest(result_key(run, row))
            traces[key] = row
            expectations[key] = cases[row["case_id"]]["expectations"][row["snapshot_slot"]]
            cohort = by_configuration[row["configuration_name"]]
            cohort["planned"] += 1
            cohort["recorded"] += 1
            name = "run_errors" if row["status"] == "run_error" else "structured"
            totals[name] += 1
            cohort[name] += 1
            policy = row.get("answer_origin") == "policy_abstention"
            totals["policy_abstentions"] += policy
            cohort["policy_abstentions"] += policy
            generation = row.get("generation") or {}
            totals["chat_attempts"] += len(generation.get("attempts", []))
            totals["completed_model_responses"] += generation.get("generation_performed") is True
            elapsed = row.get("elapsed_seconds")
            if isinstance(elapsed, (int, float)):
                latency[name].append(elapsed)
        run_rows.append({"path": entry["path"], "run_id": run["run_id"], "raw_sha256": recorded["raw_sha256"],
            "counts": run["counts"], "official_judgments": evaluation["counts"]["answer_outcomes"],
            "metrics": summarize_metrics(evaluation), "elapsed_seconds": run["elapsed_seconds"],
            "latency_seconds": {k: {"count": len(v), "median": median(v), "minimum": min(v), "maximum": max(v)}
                                for k, v in latency.items()}})
    if totals["recorded"] != 240 or execution["recorded_main_records"] != 240:
        raise ValidationError("Full main matrix missing")
    variability_path = folder / "development-variability.json"
    raw = variability_path.read_bytes()
    if sha256(raw).hexdigest() != execution["variability_raw_sha256"]:
        raise ValidationError("Variability raw run hash changed")
    variability = json.loads(raw)
    verify_result(variability, 36, protocol["model_digest"])
    base = entries[0]
    subset = dict(base["dataset"], cases=[c for c in base["dataset"]["cases"] if c["case_id"] in protocol["variability_cases"]])
    relations = dict(base["relations"], dataset_hash=digest(subset), relations=[
        r for r in base["relations"]["relations"] if r["case_id"] in protocol["variability_cases"]])
    evaluate_run(variability, subset, relations, snapshots=base["snapshots"])
    groups = defaultdict(list)
    for row in variability["results"]:
        groups[(row["case_id"], row["configuration_name"], row["snapshot_slot"])].append(row)
    variations = []
    for key, rows in groups.items():
        answers = [digest(r["answer"]) for r in rows if r["status"] == "answered_pending_review"]
        variations.append({"case_id": key[0], "configuration": key[1], "snapshot_slot": key[2],
            "planned_repetitions": 3, "recorded": len(rows), "run_errors": sum(r["status"] == "run_error" for r in rows),
            "valid_answers": len(answers), "distinct_answer_objects": len(set(answers)),
            "semantic_difference_judged": False})
    proposals, proposed_counts, covered = [], Counter(), set()
    analysis = root / "docs/evidence/milestone5-analysis"
    for file in sorted(analysis.glob("*-assessments.json")):
        report = read_json(file)
        if (report.get("kind") != "provisional_agent_assessment" or report.get("human_review") is not False
                or report.get("independent_reference") is not False or report.get("provisional") is not True):
            raise ValidationError("AI assessment must retain explicit non-human/provisional provenance")
        for item in report["records"]:
            key = digest(item["result_key"])
            if key not in traces or key in covered or digest(traces[key]) != item["trace_hash"]:
                raise ValidationError("Stale, duplicate or foreign AI assessment")
            if digest(expectations[key]) != item["expectation_hash"]:
                raise ValidationError("AI assessment expectation changed")
            if item["proposed_outcome"] not in ("pass", "fail", "needs_human_review", "run_error"):
                raise ValidationError("Unknown provisional AI assessment outcome")
            if traces[key]["status"] == "run_error" and item["proposed_outcome"] != "run_error":
                raise ValidationError("AI analysis cannot turn a run error into a semantic judgment")
            if any(item.get(k) is not v for k, v in (("human_review", False), ("independent_reference", False), ("provisional", True))):
                raise ValidationError("AI assessment row misrepresents provenance")
            covered.add(key)
            proposed_counts[item["proposed_outcome"]] += 1
        proposals.append({"file": file.relative_to(root).as_posix(), "sha256": sha256(file.read_bytes()).hexdigest(),
                          "assessor": report["assessor"], "records": len(report["records"])})
    return {"kind": "verified_study_accounting", "protocol_id": protocol["protocol_id"], "execution_run_id": execution["run_id"],
        "definitions": definitions, "owner_approved_definitions": protocol["user_approved_definitions"],
        "main": dict(totals), "by_configuration": {k: dict(v) for k, v in by_configuration.items()}, "runs": run_rows,
        "variability": {"counts": variability["counts"], "groups": variations, "answer_cache_used": False},
        "provisional_ai_review": {"assessed": len(covered), "unassessed": 240-len(covered),
                                  "proposed_outcomes": dict(proposed_counts), "files": proposals,
                                  "human_review": False, "independent_ground_truth": False, "benchmark_accuracy_measured": False},
        "limitations": ["Owner blanket approval does not establish individual human case review.",
            "AI-assisted proposals are not human judgments, deterministic correctness checks or independent reference labels.",
            "Reported latencies reflect execution order and concurrent desktop/packaging workload; no causal speedup is inferred.",
            "Formatting controls are whitespace-only; empty removal snapshots test policy abstention rather than model generation."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("runs/milestone5-study"))
    parser.add_argument("--protocol", type=Path, default=Path("runs/milestone5-study-protocol.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = summarize(ROOT, args.study, args.protocol)
        output = (ROOT / args.output).resolve()
        targets = [output.with_suffix(s) for s in (".json", ".html")]
        if not output.is_relative_to(ROOT) or any(p.exists() for p in targets):
            raise ValidationError("Choose new project-local JSON/HTML output paths")
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        targets[0].write_text(payload + "\n", encoding="utf-8")
        targets[1].write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>KnowledgeDelta study evidence</title><style>body{font:15px/1.6 system-ui;max-width:1100px;margin:32px auto;padding:24px;color:#172c38}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f7f5;padding:24px}</style><h1>Verified study accounting</h1><p>Execution and mechanical checks are separate from provisional AI-assisted semantic assessments.</p><pre>' + escape(payload) + '</pre></html>', encoding="utf-8")
        print(json.dumps({"status": "passed", "main": result["main"], "outputs": list(map(str, targets))}))
        return 0
    except (ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
