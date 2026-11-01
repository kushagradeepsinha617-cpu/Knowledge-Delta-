"""Configure this Python child process for repository-contained offline ML state."""
import os
from pathlib import Path
import sys

from .validation import ValidationError


def configure_offline_environment(project_root):
    root = Path(project_root).resolve()
    paths = {"HF_HOME": ".tools/cache/hf", "HF_HUB_CACHE": ".tools/cache/hf/hub",
             "HF_XET_CACHE": ".tools/cache/hf/xet", "TORCH_HOME": ".tools/cache/torch",
             "XDG_CACHE_HOME": ".tools/cache", "TEMP": ".tools/tmp/ml", "TMP": ".tools/tmp/ml"}
    resolved = {}
    for name, relative in paths.items():
        directory = (root / relative).resolve()
        if not directory.is_relative_to(root):
            raise ValidationError(f"Offline state directory escapes project: {name}")
        resolved[name] = str(directory)
    # Validate every path before creating any directories or changing this process.
    for value in resolved.values():
        Path(value).mkdir(parents=True, exist_ok=True)
    os.environ.update(resolved)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True
    return resolved
