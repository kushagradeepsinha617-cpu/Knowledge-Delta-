"""Explicit Windows child-runtime preparation; no installer or model downloads."""
from hashlib import sha256
import os
from pathlib import Path
import re
import socket
import stat
import subprocess

from .validation import ValidationError, digest


def runtime_plan(project_root, runtime=None):
    if os.name != "nt":
        raise ValidationError("This contained Ollama launcher is Windows-only; other platforms are unverified")
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise ValidationError("Project root must be an existing directory")
    candidate = root / ".tools/runtime/ollama/ollama.exe" if runtime is None else Path(runtime)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.is_symlink():
        raise ValidationError("Ollama executable must not be a symlink")
    executable = candidate.resolve()
    if not executable.is_relative_to(root) or executable.suffix.lower() != ".exe":
        raise ValidationError("Ollama executable must be an .exe inside the project folder")
    relative = {"USERPROFILE": ".tools/ollama-profile",
                "LOCALAPPDATA": ".tools/ollama-profile/AppData/Local",
                "APPDATA": ".tools/ollama-profile/AppData/Roaming",
                "TEMP": ".tools/tmp/ollama", "TMP": ".tools/tmp/ollama",
                "OLLAMA_MODELS": ".tools/models/ollama"}
    paths = {name: (root / value).resolve() for name, value in relative.items()}
    if any(not path.is_relative_to(root) for path in paths.values()):
        raise ValidationError("Ollama child-state path escapes the project folder")
    overrides = {name: str(path) for name, path in paths.items()}
    overrides.update(OLLAMA_HOST="127.0.0.1:11434", OLLAMA_NO_CLOUD="1", OLLAMA_NUM_PARALLEL="1",
                     OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_CONTEXT_LENGTH="4096")
    exists = executable.exists()
    checksum = None
    if exists:
        if not stat.S_ISREG(executable.stat().st_mode):
            raise ValidationError("Ollama executable must be a regular file")
        hasher = sha256()
        with executable.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                hasher.update(block)
        checksum = hasher.hexdigest()
    command = [str(executable), "serve"]
    return {"status": "ready_for_explicit_start" if exists else "missing_runtime",
            "project_root": str(root), "command": command, "environment_overrides": overrides,
            "runtime_sha256": checksum, "configuration_id": digest({"launcher": "contained-ollama-v1",
                "runtime_sha256": checksum, "overrides": overrides}),
            "downloads_performed": False, "native_execution_performed": False,
            "runtime_publisher_provenance_verified": False,
            "note": "The executable hash identifies bytes; verify the approved upstream archive separately. Planning creates no directories."}


def start_runtime(project_root, runtime, expected_sha256):
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
        raise ValidationError("Explicit start requires the separately reviewed executable SHA256")
    plan = runtime_plan(project_root, runtime)
    if plan["status"] != "ready_for_explicit_start":
        raise ValidationError("Local Ollama executable is missing; setup and downloads remain explicit")
    if plan["runtime_sha256"] != expected_sha256.lower():
        raise ValidationError("Ollama executable hash mismatch; no native process started")
    # Fail before creating state if another service owns the configured port.
    # The socket is closed before serve; a later bind race must fail in Ollama.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("127.0.0.1", 11434))
    root = Path(plan["project_root"])
    for name in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "OLLAMA_MODELS"):
        path = Path(plan["environment_overrides"][name])
        if not path.resolve().is_relative_to(root):
            raise ValidationError("Child-state path changed outside the project before start")
        path.mkdir(parents=True, exist_ok=True)
    child = os.environ.copy()
    child.update(plan["environment_overrides"])
    # Foreground child in this terminal, without shell interpretation or global env edits.
    return subprocess.run(plan["command"], cwd=root, env=child, check=False).returncode
