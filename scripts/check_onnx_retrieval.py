"""Optional real local embedding/index check; requires explicitly downloaded assets.

No Ollama, answering model, grading, model download or hosted API is called.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.cases import validate_dataset
from knowledge_delta.chunking import chunk_snapshot
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.onnx_embeddings import LocalOnnxMiniLM
from knowledge_delta.questions import QuestionInput
from knowledge_delta.retrieval import build_index
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json, digest


def check(root=ROOT):
    configure_offline_environment(root)
    started = time.perf_counter()
    embedder = LocalOnnxMiniLM(root / ".tools/models/minilm-onnx", root)
    base = root / "examples/pydantic"
    snapshots = {slot: load_snapshot(base / slot / "manifest.json") for slot in ("before", "after")}
    dataset = read_json(base / "cases.json")
    summary = validate_dataset(dataset, snapshots["before"], snapshots["after"])
    indexes = {}
    for slot, snapshot in snapshots.items():
        chunks = chunk_snapshot(snapshot, embedder.tokenizer, 128, 16)
        indexes[slot] = build_index(snapshot, chunks, embedder)
    if indexes["before"].index_id == indexes["after"].index_id:
        raise ValidationError("Separate snapshot index identities unexpectedly match")
    if {c.chunk_id for c in indexes["before"].chunks} & {c.chunk_id for c in indexes["after"].chunks}:
        raise ValidationError("Chunk identities are not snapshot-isolated")
    records = []
    for case in dataset["cases"]:
        for configuration, filtered in (("basic", False), ("version_filtered", True)):
            for slot, snapshot in snapshots.items():
                question = QuestionInput.from_case(case, slot)
                result = indexes[slot].search(question, snapshot, embedder, top_k=2, version_filter=filtered)
                if filtered and any(question.effective_version(snapshot) not in c.software_versions for c in result.chunks):
                    raise ValidationError("Version-filtered real retrieval includes an incompatible chunk")
                records.append({"case_id": case["case_id"], "snapshot_slot": slot,
                    "snapshot_id": snapshot.snapshot_id, "configuration": configuration,
                    "question": asdict(question), "effective_version": result.effective_version,
                    "retrieved_passages": [dict(asdict(chunk), similarity=score)
                                          for chunk, score in zip(result.chunks, result.scores)],
                    "excluded": list(result.excluded)})
    return {"schema_version": 1, "kind": "actual_onnx_retrieval_contract_check",
        "status": "passed", "origin": "live_embeddings_and_numpy_retrieval",
        "dataset_hash": digest(dataset), "case_review_counts": summary,
        "embedder": embedder.configuration, "embedder_id": embedder.identity,
        "indexes": {slot: {"index_id": index.index_id, "snapshot_id": index.snapshot_id,
                           "chunks": len(index.chunks)} for slot, index in indexes.items()},
        "records": records, "query_count": len(records), "elapsed_seconds": time.perf_counter()-started,
        "answering_model_called": False, "answer_correctness_measured": False,
        "torch_imported": "torch" in sys.modules, "downloads_performed": False,
        "notice": "Actual local embeddings/retrieval on constructed assembly of genuine sources. No answers, semantic correctness, configuration improvement or causal regression measured."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="runs/onnx-retrieval-check.json", type=Path)
    args = parser.parse_args(argv)
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "runs") or output.suffix != ".json" or output.exists():
        parser.error("Choose a new project-local runs/*.json output")
    try:
        result = check()
        code = 0
    except Exception as exc:
        result = {"status": "error", "error_type": type(exc).__name__, "error": str(exc),
                  "answering_model_called": False, "downloads_performed": False}
        code = 2
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result.get(key) for key in ("status", "query_count", "elapsed_seconds",
                     "indexes", "answering_model_called", "torch_imported", "error")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
