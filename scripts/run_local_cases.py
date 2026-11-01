"""Run all cases on both snapshots/configurations; emits traces, not correctness scores."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.embeddings import LocalMiniLM
from knowledge_delta.experiments import run_dataset
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.ollama import ALLOWED_MODELS, OllamaClient
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--embedding-directory", required=True, type=Path)
    parser.add_argument("--model", choices=ALLOWED_MODELS, default="qwen3:1.7b")
    parser.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
    args = parser.parse_args(argv)
    try:
        before, after = load_snapshot(args.before), load_snapshot(args.after)
        dataset = read_json(args.dataset)
        directory = args.embedding_directory.resolve()
        if not directory.is_relative_to(ROOT):
            raise ValidationError("Embedding assets must be explicitly installed inside the project folder")
        configure_offline_environment(ROOT)
        embedder = LocalMiniLM(directory, ROOT)
        result = run_dataset(dataset, before, after, embedder, OllamaClient(args.model),
                             repeats=args.repeats, token_limit=min(128, embedder.token_limit))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["counts"]["run_errors"] else 0
    except (ValidationError, RuntimeError, OSError) as exc:
        print(json.dumps({"status": "run_error", "error": str(exc), "generation_performed": False,
                          "downloads_performed": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
