"""Install exactly the approved UI wheels locally, only with explicit --install.

Default operation plans without network or writes. Installation never resolves
dependencies online, starts a server, downloads a model, or installs globally.
"""
import sys
sys.dont_write_bytecode = True

import argparse
from datetime import datetime, timezone
import ensurepip
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import time
import urllib.parse
import urllib.request
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_checks import evidence_lock
from scripts.inspect_ui_setup import packaging_api

FOLDER_LIMIT = 750_000_000
DOWNLOAD_LIMIT = 150_000_000
RESERVE = 25_000_000
CHUNK = 1024 * 1024
PIP_NAME = "pip-26.2.2-py3-none-any.whl"
PIP_SHA256 = "fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"


class SetupError(ValueError):
    pass


def inside(root, path):
    path = Path(path)
    if path.is_symlink():
        raise SetupError("Setup paths must not be symlinks")
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SetupError("Setup path escapes the project folder")
    return resolved


def folder_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def check_space(root, extra=0):
    size = folder_bytes(root)
    if size + extra + RESERVE > FOLDER_LIMIT:
        raise SetupError("Project folder plus the setup reserve would exceed 750 MB")
    return size


def file_hash(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            value.update(block)
    return value.hexdigest()


def runtime_check(root):
    if (os.name != "nt" or sys.version_info[:3] != (3, 15, 2)
            or platform.machine().lower() not in ("amd64", "x86_64")):
        raise SetupError("Approved setup targets Windows AMD64 and CPython 3.15.2 only")
    if sys.prefix == sys.base_prefix or not Path(sys.prefix).resolve().is_relative_to(root):
        raise SetupError("Run this script with this project's isolated Python environment")


def load_packages(root):
    manifest_path = inside(root, root / "docs/readiness/ui-wheel-candidates.json")
    lock_path = inside(root, root / "docs/readiness/requirements-ui.lock.txt")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packages = manifest.get("packages")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1 or not isinstance(packages, list) or len(packages) != 34:
        raise SetupError("The approved manifest must contain exactly 34 wheels")
    pins = {}
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)\s+--hash=sha256:([a-f0-9]{64})", line.strip())
        if match is None:
            raise SetupError("UI lock contains an unsupported or unpinned requirement")
        name = re.sub(r"[-_.]+", "-", match[1]).lower()
        if name in pins:
            raise SetupError("Duplicate UI lock requirement")
        pins[name] = (match[2], match[3])
    _, Version, canonical, parse_wheel, tags, _ = packaging_api()
    names = set()
    for package in packages:
        name = canonical(package["name"])
        filename = package["filename"]
        parsed_name, version, build, wheel_tags = parse_wheel(filename)
        url = urllib.parse.urlsplit(package["url"])
        if (name in names or pins.get(name) != (package["version"], package["sha256"])
                or parsed_name != name or version != Version(package["version"])
                or not wheel_tags.intersection(tags) or Path(filename).name != filename
                or url.scheme != "https" or url.hostname != "files.pythonhosted.org"
                or url.username or url.password or url.port is not None
                or urllib.parse.unquote(url.path).split("/")[-1] != filename
                or not re.fullmatch(r"[a-f0-9]{64}", package["sha256"])):
            raise SetupError("Manifest/lock/wheel identity or target compatibility mismatch")
        for field in ("compressed_bytes", "declared_expanded_bytes"):
            if type(package[field]) is not int or package[field] <= 0:
                raise SetupError("Wheel sizes must be explicit positive integers")
        names.add(name)
    if names != set(pins) or sum(p["compressed_bytes"] + 1 for p in packages) > DOWNLOAD_LIMIT:
        raise SetupError("Lock scope or approved artifact payload budget differs")
    return packages, {"manifest_sha256": file_hash(manifest_path), "lock_sha256": file_hash(lock_path)}


def installed_version(package, root):
    try:
        distribution = importlib.metadata.distribution(package["name"])
    except importlib.metadata.PackageNotFoundError:
        return None
    if not Path(distribution.locate_file("")).resolve().is_relative_to(Path(sys.prefix).resolve()):
        raise SetupError("An existing UI dependency is outside the isolated environment")
    if distribution.version != package["version"]:
        raise SetupError("Existing dependency version differs; preserve it and review the environment first")
    return distribution.version


def plan(root=ROOT):
    root = Path(root).resolve()
    runtime_check(root)
    packages, identities = load_packages(root)
    work = inside(root, root / ".tools/ui-setup")
    pending = [p for p in packages if installed_version(p, root) is None]
    existing = folder_bytes(root)
    expanded = sum(p["declared_expanded_bytes"] for p in pending)
    peak = existing + max((p["compressed_bytes"] for p in pending), default=0) + 2 * expanded + RESERVE
    if peak > FOLDER_LIMIT:
        raise SetupError("Conservative remaining-install planning total exceeds 750 MB")
    return packages, {"status": "plan_ready", **identities, "project_root": str(root), "work_directory": str(work),
        "python_executable": sys.executable, "environment_prefix": sys.prefix,
        "packages": len(packages), "pending_packages": len(pending), "existing_folder_bytes": existing,
        "remaining_declared_expanded_bytes": expanded, "conservative_planning_bytes": peak,
        "folder_ceiling_bytes": FOLDER_LIMIT, "artifact_payload_ceiling_bytes": DOWNLOAD_LIMIT,
        "packages_installed_by_this_plan": False, "network_requests_performed": False,
        "note": "Planning is not an OS quota guarantee. Explicit --install is required."}


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class DownloadLedger:
    """Reservations are persisted before reads and never refunded or reset."""
    def __init__(self, work):
        self.path = work / "download-ledger.json"
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
            "schema_version": 1, "ceiling_bytes": DOWNLOAD_LIMIT, "reserved_bytes": 0, "reservations": []}
        if (self.data.get("schema_version") != 1 or self.data.get("ceiling_bytes") != DOWNLOAD_LIMIT
                or type(self.data.get("reserved_bytes")) is not int
                or not 0 <= self.data["reserved_bytes"] <= DOWNLOAD_LIMIT
                or not isinstance(self.data.get("reservations"), list)
                or any(not isinstance(item, dict) or type(item.get("bytes")) is not int or item["bytes"] <= 0
                       or not isinstance(item.get("filename"), str) for item in self.data["reservations"])
                or sum(item["bytes"] for item in self.data["reservations"]) != self.data["reserved_bytes"]):
            raise SetupError("Download ledger is invalid; do not reset the approved budget")

    def reserve(self, amount, filename):
        if type(amount) is not int or amount <= 0 or self.data["reserved_bytes"] + amount > DOWNLOAD_LIMIT:
            raise SetupError("Persistent 150 MB artifact-payload allowance is exhausted")
        self.data["reserved_bytes"] += amount
        self.data["reservations"].append({"filename": filename, "bytes": amount})
        atomic_json(self.path, self.data)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise SetupError("Wheel redirect refused")


def verify_wheel(path, package):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != package["compressed_bytes"] or file_hash(path) != package["sha256"]:
        raise SetupError("Staged wheel size/SHA256 does not match the approved artifact")
    names, expanded = set(), 0
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = entry.orig_filename
            parts = (name[:-1] if entry.is_dir() else name).split("/")
            mode = (entry.external_attr >> 16) & 0o170000
            reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
            reserved.update(prefix + number for prefix in ("COM", "LPT") for number in "123456789¹²³")
            if (not name or "\\" in name or name.startswith("/") or ":" in name or ".." in parts
                    or name.casefold() in names or entry.flag_bits & 1 or mode == stat.S_IFLNK
                    or mode not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or any(not part or part == "." or part.endswith((".", " "))
                           or part.split(".")[0].rstrip(" ").upper() in reserved
                           or any(ord(char) < 32 or char in '<>"|?*' for char in part) for part in parts)
                    or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                raise SetupError("Unsafe or unsupported wheel archive entry")
            names.add(name.casefold())
            expanded += entry.file_size
    if expanded != package["declared_expanded_bytes"]:
        raise SetupError("Full wheel expanded declarations differ from the approved metadata")
    return expanded


def download_wheel(package, root, work, ledger, opener=None):
    target = inside(root, work / package["filename"])
    if target.exists():
        verify_wheel(target, package)
        return target
    part = inside(root, work / (package["filename"] + "." + uuid4().hex + ".part"))
    opener = opener or urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(package["url"], headers={"Accept-Encoding": "identity", "User-Agent": "KnowledgeDelta-approved-ui-setup/1"})
    try:
        with opener.open(request, timeout=30) as response:
            if (response.status != 200 or response.headers.get("Content-Encoding", "identity") != "identity"
                    or response.headers.get("Content-Length") != str(package["compressed_bytes"])):
                raise SetupError("Wheel response status, encoding or length differs from approval")
            with part.open("xb") as output:
                written = 0
                while written < package["compressed_bytes"]:
                    amount = min(CHUNK, package["compressed_bytes"] - written)
                    check_space(root, amount)
                    ledger.reserve(amount, package["filename"])
                    data = response.read(amount)
                    if not data or len(data) > amount:
                        raise SetupError("Wheel transfer was incomplete or exceeded its bound")
                    output.write(data)
                    written += len(data)
                ledger.reserve(1, package["filename"])
                if response.read(1):
                    raise SetupError("Wheel response exceeds the approved size")
        verify_wheel(part, package)
        part.replace(target)
        return target
    finally:
        # Only this invocation's uniquely named partial is removed; no recursive cleanup.
        if part.exists() and not part.is_symlink():
            part.unlink()


def child_environment(root, work):
    paths = {"USERPROFILE": "profile", "LOCALAPPDATA": "profile/AppData/Local", "APPDATA": "profile/AppData/Roaming",
        "TEMP": "temp", "TMP": "temp", "PIP_CACHE_DIR": "cache", "XDG_CACHE_HOME": "cache"}
    env = {k: v for k, v in os.environ.items() if not k.startswith("PIP_") and k not in (
        "PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTHONSTARTUP", "PYTHONINSPECT")}
    for name, suffix in paths.items():
        path = inside(root, work / suffix)
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env.update(PIP_CONFIG_FILE=os.devnull, PYTHONDONTWRITEBYTECODE="1", STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
               STREAMLIT_SERVER_HEADLESS="true")
    return env


def bootstrap_pip(root, work):
    original = Path(ensurepip.__file__).parent / "_bundled" / PIP_NAME
    if not original.is_file() or file_hash(original) != PIP_SHA256:
        raise SetupError("Existing bundled pip 26.2.2 hash differs; no bootstrap download is permitted")
    target = inside(root, work / PIP_NAME)
    if target.exists():
        if file_hash(target) != PIP_SHA256:
            raise SetupError("Project-local pip bootstrap differs; preserve and inspect it")
    else:
        check_space(root, original.stat().st_size)
        with original.open("rb") as source, target.open("xb") as output:
            shutil.copyfileobj(source, output, CHUNK)
    if file_hash(target) != PIP_SHA256:
        raise SetupError("Copied pip bootstrap hash mismatch")
    return target


def monitored_process(command, root, work, env, log_path, *, timeout=180):
    check_space(root)
    started = time.monotonic()
    with log_path.open("xb") as log:
        child = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            while child.poll() is None:
                check_space(root)
                if time.monotonic() - started > timeout:
                    raise SetupError("Local setup subprocess exceeded its time bound")
                time.sleep(.25)
            if child.returncode:
                raise SetupError(f"Local subprocess failed with exit {child.returncode}; inspect {log_path.relative_to(root)}")
            check_space(root)
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)


def install_wheel(package, wheel, root, work, pip_wheel, env):
    requirement = inside(root, work / "current-wheel.txt")
    requirement.write_text(f"{wheel.as_uri()} --hash=sha256:{package['sha256']}\n", encoding="utf-8")
    bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('pip',run_name='__main__')"
    command = [sys.executable, "-I", "-B", "-c", bootstrap, str(pip_wheel), "--isolated", "install", "--no-index", "--no-deps",
        "--no-compile", "--require-hashes", "--only-binary=:all:", "--disable-pip-version-check", "--no-input",
        "--cache-dir", env["PIP_CACHE_DIR"], "-r", str(requirement)]
    log = inside(root, work / ("pip-" + package["name"] + "-" + uuid4().hex + ".log"))
    monitored_process(command, root, work, env, log)


def readiness(packages, root, work, env):
    code = ("import importlib,importlib.metadata,json;names=" + repr([p["name"] for p in packages]) + ";"
        "versions={n:importlib.metadata.version(n) for n in names};"
        "modules={n:str(importlib.import_module(n).__file__) for n in ['streamlit','numpy','pandas','pyarrow']};"
        "print('KNOWLEDGEDELTA_READY='+json.dumps({'versions':versions,'imports':modules}))")
    log = inside(root, work / ("readiness-" + uuid4().hex + ".log"))
    monitored_process([sys.executable, "-I", "-B", "-c", code], root, work, env, log)
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    values = [line.split("=", 1)[1] for line in lines if line.startswith("KNOWLEDGEDELTA_READY=")]
    if len(values) != 1:
        raise SetupError("Readiness response is missing; imports remain unverified")
    value = json.loads(values[0])
    if (any(value["versions"].get(p["name"]) != p["version"] for p in packages)
            or any(not Path(path).resolve().is_relative_to(Path(sys.prefix).resolve()) for path in value["imports"].values())):
        raise SetupError("Installed versions or imported modules differ from the isolated approved setup")
    return value


def perform_install(root, packages, record):
    work = inside(root, root / ".tools/ui-setup")
    with evidence_lock(root, work):
        work.mkdir(parents=True, exist_ok=True)
        ledger = DownloadLedger(work)
        record["download_reserved_bytes_before"] = ledger.data["reserved_bytes"]
        pip_wheel = bootstrap_pip(root, work)
        env = child_environment(root, work)
        for number, package in enumerate(packages, 1):
            step = {"name": package["name"], "version": package["version"], "status": "pending"}
            record["steps"].append(step)
            print(f"[{number}/{len(packages)}] {package['name']} {package['version']}", flush=True)
            if installed_version(package, root) is not None:
                step.update(status="existing_version_matches", installed_files_independently_verified=False)
                continue
            check_space(root, package["compressed_bytes"] + 2 * package["declared_expanded_bytes"])
            wheel = download_wheel(package, root, work, ledger)
            step["artifact_sha256_verified"] = True
            install_wheel(package, wheel, root, work, pip_wheel, env)
            if installed_version(package, root) != package["version"]:
                raise SetupError("Pip exited without the expected installed version")
            step.update(status="installed", full_wheel_sha256=package["sha256"])
            # Delete only the exact verified staging wheel inside this owned workdir.
            if wheel.parent == work and file_hash(wheel) == package["sha256"]:
                wheel.unlink()
            record["download_reserved_bytes_after"] = ledger.data["reserved_bytes"]
        record["readiness"] = readiness(packages, root, work, env)
        record["download_reserved_bytes_after"] = ledger.data["reserved_bytes"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Explicitly perform the approved project-local UI-only setup")
    args = parser.parse_args(argv)
    record = {"schema_version": 1, "kind": "approved_ui_setup", "run_id": uuid4().hex,
        "started_at": datetime.now(timezone.utc).isoformat(), "steps": [], "models_downloaded": False,
        "server_started": False, "runtime_containment_verified": False, "os_quota_enforced": False}
    try:
        packages, setup_plan = plan(ROOT)
        record["plan"] = setup_plan
        if not args.install:
            print(json.dumps(setup_plan, indent=2))
            return 0
        perform_install(ROOT, packages, record)
        record["status"] = "installed_imports_verified_ui_not_started"
        code = 0
    except Exception as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    if args.install:
        report = inside(ROOT, ROOT / "runs/ui-setup" / (record["run_id"] + ".json"))
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(json.dumps({"status": record["status"], "report": str(report), "error": record.get("error"),
                          "server_started": False, "models_downloaded": False}, indent=2))
    else:
        print(json.dumps(record, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
