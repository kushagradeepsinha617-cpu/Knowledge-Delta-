"""Pinned, offline MiniLM ONNX embeddings. No PyTorch, network or automatic download."""
from hashlib import sha1, sha256
import importlib.metadata
import json
import math
from pathlib import Path

from .embeddings import MODEL_NAME, MODEL_REVISION, LocalModelUnavailable, validate_cache_environment
from .validation import ValidationError, digest

# Git blob identities for small files; SHA256 for the upstream ONNX LFS object.
ASSETS = {
    "config.json": (612, "git_blob_sha1", "72b987fd805cfa2b58c4c8c952b274a11bfd5a00"),
    "config_sentence_transformers.json": (116, "git_blob_sha1", "fd1b291129c607e5d49799f87cb219b27f98acdf"),
    "modules.json": (349, "git_blob_sha1", "952a9b81c0bfd99800fabf352f69c7ccd46c5e43"),
    "sentence_bert_config.json": (53, "git_blob_sha1", "59d594003bf59880a884c574bf88ef7555bb0202"),
    "tokenizer.json": (466247, "git_blob_sha1", "cb202bfe2e3c98645018a6d12f182a434c9d3e02"),
    "tokenizer_config.json": (350, "git_blob_sha1", "c79f2b6a0cea6f4b564fed1938984bace9d30ff0"),
    "special_tokens_map.json": (112, "git_blob_sha1", "e7b0375001f109a6b8873d756ad4f7bbb15fbaa5"),
    "vocab.txt": (231508, "git_blob_sha1", "fb140275c155a9c7c5a3b3e0e77a9e839594a938"),
    "1_Pooling/config.json": (190, "git_blob_sha1", "d1514c3162bbe87b343f565fadc62e6c06f04f03"),
    "README.md": (10502, "git_blob_sha1", "44af2e3b0fa3a0b6239e48422972bf755f28fde0"),
    "onnx/model.onnx": (90405214, "sha256", "6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452"),
}


def verify_asset(path, pin):
    size, algorithm, expected = pin
    if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
        raise LocalModelUnavailable("Missing, unsafe or wrong-size MiniLM asset: " + path.name)
    checksum = sha256() if algorithm == "sha256" else sha1()
    actual_sha256 = sha256()
    if algorithm == "git_blob_sha1":
        checksum.update(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
            actual_sha256.update(block)
    if checksum.hexdigest() != expected:
        raise ValidationError("Pinned MiniLM asset digest mismatch: " + path.name)
    return actual_sha256.hexdigest()


def inspect_assets(directory, project_root, *, pins=None):
    directory, root = Path(directory).resolve(), Path(project_root).resolve()
    if not directory.is_relative_to(root):
        raise ValidationError("ONNX model assets must stay inside the project")
    hashes = {}
    for relative, pin in (ASSETS if pins is None else pins).items():
        path = directory / relative
        if not path.resolve().is_relative_to(directory):
            raise ValidationError("Model asset path escapes its directory")
        hashes[relative] = verify_asset(path, pin)
    return directory, hashes


def mean_pool_normalize(token_vectors, attention_mask, dimension=384):
    """Mask-aware pooling with a portable scalar reference, returning one vector.

    Includes all attended tokens, including BERT special tokens. Padding is ignored.
    Python accumulation precedes the adapter's final float32 conversion.
    """
    if len(token_vectors) != len(attention_mask) or not token_vectors:
        raise ValidationError("Token tensor and attention mask shapes differ")
    if any(type(value) is not int or value not in (0, 1) for value in attention_mask):
        raise ValidationError("Attention mask must contain binary integers")
    for row in token_vectors:
        if len(row) != dimension or any(isinstance(v, bool) or not isinstance(v, (float, int))
                                       or not math.isfinite(v) for v in row):
            raise ValidationError("Malformed or nonfinite token embeddings")
    count = sum(attention_mask)
    if count == 0:
        raise ValidationError("All-zero attention mask is invalid")
    pooled = [math.fsum(row[j] for row, active in zip(token_vectors, attention_mask) if active) / count
              for j in range(dimension)]
    norm = math.sqrt(math.fsum(value * value for value in pooled))
    if not math.isfinite(norm) or norm < 1e-12:
        raise ValidationError("Zero or nonfinite embedding norm")
    return [value / norm for value in pooled]


class OnnxTokenizer:
    mode = "local"
    def __init__(self, tokenizer, identity):
        self._tokenizer, self.identity = tokenizer, identity
        tokenizer.no_truncation()
        tokenizer.no_padding()

    def offsets(self, text):
        return list(self._tokenizer.encode(text, add_special_tokens=False).offsets)

    def count(self, text):
        return len(self._tokenizer.encode(text, add_special_tokens=True).ids)


class LocalOnnxMiniLM:
    mode = "local"
    dimension = 384
    asset_provenance_verified = True

    def __init__(self, model_path, project_root):
        validate_cache_environment(project_root)
        directory, hashes = inspect_assets(model_path, project_root)
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        sentence = json.loads((directory / "sentence_bert_config.json").read_text(encoding="utf-8"))
        pooling = json.loads((directory / "1_Pooling/config.json").read_text(encoding="utf-8"))
        if config.get("model_type") != "bert" or config.get("hidden_size") != self.dimension:
            raise ValidationError("Unexpected pinned encoder configuration")
        limit = sentence.get("max_seq_length")
        if type(limit) is not int or not 2 < limit <= 256:
            raise ValidationError("MiniLM input limit must be explicit and at most 256")
        if (pooling.get("word_embedding_dimension") != self.dimension
                or pooling.get("pooling_mode_mean_tokens") is not True
                or any(value for key, value in pooling.items()
                       if key.startswith("pooling_mode_") and key != "pooling_mode_mean_tokens")):
            raise ValidationError("Unsupported MiniLM pooling configuration")
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except (ImportError, OSError, RuntimeError) as exc:
            raise LocalModelUnavailable("ONNX runtime/tokenizer dependencies unavailable; use explicit setup") from exc
        ort.disable_telemetry_events()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        try:
            self._session = ort.InferenceSession(str(directory / "onnx/model.onnx"),
                sess_options=options, providers=["CPUExecutionProvider"])
        except Exception as exc:
            raise LocalModelUnavailable("Cannot load pinned ONNX model locally: " + str(exc)) from exc
        if self._session.get_providers() != ["CPUExecutionProvider"]:
            raise ValidationError("ONNX session must use only the CPU execution provider")
        inputs = self._session.get_inputs()
        self._input_names = tuple(item.name for item in inputs)
        if (not {"input_ids", "attention_mask"}.issubset(self._input_names)
                or set(self._input_names) - {"input_ids", "attention_mask", "token_type_ids"}
                or any(item.type != "tensor(int64)" or len(item.shape) != 2 for item in inputs)):
            raise ValidationError("Unexpected ONNX graph inputs/types")
        outputs = {item.name: item for item in self._session.get_outputs()}
        output = outputs.get("last_hidden_state")
        if (output is None or output.type != "tensor(float)" or len(output.shape) != 3
                or output.shape[-1] != self.dimension):
            raise ValidationError("Pinned ONNX graph must return float last_hidden_state[B,T,384]")
        raw_tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        pad_id = raw_tokenizer.token_to_id("[PAD]")
        if type(pad_id) is not int or pad_id < 0:
            raise ValidationError("Pinned tokenizer has no valid padding token")
        self._pad_id, self._np, self.token_limit = pad_id, np, limit
        self.library_versions = {name: importlib.metadata.version(name)
                                 for name in ("onnxruntime", "numpy", "tokenizers")}
        self.configuration = {"adapter_version": "minilm-onnx-direct-v1", "model": MODEL_NAME,
            "requested_revision": MODEL_REVISION, "backend": "onnxruntime",
            "assets": hashes, "asset_provenance_verified": True, "library_versions": self.library_versions,
            "providers": self._session.get_providers(), "device": "cpu", "token_limit": limit,
            "threads": {"intra_op": 1, "inter_op": 1}, "execution": "sequential",
            "graph_optimization": "basic", "pooling": "attention_mask_mean_all_attended_tokens",
            "normalization": "l2", "pool_accumulation": "python_float_then_float32",
            "input_names": self._input_names, "output_name": "last_hidden_state", "batch_size": 8}
        self.identity = digest(self.configuration)
        self.tokenizer = OnnxTokenizer(raw_tokenizer, self.identity)

    def encode(self, texts):
        if isinstance(texts, (str, bytes)):
            raise ValidationError("Embedding inputs must be a sequence of strings")
        texts = list(texts)
        if any(not isinstance(text, str) for text in texts):
            raise ValidationError("Embedding inputs must be strings")
        if not texts:
            return self._np.empty((0, self.dimension), dtype=self._np.float32)
        encoded = [self.tokenizer._tokenizer.encode(text, add_special_tokens=True) for text in texts]
        if any(len(item.ids) > self.token_limit for item in encoded):
            raise ValidationError("Embedding input exceeds actual token limit; truncation is disabled")
        vectors = []
        for start in range(0, len(encoded), 8):
            batch = encoded[start:start + 8]
            width = max(len(item.ids) for item in batch)
            ids, masks, types = [], [], []
            for item in batch:
                padding = width - len(item.ids)
                if not item.ids or len(item.type_ids) != len(item.ids):
                    raise ValidationError("Malformed tokenizer encoding")
                ids.append(item.ids + [self._pad_id] * padding)
                masks.append([1] * len(item.ids) + [0] * padding)
                types.append(item.type_ids + [0] * padding)
            values = {"input_ids": ids, "attention_mask": masks, "token_type_ids": types}
            feed = {name: self._np.asarray(values[name], dtype=self._np.int64) for name in self._input_names}
            try:
                output = self._session.run(["last_hidden_state"], feed)[0]
            except Exception as exc:
                raise LocalModelUnavailable("Local ONNX embedding execution failed: " + str(exc)) from exc
            if not hasattr(output, "shape") or tuple(output.shape) != (len(batch), width, self.dimension):
                raise ValidationError("Unexpected ONNX output tensor shape")
            for rows, mask in zip(output.tolist(), masks):
                vectors.append(mean_pool_normalize(rows, mask, self.dimension))
        result = self._np.asarray(vectors, dtype=self._np.float32)
        if result.shape != (len(texts), self.dimension) or not self._np.isfinite(result).all():
            raise ValidationError("Malformed sentence embeddings")
        return result
