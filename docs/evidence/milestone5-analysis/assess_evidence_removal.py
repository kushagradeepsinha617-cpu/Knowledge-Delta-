"""Record a bounded, provisional reading of the frozen evidence-removal run.

The verdicts below were assigned after reading the question, expectation, answer,
citations and supplied passages for all 48 rows. This is not an automatic grader.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from knowledge_delta.evaluation import result_key
from knowledge_delta.validation import ValidationError, digest, read_json

RAW = ROOT / "runs/milestone5-study/bundle-5.json"
DATASET = ROOT / "examples/pydantic-evaluation/heldout-evidence-removed/cases.json"
OUTPUT = ROOT / "docs/evidence/milestone5-analysis/heldout-evidence-removed-assessments.json"
FROZEN_RAW_SHA256 = "153a953c8d0df975e37905f4736c27370822df395d1151ebc05e65e644408b05"
FROZEN_RUN_ID = "e551db7d6f0844579350ec41c2a8473b"

# Deliberately case-specific judgments. They are not extrapolated to other runs.
BEFORE = {
    "study-mutable-default-isolation": ("fail", "factual_contradiction", "The answer says the unhashable default is shared. Its cited passage says Pydantic deep-copies this default for each instance."),
    "study-with-json-schema-replacement": ("fail", "factual_contradiction", "The answer says WithJsonSchema merely appends keys and type may be omitted. The actually supplied passage says it overrides the base schema; the snapshot expectation additionally quotes the documentation's type-needed example. The type-needed sentence itself was not in these retrieved passages."),
    "study-schema-specification": ("pass", None, "The answer names Draft 2020-12, and its citation directly identifies that specification."),
    "study-schema-ref-definitions": ("pass", None, "The answer separates reference formatting from definition placement. The cited passage explicitly retains definitions under $defs."),
    "study-skip-json-schema": ("pass", None, "The answer names SkipJsonSchema and limits the claim to generated schema. Its citation directly supports this."),
    "study-adapter-reuse": ("fail", "factual_contradiction", "The answer recommends recreating TypeAdapter every loop. Its citation describes nontrivial construction overhead and recommends reuse."),
    "study-adapter-deferred-build": ("pass", None, "The answer gives first-use construction for validation/serialization and the rebuild() method. Both facts appear in supplied passages; the filtered answer cites only the first fragment and relies on an uncited second fragment for the full rule."),
    "study-field-after-stage": ("fail", "factual_contradiction", "The answer places an after validator before internal validation and says it may omit returning the value. The case expectation contradicts both claims. Actual retrieved passages instead describe before and plain validators; the after-validator rule was not retrieved, so the response is unsupported by its context."),
    "study-field-before-inner-validation": ("fail", "factual_contradiction", "The answer claims a before validator bypasses subsequent type validation. A supplied passage explicitly says its returned value is then validated against the annotation."),
    "study-field-plain-termination": ("needs_human_review", "incomplete_explanation", "The brief negative answer is compatible with the source, but omits the rubric's required explanation that a plain validator terminates the usual internal validation path."),
    "study-field-wrap-handler": ("fail", "factual_contradiction", "The answer says the handler must always be called and errors cannot be intercepted. The actually supplied wrap passage describes flexible control and begins the optional handler-call sentence, but cuts before its try/except detail. The case expectation contains the full source quote; the mandatory-handler claim is contradicted by the documented rule."),
    "study-annotated-validator-order": ("pass", None, "The answer gives before/wrap right-to-left and after left-to-right, as the cited ordering passage states."),
}


def main():
    raw = RAW.read_bytes()
    run = json.loads(raw)
    dataset = read_json(DATASET)
    cases = {case["case_id"]: case for case in dataset["cases"]}
    if (sha256(raw).hexdigest() != FROZEN_RAW_SHA256 or run["run_id"] != FROZEN_RUN_ID
            or run.get("dataset_hash") != digest(dataset) or len(cases) != 12
            or set(cases) != set(BEFORE) or len(run["results"]) != 48):
        raise ValidationError("Evidence-removal matrix changed; revisit all verdicts")
    records = []
    by_configuration = defaultdict(Counter)
    for row in run["results"]:
        case_id, slot = row["case_id"], row["snapshot_slot"]
        if case_id not in cases or row["status"] != "answered_pending_review":
            raise ValidationError("Unexpected case or run error; revisit verdicts")
        answer = row["answer"]
        if slot == "after":
            if (row["answer_origin"] != "policy_abstention" or row["retrieved_passages"]
                    or row["generation_performed"] or not answer["abstained"] or answer["citations"]):
                raise ValidationError("Evidence-removal policy path changed")
            outcome, kind = "pass", None
            rationale = ("The after snapshot supplies zero passages and the recorded evidence-only policy abstains "
                         "without a model call. This verifies the configured policy path, not that the underlying fact became false.")
        elif slot == "before":
            if row["answer_origin"] != "live" or not row["generation_performed"] or answer["abstained"]:
                raise ValidationError("Before-snapshot generation path changed")
            cited = set(answer["citations"])
            supplied = {p["chunk_id"] for p in row["retrieved_passages"]}
            if not cited or not cited <= supplied:
                raise ValidationError("Before-snapshot citation set changed")
            outcome, kind, rationale = BEFORE[case_id]
        else:
            raise ValidationError("Unknown snapshot slot")
        by_configuration[row["configuration_name"]][outcome] += 1
        records.append({"result_key": result_key(run, row), "snapshot_id": row["snapshot_id"],
                        "trace_hash": digest(row), "expectation_hash": digest(cases[case_id]["expectations"][slot]),
                        "proposed_outcome": outcome, "failure_kind": kind, "rationale": rationale,
                        "cited_chunk_ids": answer["citations"], "assessor": "Codex AI-assisted",
                        "human_review": False, "independent_reference": False, "provisional": True})
    counts = Counter(r["proposed_outcome"] for r in records)
    report = {"schema_version": 1, "kind": "provisional_agent_assessment",
              "raw_run_path": RAW.relative_to(ROOT).as_posix(), "raw_run_sha256": sha256(raw).hexdigest(),
              "run_id": run["run_id"], "dataset_hash": digest(dataset),
              "assessed_at": datetime.now(timezone.utc).isoformat(), "assessor": "Codex AI-assisted",
              "human_review": False, "independent_reference": False, "provisional": True,
              "scope_note": "All 48 actual rows were read against expectations, answers, citations and supplied passages. The after snapshot has no context and records policy abstentions. These proposals are not human grades or benchmark truth.",
              "assessment_policy": "Factual contradiction fails; incomplete rubric/evidence support remains unresolved. Exact recorded passages, not keyword presence alone, inform these case-specific proposals.",
              "summary": {"planned_records": 48, "assessed_records": len(records),
                          "proposed_outcomes": dict(counts),
                          "by_configuration": {key: dict(value) for key, value in by_configuration.items()},
                          "human_answer_judgments_created": 0, "benchmark_accuracy_measured": False,
                          "findings": ["All 24 after-snapshot rows abstain through the deterministic empty-context policy; no model generation occurs there.",
                                       "Twelve before-snapshot answers contradict their supplied evidence across six case definitions.",
                                       "Two plain-validator answers leave the required short-circuit mechanism unstated and need human review.",
                                       "Removing evidence tests the configured evidence-only response, not a change in Pydantic behavior."]},
              "records": records}
    if OUTPUT.exists():
        raise ValidationError("Assessment already exists; do not overwrite")
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "provisional_only", "records": len(records), "outcomes": dict(counts),
                      "output": OUTPUT.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
