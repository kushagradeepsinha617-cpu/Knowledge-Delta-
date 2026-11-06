"""Read-only audit probe: reproduce old results, without inference or journal writes."""
import json
from hashlib import sha256
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from knowledge_delta.evaluation import evaluate_run
from knowledge_delta.metrics import summarize_metrics
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import read_json
from scripts import setup_ml_python, setup_ollama_runtime

inputs = {}


def read(path):
    inputs[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return read_json(path)


frozen = ROOT / "docs/evidence/milestone4-output-cap-256"
dataset, relations = read(frozen / "cases-at-run.json"), read(frozen / "relations-at-run.json")
snapshots = {slot: load_snapshot(ROOT / "examples/pydantic" / slot / "manifest.json")
             for slot in ("before", "after")}
observations = []
for filename, expected in (
    ("pydantic-live-main.json", {"pass": 0, "fail": 1, "needs_human_review": 21, "run_error": 18}),
    ("pydantic-live-main-256.json", {"pass": 0, "fail": 2, "needs_human_review": 38, "run_error": 0}),
):
    value = evaluate_run(read(ROOT / "runs" / filename), dataset, relations, snapshots=snapshots)
    actual = value["counts"]["answer_outcomes"]
    if actual != expected:
        raise RuntimeError((filename, actual, expected))
    observations.append({"file": filename, "outcomes": actual})

review_dir = ROOT / "docs/evidence/milestone4-human-answer-review"
record = read(review_dir / "human-review-records.json")
archive_path = review_dir / "human-reviewed-subset-report.zip"
inputs[archive_path.relative_to(ROOT).as_posix()] = sha256(archive_path.read_bytes()).hexdigest()
with ZipFile(archive_path) as archive:
    raw = archive.read("raw-run.json")
if sha256(raw).hexdigest() != record["source_run_sha256"]:
    raise RuntimeError("Published raw run hash differs")
value = evaluate_run(json.loads(raw), dataset, record["relation_annotations"],
                     record["review_records"], snapshots=snapshots, allow_fixture=False)
if (value["counts"] != record["counts"] or summarize_metrics(value) != record["metrics"]
        or value["counts"]["human_answer_reviews"] != 4):
    raise RuntimeError("Published human review counts/metrics differ")
observations.append({"published_human_review_reproduction": "exact counts and metrics matched",
                     "human_answer_reviews": 4})

genuine = ROOT / "examples/pydantic-revision"
value = evaluate_run(read(ROOT / "runs/pydantic-genuine-reviewed-live.json"),
    read(genuine / "cases.json"), read(genuine / "relations.json"),
    snapshots={slot: load_snapshot(genuine / slot / "manifest.json") for slot in ("before", "after")})
if value["counts"]["answer_outcomes"] != {"pass": 0, "fail": 0, "needs_human_review": 4, "run_error": 0}:
    raise RuntimeError("Genuine diagnostic outcomes differ")
observations.append({"file": "pydantic-genuine-reviewed-live.json", "outcomes": value["counts"]["answer_outcomes"]})

for label, module, relative in (("python", setup_ml_python, ".tools/python-3.14"),
                                ("ollama", setup_ollama_runtime, ".tools/runtime/ollama")):
    receipt = module.verify_cached_runtime(ROOT, ROOT / relative)
    observations.append({"cached_runtime": label, "verified_file_count": len(receipt["files"]),
                         "native_execution_performed": False})
print(json.dumps({"result": "passed", "observations": observations, "input_sha256": inputs,
                  "inference_performed": False, "downloads_performed": False,
                  "journal_opened": False}, indent=2))
