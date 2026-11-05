"""Explicit offline check of real local ONNX embeddings; no answering model."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.local_environment import configure_offline_environment
from knowledge_delta.onnx_embeddings import LocalOnnxMiniLM
from knowledge_delta.validation import ValidationError


def check(directory, root=ROOT):
    configure_offline_environment(root)
    started = time.perf_counter()
    model = LocalOnnxMiniLM(directory, root)
    loaded = time.perf_counter()
    texts = ["Documentation explains the request timeout.",
             "Documentation explains the request timeout.",
             "Unicode café λ and documentation.",
             "A substantially longer documentation passage about requests, versions and configuration. " * 4]
    vectors = model.encode(texts)
    np = model._np
    single = model.encode([texts[0]])
    if vectors.shape != (4, 384) or not np.isfinite(vectors).all():
        raise ValidationError("Live embedding shape/finite check failed")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        raise ValidationError("Live embedding norm check failed")
    if not np.allclose(vectors[0], vectors[1], atol=1e-5, rtol=1e-5):
        raise ValidationError("Repeated-text smoke consistency check failed")
    if not np.allclose(vectors[0], single[0], atol=1e-5, rtol=1e-5):
        raise ValidationError("Padding/batch invariance smoke check failed")
    boundary = "a " * 254
    if model.tokenizer.count(boundary) != 256:
        raise ValidationError("Expected pinned tokenizer boundary differs")
    model.encode([boundary])
    try:
        model.encode(["a " * 255])
    except ValidationError:
        pass
    else:
        raise ValidationError("Over-limit input was not rejected")
    unicode_text = "café λ 😀"
    offsets = model.tokenizer.offsets(unicode_text)
    if not offsets or any(not 0 <= start < end <= len(unicode_text) for start, end in offsets):
        raise ValidationError("Unicode original-text offsets failed")
    if "torch" in sys.modules:
        raise ValidationError("ONNX smoke must not import PyTorch")
    return {"kind": "actual_local_onnx_embedding_smoke", "origin": "live",
        "status": "embedding_contracts_verified", "embedding_model": model.configuration,
        "embedder_id": model.identity, "shape": list(vectors.shape), "smoke_texts": texts,
        "embeddings": vectors.tolist(), "single_embedding": single[0].tolist(),
        "norms": norms.tolist(), "duplicate_max_absolute_difference": float(np.max(np.abs(vectors[0]-vectors[1]))),
        "batch_max_absolute_difference": float(np.max(np.abs(vectors[0]-single[0]))),
        "unicode_offsets": offsets, "boundary_tokens": 256, "over_limit_rejected": True,
        "load_seconds": loaded-started, "encoding_and_checks_seconds": time.perf_counter()-loaded,
        "torch_imported": False, "answering_model_called": False,
        "correctness_measured": False,
        "notice": "Actual embeddings on constructed smoke strings. No RAG answer correctness, Torch equivalence, general determinism or model-performance comparison is established."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_directory", type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(check(args.model_directory), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "run_error", "error_type": type(exc).__name__, "error": str(exc),
                          "answering_model_called": False, "downloads_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
