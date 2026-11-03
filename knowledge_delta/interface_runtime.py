"""Read-only UI readiness and explicit project-contained Streamlit launch."""
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys

from .validation import ValidationError, digest

WINDOWS_SUPPORTED = os.name == "nt"


def interface_plan(project_root):
    if not WINDOWS_SUPPORTED:
        raise ValidationError("The contained interface launcher is Windows-only; other platforms are unverified")
    root = Path(project_root).resolve()
    app = (root / "scripts/streamlit_app.py").resolve()
    if not root.is_dir() or not app.is_relative_to(root):
        raise ValidationError("Interface application must remain inside the project")
    isolated = sys.prefix != sys.base_prefix and Path(sys.prefix).resolve().is_relative_to(root)
    installed = importlib.util.find_spec("streamlit") is not None
    try:
        version = importlib.metadata.version("streamlit") if installed else None
    except importlib.metadata.PackageNotFoundError:
        version = None
    paths = {"USERPROFILE": ".tools/ui-profile", "LOCALAPPDATA": ".tools/ui-profile/AppData/Local",
             "APPDATA": ".tools/ui-profile/AppData/Roaming", "XDG_CACHE_HOME": ".tools/cache/ui",
             "TEMP": ".tools/tmp/ui", "TMP": ".tools/tmp/ui"}
    resolved = {name: (root / value).resolve() for name, value in paths.items()}
    if any(not path.is_relative_to(root) for path in resolved.values()):
        raise ValidationError("Interface state path escapes the project")
    overrides = {name: str(path) for name, path in resolved.items()}
    overrides["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", "-m", "streamlit", "run", str(app),
               "--server.address=127.0.0.1", "--server.port=8501", "--server.headless=true",
               "--browser.gatherUsageStats=false", "--server.fileWatcherType=none", "--server.maxUploadSize=10"]
    status = ("wrong_environment" if not isolated else "missing_streamlit" if not installed else
              "unversioned_streamlit" if version is None else "missing_app" if not app.is_file() else "ready_for_explicit_start")
    return {"status": status, "streamlit_version": version, "project_environment": isolated,
            "command": command, "environment_overrides": overrides, "url": "http://127.0.0.1:8501",
            "configuration_id": digest({"launcher": "fixture-interface-v1", "version": version, "command": command, "overrides": overrides}),
            "downloads_performed": False, "ui_launched": False, "runtime_containment_verified": False,
            "action": "Use an isolated project environment with explicitly installed Streamlit. No startup command installs packages or models."}


def start_interface(project_root):
    plan = interface_plan(project_root)
    if plan["status"] != "ready_for_explicit_start":
        raise ValidationError(plan["status"] + ": " + plan["action"])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("127.0.0.1", 8501))
    root = Path(project_root).resolve()
    for name, value in plan["environment_overrides"].items():
        if name == "PYTHONDONTWRITEBYTECODE":
            continue
        path = Path(value)
        if not path.resolve().is_relative_to(root):
            raise ValidationError("Interface state path changed outside the project")
        path.mkdir(parents=True, exist_ok=True)
    child = os.environ.copy()
    child.update(plan["environment_overrides"])
    return subprocess.run(plan["command"], cwd=root, env=child, check=False).returncode
