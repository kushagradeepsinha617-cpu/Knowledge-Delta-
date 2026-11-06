"""Offline review packet and review-gated, hash-bound local study protocol."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from html import escape
import json
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.cases import validate_dataset
from knowledge_delta.evaluation import validate_relations
from knowledge_delta.pipeline import RunConfiguration
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, digest, read_json
from scripts.prepare_evaluation_study import prepare
from scripts.run_checks import project_source

MODEL = "qwen3:1.7b"
CONFIGURATION = asdict(RunConfiguration(max_output_tokens=256))
REPEAT_CASES = ["pydantic-serialization", "pydantic-optional", "pydantic-union"]


def verify_result(result, expected_records, model_digest):
    """Recorded execution counts and both model observations must agree."""
    rows = result.get("results")
    counts = result.get("counts")
    if not isinstance(rows, list) or not isinstance(counts, dict):
        raise ValidationError("Run lacks its result matrix/counts")
    errors = sum(row.get("status") == "run_error" for row in rows)
    if (len(rows) != expected_records or counts.get("planned") != expected_records
            or counts.get("recorded") != len(rows) or counts.get("run_errors") != errors):
        raise ValidationError("Run has missing or contradictory planned/recorded/error counts")
    for row in rows:
        generation = row.get("generation")
        if isinstance(generation, dict):
            for field in ("model_digest", "model_digest_after"):
                if generation.get(field) not in (None, model_digest):
                    raise ValidationError("Retained run violates frozen model identity: " + field)


def approval_coverage(root, entries):
    path = root / "examples/pydantic-evaluation/user-approval.json"
    if not path.is_file():
        return 0
    ledger = read_json(path)
    if (ledger.get("kind") != "user_blanket_case_approval" or ledger.get("approval_scope") != "case definitions and expected relations"
            or ledger.get("item_by_item_human_review_verified") is not False):
        raise ValidationError("Approval ledger must distinguish blanket authorization from item-level human review")
    records = ledger.get("records")
    if not isinstance(records, list) or len({r["case_id"] for r in records}) != len(records):
        raise ValidationError("Invalid approval ledger records")
    actual = []
    for entry in entries:
        relations = {r["case_id"]: r for r in entry["relations"]["relations"]}
        for case in entry["dataset"]["cases"]:
            actual.append({"case_id": case["case_id"], "case_hash": digest(case),
                           "relation_hash": digest(relations.get(case["case_id"])),
                           "dataset_hash": digest(entry["dataset"]), "snapshot_ids": entry["dataset"]["snapshot_ids"]})
    if sorted(actual, key=lambda r: r["case_id"]) != sorted(records, key=lambda r: r["case_id"]):
        raise ValidationError("Approval ledger is stale; case definitions or relations changed")
    return len(actual)


def output_path(root, relative):
    path = (root / relative).resolve()
    if (not path.is_relative_to(root.resolve())
            or not path.is_relative_to((root / "runs").resolve()) or path.exists()):
        raise ValidationError("Choose a new project-local runs/ output; existing records are preserved")
    return path


def inventory(root):
    plan = prepare(root)
    paths = plan["existing_development"] + [b["path"] for b in plan["new_bundles"]]
    entries, ids, families = [], set(), {}
    counts = {"development": 0, "held_out": 0, "human_reviewed": 0, "draft": 0,
              "human_relations": 0, "cases": 0}
    for relative in paths:
        base = root / relative
        snapshots = {s: load_snapshot(base / s / "manifest.json") for s in ("before", "after")}
        dataset, relations = read_json(base / "cases.json"), read_json(base / "relations.json")
        validate_dataset(dataset, snapshots["before"], snapshots["after"])
        relation_map = validate_relations(relations, dataset)
        for case in dataset["cases"]:
            if case["case_id"] in ids:
                raise ValidationError("Study case IDs must be globally unique")
            ids.add(case["case_id"])
            # Both generic-model contracts are development; record the related-family grouping.
            family = {"pydantic-generic-upper-bound": "pydantic-generic-models"}.get(case["family_id"], case["family_id"])
            if family in families and families[family] != case["split"]:
                raise ValidationError("Related family crosses study split: " + family)
            families[family] = case["split"]
            counts[case["split"]] += 1
            counts[case["review"]["status"]] += 1
            counts["cases"] += 1
            counts["human_relations"] += relation_map.get(case["case_id"], {}).get("basis") == "human_review"
        entries.append({"path": relative, "dataset": dataset, "relations": relations,
                        "snapshots": snapshots})
    if (counts["development"], counts["held_out"], counts["cases"]) != (20, 40, 60):
        raise ValidationError("Study must contain exactly 20 development and 40 held-out cases")
    return entries, counts, families


def review_packet(root, output):
    entries, counts, _ = inventory(root)
    lines = ["# KnowledgeDelta: 60-case definition review", "",
        "DRAFT REVIEW PACKET — no new human approval or live benchmark is implied.", "",
        "Review each question, version, both expectations, source passages, rubric and expected relation.",
        "Case-definition approval is not approval of a future model answer. Tell Codex the exact case IDs you approve or correct.",
        "Held-out means withheld from project tuning, not unseen by model pretraining or independently authored.", "",
        "Formatting-only controls change whitespace. Empty evidence-removal snapshots test policy abstention, not inference.", "",
        f"Current definitions: {counts['human_reviewed']} reviewed, {counts['draft']} draft. Expected relations separately reviewed: {counts['human_relations']}/60.", ""]
    bindings = []
    for entry in entries:
        relations = {r["case_id"]: r for r in entry["relations"]["relations"]}
        for case in entry["dataset"]["cases"]:
            relation = relations.get(case["case_id"])
            bindings.append({"path": entry["path"], "case_id": case["case_id"], "case_hash": digest(case),
                             "dataset_hash": digest(entry["dataset"]), "relation_hash": digest(relation)})
            lines += [f"## {case['case_id']}", "", f"Split: {case['split']} | Family: {case['family_id']} | Status: {case['review']['status']}",
                      "", case["question"], "", f"Requested version: {case['requested_version'] or 'unspecified; do not invent release applicability'}.",
                      f"Condition: {case['category']} ({case['provenance']}).", ""]
            for slot in ("before", "after"):
                expected = case["expectations"][slot]
                lines += [f"### {slot.title()}", f"Behavior: {expected['behavior']}", "",
                          expected["answer"] or "Abstain under the evidence-only policy.", "", "Rubric: " + expected["rubric"], ""]
                for evidence in expected["evidence"]:
                    doc = entry["snapshots"][slot].document(evidence["document_id"])
                    lines += ["Source: " + doc.source_reference, "", "Exact supporting passage:", "", evidence["quote"], ""]
            lines += ["Expected relation: " + (relation["relation"] if relation else "missing"),
                      "Relation review: " + (relation["basis"] if relation else "missing"), "",
                      "Review binding: " + digest(bindings[-1]), ""]
    path = output_path(root, output)
    path.mkdir(parents=True)
    markdown = "\n".join(lines)
    (path / "review.md").write_text(markdown, encoding="utf-8")
    (path / "review.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KnowledgeDelta case review</title><style>body{max-width:960px;margin:32px auto;padding:0 24px;font:15px/1.65 system-ui;color:#172c38;background:#f5f8f6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:28px;border:1px solid #dce5e7;border-radius:12px}a{color:#166b65}</style><h1>Case-definition review packet</h1><p>Drafts require your actual review. No model answers are graded here.</p><pre>' + escape(markdown) + '</pre></html>', encoding="utf-8")
    (path / "bindings.json").write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    return {"status": "review_packet_written", "output": str(path), "counts": counts,
            "human_reviews_created": False, "inference_performed": False}


def freeze(root, output):
    entries, counts, families = inventory(root)
    owner_approved = approval_coverage(root, entries)
    if (counts["human_reviewed"] != 60 or counts["human_relations"] != 60) and owner_approved != 60:
        raise ValidationError(f"Review gate: {counts['draft']} draft cases and {60-counts['human_relations']} unreviewed expected relations remain. No held-out inference started.")
    path = output_path(root, output)
    # Import/connect only after the review gate passes. Never pulls a model.
    from knowledge_delta.ollama import OllamaClient
    model_digest = OllamaClient(MODEL)._inventory()
    if not model_digest:
        raise ValidationError("A recorded local model digest is required")
    protocol = {"schema_version": 1, "kind": "frozen_60_case_study", "frozen_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts, "user_approved_definitions": owner_approved,
        "review_provenance": "Item-level human reviews and user blanket approval are counted separately; neither grades actual answers.",
        "families": families, "model": MODEL, "model_digest": model_digest,
        "configuration": CONFIGURATION, "embedding_backend": "onnxruntime", "chunk_tokens": 128,
        "overlap_tokens": 16, "repeats": 1, "variability_cases": REPEAT_CASES, "variability_repeats": 3,
        "answer_cache_used": False, "order": "existing development, development extension, then held-out bundles in study-plan order",
        "source": project_source(root), "human_answer_judgments": "separate; never inferred from case approval"}
    protocol["protocol_id"] = digest(protocol)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(protocol, stream, indent=2)
    return {"status": "frozen", "protocol_id": protocol["protocol_id"], "output": str(path)}


def verify_protocol(root, path):
    path = (root / path).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_relative_to((root / "runs").resolve()):
        raise ValidationError("Select a project-local runs/ protocol")
    protocol = read_json(path)
    plain = dict(protocol)
    identity = plain.pop("protocol_id", None)
    if (protocol.get("kind") != "frozen_60_case_study" or digest(plain) != identity
            or protocol.get("model") != MODEL or protocol.get("configuration") != CONFIGURATION
            or protocol.get("embedding_backend") != "onnxruntime"
            or protocol.get("chunk_tokens") != 128 or protocol.get("overlap_tokens") != 16
            or protocol.get("repeats") != 1 or protocol.get("variability_repeats") != 3
            or protocol.get("variability_cases") != REPEAT_CASES or protocol.get("answer_cache_used") is not False
            or protocol.get("source") != project_source(root)):
        raise ValidationError("Frozen inputs/configuration/source changed; do not tune or silently rebind this study")
    entries, counts, _ = inventory(root)
    if ((counts["human_reviewed"] != 60 or counts["human_relations"] != 60)
            and approval_coverage(root, entries) != 60):
        raise ValidationError("Frozen study no longer has complete human definition reviews")
    return protocol


def run(root, protocol_path, output):
    protocol = verify_protocol(root, protocol_path)
    directory = output_path(root, output)
    from knowledge_delta.local_environment import configure_offline_environment
    from knowledge_delta.onnx_embeddings import LocalOnnxMiniLM
    from knowledge_delta.ollama import OllamaClient
    from knowledge_delta.experiments import run_dataset
    from knowledge_delta.review_workflow import ReviewSession
    from knowledge_delta.workflow import export_report
    configure_offline_environment(root)
    client = OllamaClient(protocol["model"])
    if client._inventory() != protocol["model_digest"]:
        raise ValidationError("Local model differs from the frozen digest")
    embedder = LocalOnnxMiniLM(root / ".tools/models/minilm-onnx", root)
    entries, _, _ = inventory(root)
    directory.mkdir(parents=True)
    summary = {"kind": "study_execution", "protocol_id": protocol["protocol_id"], "run_id": uuid4().hex,
               "status": "running", "semantic_correctness_measured": False, "runs": [],
               "planned_main_records": 240, "planned_variability_records": 36}
    def save():
        summary["recorded_main_records"] = sum(r["counts"]["recorded"] for r in summary["runs"])
        summary["missing_main_records"] = summary["planned_main_records"] - summary["recorded_main_records"]
        summary["main_run_errors"] = sum(r["counts"]["run_errors"] for r in summary["runs"])
        temporary = directory / "summary.tmp"
        temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        temporary.replace(directory / "summary.json")
    save()
    try:
        for number, entry in enumerate(entries):
            verify_protocol(root, protocol_path)
            if client._inventory() != protocol["model_digest"]:
                raise ValidationError("Local model changed between study bundles")
            print(json.dumps({"phase": "bundle", "number": number+1, "path": entry["path"]}), flush=True)
            dataset = entry["dataset"]
            result = run_dataset(dataset, entry["snapshots"]["before"], entry["snapshots"]["after"], embedder, client,
                                 configuration=RunConfiguration(**protocol["configuration"]), repeats=protocol["repeats"],
                                 token_limit=protocol["chunk_tokens"], overlap_tokens=protocol["overlap_tokens"])
            raw = directory / f"bundle-{number+1}.json"
            with raw.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
            generations = [row["generation"] for row in result["results"] if isinstance(row.get("generation"), dict)]
            actual_counts = dict(result["counts"], recorded=len(result["results"]),
                                 run_errors=sum(r.get("status") == "run_error" for r in result["results"]))
            summary["runs"].append({"path": entry["path"], "raw": str(raw.relative_to(root)),
                "raw_sha256": sha256(raw.read_bytes()).hexdigest(), "counts": actual_counts, "reported_counts": result["counts"],
                "origin": result["origin"],
                "model_responses": sum(g.get("generation_performed") is True for g in generations),
                "chat_attempts": sum(len(g.get("attempts", [])) for g in generations),
                "policy_abstentions": sum(row.get("answer_origin") == "policy_abstention" for row in result["results"])})
            save()  # Record retained answers even if later validation/export fails.
            verify_result(result, len(dataset["cases"]) * 4, protocol["model_digest"])
            verify_protocol(root, protocol_path)
            base = entry["path"]
            session = ReviewSession(root, before=base+"/before/manifest.json", after=base+"/after/manifest.json",
                                    dataset=base+"/cases.json", relations=base+"/relations.json", run_path=raw)
            export_report(root, directory / f"report-{number+1}", session.evaluate())
            save()
        # Fixed development-only variability subset, separate from the 60-case main counts.
        entry = entries[0]
        subset = dict(entry["dataset"], cases=[c for c in entry["dataset"]["cases"] if c["case_id"] in REPEAT_CASES])
        if len(subset["cases"]) != 3:
            raise ValidationError("Fixed variability subset missing")
        verify_protocol(root, protocol_path)
        if client._inventory() != protocol["model_digest"]:
            raise ValidationError("Local model changed before the variability study")
        result = run_dataset(subset, entry["snapshots"]["before"], entry["snapshots"]["after"], embedder, client,
                             repeats=protocol["variability_repeats"], configuration=RunConfiguration(**protocol["configuration"]),
                             token_limit=protocol["chunk_tokens"], overlap_tokens=protocol["overlap_tokens"])
        with (directory / "development-variability.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        summary["variability_counts"] = result["counts"]
        summary["variability_raw_sha256"] = sha256((directory / "development-variability.json").read_bytes()).hexdigest()
        save()
        verify_result(result, 36, protocol["model_digest"])
        verify_protocol(root, protocol_path)
        if (client._inventory() != protocol["model_digest"] or any(
                row["generation"].get("model_digest") not in (None, protocol["model_digest"])
                for row in result["results"] if isinstance(row.get("generation"), dict))):
            raise ValidationError("Variability run violates the frozen model identity")
        if summary["recorded_main_records"] != 240 or summary["missing_main_records"] != 0:
            raise ValidationError("Main study matrix incomplete; cannot declare completion")
        summary["status"] = ("completed_with_run_errors_ungraded" if summary["main_run_errors"] or result["counts"]["run_errors"]
                             else "completed_ungraded")
        save()
    except Exception as exc:
        summary.update(status="interrupted_or_run_error", error=str(exc))
        save()
        raise
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "review-packet", "freeze", "run"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "status":
            _, counts, families = inventory(ROOT)
            result = {"counts": counts, "family_count": len(families), "inference_performed_by_this_command": False,
                      "historical_runs_inspected": False}
        else:
            if args.output is None or (args.action == "run" and args.protocol is None):
                raise ValidationError("Provide --output, and --protocol for run")
            result = (review_packet(ROOT, args.output) if args.action == "review-packet" else
                      freeze(ROOT, args.output) if args.action == "freeze" else run(ROOT, args.protocol, args.output))
        print(json.dumps(result, indent=2))
        return 0
    except (ValidationError, OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
