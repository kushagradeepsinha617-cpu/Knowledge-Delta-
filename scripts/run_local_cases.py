"""Run all cases on both snapshots/configurations; emits traces, not correctness scores."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.embeddings import LocalMiniLM
from knowledge_delta.onnx_embeddings import LocalOnnxMiniLM
from knowledge_delta.experiments import run_dataset
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.ollama import ALLOWED_MODELS, OllamaClient
from knowledge_delta.pipeline import RunConfiguration
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--embedding-directory", required=True, type=Path)
    parser.add_argument("--embedding-backend", choices=("sentence-transformers", "onnxruntime"),
                        default="sentence-transformers", help="Explicit backend; never falls back automatically")
    parser.add_argument("--model", choices=ALLOWED_MODELS, default="qwen3:1.7b")
    parser.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--max-output-tokens", type=int, choices=(128, 256), default=128,
                        help="Explicit output cap; changing it creates a separate experiment")
    parser.add_argument("--output", type=Path, help="Save raw UTF-8 JSON to a new project-local runs/*.json file")
    args = parser.parse_args(argv)
    run_started = False
    try:
        output = None
        if args.output is not None:
            output = (ROOT / args.output).resolve()
            if (not output.is_relative_to((ROOT / "runs").resolve())
                    or not output.is_relative_to(ROOT.resolve())
                    or output.suffix != ".json" or output.exists() or args.output.is_symlink()):
                raise ValidationError("Choose a new project-local runs/*.json output; existing records are preserved")
        before, after = load_snapshot(args.before), load_snapshot(args.after)
        dataset = read_json(args.dataset)
        directory = args.embedding_directory.resolve()
        if not directory.is_relative_to(ROOT):
            raise ValidationError("Embedding assets must be explicitly installed inside the project folder")
        configure_offline_environment(ROOT)
        embedding_class = LocalOnnxMiniLM if args.embedding_backend == "onnxruntime" else LocalMiniLM
        embedder = embedding_class(directory, ROOT)
        run_started = True
        result = run_dataset(dataset, before, after, embedder, OllamaClient(args.model),
                             repeats=args.repeats, token_limit=min(128, embedder.token_limit),
                             configuration=RunConfiguration(max_output_tokens=args.max_output_tokens))
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({"status": result["status"], "run_id": result["run_id"],
                              "origin": result["origin"], "counts": result["counts"],
                              "output": str(output), "correctness_measured": False}, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["counts"]["run_errors"] else 0
    except (ValidationError, RuntimeError, OSError) as exc:
        print(json.dumps({"status": "run_error", "error": str(exc), "generation_performed": None if run_started else False,
                          "experiment_started": run_started, "downloads_performed": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
