"""Read-only readiness checks. Never download, start services, or infer."""
import importlib.metadata
from http.client import HTTPException
import json
import platform
import shutil
import sys
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

from .validation import text

MODEL = "qwen3:1.7b"
MAX_INVENTORY_BYTES = 1024 * 1024


class NoRedirects(HTTPRedirectHandler):
    """Do not let a localhost response redirect inventory checks elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def readiness(check_ollama=False):
    try:
        free_disk = shutil.disk_usage(".").free
        disk_error = None
    except OSError as exc:
        free_disk = None
        disk_error = str(exc)
    packages = {}
    for name in ("knowledge-delta", "pytest", "numpy", "sentence-transformers", "streamlit"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {
        "python": sys.version, "platform": platform.platform(),
        "executables": {name: shutil.which(name) for name in ("git", "ollama")},
        "packages": packages,
        "hardware": {"cpu": platform.processor() or None, "gpu": None,
                     "ram_bytes": None, "free_disk_bytes": free_disk},
        "disk_note": "Free space on the working directory volume; not a model memory estimate.",
        "disk_error": disk_error,
        "hardware_note": "Null means unknown; no GPU or performance capability inferred.",
        "ollama": {"status": "not_checked", "model": MODEL},
        "downloads_performed": False,
        "path_note": "Null executable means not found in this process PATH.",
    }
    if check_ollama:
        try:
            # Fixed localhost endpoint; ignore proxy environment configuration.
            opener = build_opener(ProxyHandler({}), NoRedirects())
            with opener.open("http://127.0.0.1:11434/api/tags", timeout=3) as response:
                body = response.read(MAX_INVENTORY_BYTES + 1)
            if len(body) > MAX_INVENTORY_BYTES:
                raise ValueError("local model inventory exceeds the 1 MiB response limit")
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise ValueError("model inventory must be an object")
            models = payload["models"]
            if not isinstance(models, list):
                raise ValueError("models must be an array")
            for model in models:
                if not isinstance(model, dict):
                    raise ValueError("each model must be an object")
                names = [model[key] for key in ("name", "model") if key in model]
                if not names or any(not isinstance(name, str) or not name.strip() for name in names):
                    raise ValueError("model names must be nonempty strings")
                for name in names:
                    text(name, "local model inventory name")
                digest = model.get("digest")
                if digest is not None and (not isinstance(digest, str) or not digest.strip()):
                    raise ValueError("model digest must be a nonempty string when present")
                if digest is not None:
                    text(digest, "local model inventory digest")
            matches = [m for m in models if m.get("name") == MODEL or m.get("model") == MODEL]
            result["ollama"] = {"status": "model_available" if matches else "model_missing",
                                "model": MODEL, "digest": matches[0].get("digest") if matches else None,
                                "inference_verified": False}
        except (URLError, OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError, RecursionError) as exc:
            result["ollama"] = {"status": "unavailable_or_invalid_response", "model": MODEL,
                                "error": str(exc), "inference_verified": False,
                                "action": "Install/start local Ollama and explicitly pull the model during setup."}
    return result
