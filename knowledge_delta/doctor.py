"""Read-only readiness checks. Never download, start services, or infer."""
import importlib.metadata
import json
import platform
import shutil
import sys
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

MODEL = "qwen3:1.7b"


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
            opener = build_opener(ProxyHandler({}))
            with opener.open("http://127.0.0.1:11434/api/tags", timeout=3) as response:
                payload = json.load(response)
            models = payload["models"]
            if not isinstance(models, list):
                raise ValueError("models must be an array")
            matches = [m for m in models if m.get("name") == MODEL or m.get("model") == MODEL]
            result["ollama"] = {"status": "model_available" if matches else "model_missing",
                                "model": MODEL, "digest": matches[0].get("digest") if matches else None,
                                "inference_verified": False}
        except (URLError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            result["ollama"] = {"status": "unavailable_or_invalid_response", "model": MODEL,
                                "error": str(exc), "inference_verified": False,
                                "action": "Install/start local Ollama and explicitly pull the model during setup."}
    return result
