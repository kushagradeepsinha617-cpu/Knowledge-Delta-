"""Reproduce the actual four-human-judgment example, without a model or journal."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from knowledge_delta.diff import compare
from knowledge_delta.evaluation import evaluate_run
from knowledge_delta.metrics import summarize_metrics
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import read_json
from knowledge_delta.workflow import export_report

frozen = ROOT / "docs/evidence/milestone4-output-cap-256"
review_dir = ROOT / "docs/evidence/milestone4-human-answer-review"
record = read_json(review_dir / "human-review-records.json")
with ZipFile(review_dir / "human-reviewed-subset-report.zip") as archive:
    raw = archive.read("raw-run.json")
if sha256(raw).hexdigest() != record["source_run_sha256"]:
    raise RuntimeError("Archived raw evidence changed")
snapshots = {s: load_snapshot(ROOT / "examples/pydantic" / s / "manifest.json") for s in ("before", "after")}
run = json.loads(raw)
result = evaluate_run(run, read_json(frozen / "cases-at-run.json"), record["relation_annotations"],
                      record["review_records"], snapshots=snapshots)
result["metrics"] = summarize_metrics(result)
if result["counts"] != record["counts"] or result["metrics"] != record["metrics"]:
    raise RuntimeError("Published human judgments did not reproduce exactly")
result.update(raw_run=run, review_records=record["review_records"],
    relation_annotations=record["relation_annotations"], snapshot_changes=compare(snapshots["before"], snapshots["after"]),
    import_notice="Actual archived local inference and four actual human judgments; assisted post-hoc subset, not a representative or independent benchmark.")
outputs = export_report(ROOT, ROOT / "docs/portfolio/reviewed-example", result)
print(json.dumps({"status": "passed", "human_answer_reviews": result["counts"]["human_answer_reviews"],
                  "outputs": outputs, "inference_performed": False, "journal_opened": False}, indent=2))
