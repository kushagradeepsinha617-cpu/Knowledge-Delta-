"""Explicit ten-question local hardware probe; no downloads, grading, or model switching."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.chunking import chunk_snapshot
from knowledge_delta.embeddings import LocalMiniLM
from knowledge_delta.onnx_embeddings import LocalOnnxMiniLM
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.ollama import ALLOWED_MODELS, OllamaClient
from knowledge_delta.retrieval import build_index
from knowledge_delta.smoke import parse_smoke_questions, run_smoke
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("questions", type=Path)
    parser.add_argument("--embedding-directory", required=True, type=Path)
    parser.add_argument("--embedding-backend", choices=("sentence-transformers", "onnxruntime"),
                        default="sentence-transformers", help="Explicit backend; never falls back automatically")
    parser.add_argument("--model", choices=ALLOWED_MODELS, default="qwen3:1.7b")
    args = parser.parse_args(argv)
    try:
        snapshot = load_snapshot(args.snapshot)
        questions = parse_smoke_questions(read_json(args.questions), snapshot)
        directory = args.embedding_directory.resolve()
        if not directory.is_relative_to(ROOT):
            raise ValidationError("Embedding assets must be explicitly installed inside the project folder")
        configure_offline_environment(ROOT)
        embedding_class = LocalOnnxMiniLM if args.embedding_backend == "onnxruntime" else LocalMiniLM
        embedder = embedding_class(directory, ROOT)
        chunks = chunk_snapshot(snapshot, embedder.tokenizer, min(128, embedder.token_limit), 16)
        index = build_index(snapshot, chunks, embedder)
        result = run_smoke(questions, snapshot, index, embedder, OllamaClient(args.model))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["live_cpu_measurement_verified"] else 2
    except (ValidationError, RuntimeError, OSError) as exc:
        print(json.dumps({"status": "run_error", "error": str(exc), "generation_performed": False,
                          "downloads_performed": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
