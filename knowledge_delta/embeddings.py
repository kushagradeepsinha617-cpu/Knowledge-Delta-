"""Explicit local MiniLM adapter. Imports ML libraries only after local readiness checks."""
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path

from .validation import ValidationError, digest

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
WEIGHT_SHA256 = "53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db"
REQUIRED = ("model.safetensors", "config.json", "config_sentence_transformers.json",
            "modules.json", "sentence_bert_config.json", "tokenizer.json",
            "tokenizer_config.json", "special_tokens_map.json", "vocab.txt",
            "1_Pooling/config.json")


class LocalModelUnavailable(RuntimeError):
    """Explicit setup is needed; ordinary startup never downloads assets."""


def validate_cache_environment(project_root):
    root = Path(project_root).resolve()
    required = ("HF_HOME", "HF_HUB_CACHE", "HF_XET_CACHE", "TORCH_HOME", "TEMP", "TMP")
    for key in required:
        value = os.environ.get(key)
        if not value or not Path(value).is_absolute() or not Path(value).resolve().is_relative_to(root):
            raise LocalModelUnavailable(f"Set child-process {key} to an absolute directory inside the project before ML imports")
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        if os.environ.get(key) != "1":
            raise LocalModelUnavailable(f"Set child-process {key}=1 for offline application operation")


def _file_hash(path):
    checksum = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def inspect_assets(model_path):
    directory = Path(model_path).resolve()
    if not directory.is_dir():
        raise LocalModelUnavailable("Local MiniLM directory is missing; run the explicit approved setup first")
    hashes = {}
    for relative in REQUIRED:
        path = directory / relative
        if path.is_symlink() or not path.resolve().is_relative_to(directory) or not path.is_file():
            raise LocalModelUnavailable(f"Missing or unsafe local MiniLM asset: {relative}")
        hashes[relative] = _file_hash(path)
    if hashes["model.safetensors"] != WEIGHT_SHA256:
        raise ValidationError("MiniLM weight hash does not match the pinned model revision")
    try:
        modules = json.loads((directory / "modules.json").read_text(encoding="utf-8"))
        expected = [("sentence_transformers.models.Transformer", ""),
                    ("sentence_transformers.models.Pooling", "1_Pooling")]
        if not isinstance(modules, list) or len(modules) not in (2, 3):
            raise ValueError("unexpected modules")
        actual = [(item["type"], item["path"]) for item in modules]
        if actual not in (expected, expected + [("sentence_transformers.models.Normalize", "2_Normalize")]):
            raise ValueError("unexpected module type/path")
        config = json.loads((directory / "sentence_bert_config.json").read_text(encoding="utf-8"))
        if type(config["max_seq_length"]) is not int or not 1 <= config["max_seq_length"] <= 256:
            raise ValueError("unsupported embedding token limit")
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise ValidationError(f"Unsupported local MiniLM configuration: {exc}") from exc
    return directory, hashes, config["max_seq_length"]


class LocalTokenizer:
    mode = "local"

    def __init__(self, tokenizer, identity):
        if not tokenizer.is_fast:
            raise LocalModelUnavailable("A local fast tokenizer with original-text offsets is required")
        self._tokenizer = tokenizer
        self.identity = identity

    def offsets(self, text):
        result = self._tokenizer(text, return_offsets_mapping=True,
                                 add_special_tokens=False, truncation=False, padding=False)
        return [tuple(span) for span in result["offset_mapping"]]

    def count(self, text):
        return len(self._tokenizer.encode(text, add_special_tokens=True, truncation=False))


class LocalMiniLM:
    mode = "local"
    dimension = 384
    # Only the weight file has a trusted published digest at this stage. Other
    # assets have recorded actual hashes, not a verified revision manifest.
    asset_provenance_verified = False

    def __init__(self, model_path, project_root):
        validate_cache_environment(project_root)
        directory, hashes, configured_limit = inspect_assets(model_path)
        try:
            from sentence_transformers import SentenceTransformer
            import numpy
        except (ImportError, OSError, RuntimeError) as exc:
            raise LocalModelUnavailable("Local embedding dependencies are unavailable; use explicit setup, not an automatic download") from exc
        versions = {}
        for name in ("sentence-transformers", "transformers", "tokenizers", "torch", "numpy"):
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = None
        try:
            self._model = SentenceTransformer(str(directory), device="cpu",
                                             local_files_only=True, trust_remote_code=False)
        except (OSError, ValueError, RuntimeError) as exc:
            raise LocalModelUnavailable(f"Cannot load the local embedding model offline: {exc}") from exc
        limits = (configured_limit, self._model.max_seq_length, self._model.tokenizer.model_max_length)
        if any(type(value) is not int or value < 1 for value in limits):
            raise ValidationError("Embedding/tokenizer limits must be explicit positive integers")
        self.token_limit = min(limits)
        self.configuration = {"adapter_version": "minilm-local-v1", "model": MODEL_NAME,
                                "requested_revision": MODEL_REVISION, "assets": hashes,
                                "asset_provenance_verified": self.asset_provenance_verified,
                                "library_versions": versions, "device": "cpu",
                                "token_limit": self.token_limit}
        self.identity = digest(self.configuration)
        self.tokenizer = LocalTokenizer(self._model.tokenizer, self.identity)
        self.library_versions = versions
        self._numpy = numpy

    def encode(self, texts):
        if isinstance(texts, (str, bytes)):
            raise ValidationError("Embedding inputs must be a sequence of strings, not one string")
        texts = list(texts)
        if any(not isinstance(text, str) for text in texts):
            raise ValidationError("Embedding inputs must be strings")
        if not texts:
            return self._numpy.empty((0, self.dimension), dtype=self._numpy.float32)
        for text in texts:
            if self.tokenizer.count(text) > self.token_limit:
                raise ValidationError("Embedding input exceeds the actual token limit; truncation is not allowed")
        vectors = self._model.encode(list(texts), batch_size=8, convert_to_numpy=True,
                                     normalize_embeddings=False, show_progress_bar=False)
        if vectors.ndim != 2 or vectors.shape != (len(texts), self.dimension):
            raise ValidationError("Embedding model returned an unexpected shape")
        return vectors
