"""Explicit project-local CPU embedding package setup; default is a read-only plan.

Requires a successful dependency inspection. Does not download model weights,
start Ollama, change security policy, or fall back to hosted inference.
"""
import argparse
from datetime import datetime, timezone
from email.parser import BytesParser
from hashlib import sha256
import importlib.metadata
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit
from urllib.request import Request, build_opener
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_embedding_setup import (Ledger, CPU_LIMIT, STORAGE_LIMIT,
    cpu_dependency_reserved, reserve_cpu_dependency)
from scripts.inspect_ui_setup import packaging_api
from scripts.run_checks import evidence_lock
from scripts.setup_ui import (inside, file_hash, verify_wheel,
                              bootstrap_pip, child_environment, NoRedirect, SetupError)
from knowledge_delta.validation import read_json, ValidationError

RESERVE = 250_000_000
CHUNK = 1024 * 1024


def runtime_check(root):
    if (os.name != "nt" or sys.version_info[:3] not in ((3, 15, 2), (3, 14, 10))
            or platform.machine().lower() not in ("amd64", "x86_64")
            or sys.prefix == sys.base_prefix
            or not Path(sys.prefix).resolve().is_relative_to(root.resolve())):
        raise SetupError("Run with a project-local Windows AMD64 Python 3.14.10/3.15.2 virtual environment")


def check_space(root, extra=0):
    used = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    if used + extra + RESERVE > STORAGE_LIMIT:
        raise SetupError("Project plus CPU setup headroom exceeds the approved 12 GB ceiling")
    return used


dependency_reserved = cpu_dependency_reserved


class DependencyBudget:
    def __init__(self, ledger):
        self.ledger = ledger
    def reserve(self, amount, label):
        try:
            reserve_cpu_dependency(self.ledger, amount, label)
        except ValidationError as exc:
            raise SetupError(str(exc)) from exc


def validate_packages(report):
    if (report.get("kind") != "cpu_embedding_dependency_inspection"
            or report.get("status") != "dependency_metadata_inspected"
            or report.get("dependency_closure_metadata_verified") is not True):
        raise SetupError("Require a successful CPU dependency inspection; nothing installed")
    packages = report.get("packages")
    if not isinstance(packages, list) or not 1 <= len(packages) <= 80:
        raise SetupError("Invalid bounded dependency package list")
    Requirement, Version, canonical, parse_wheel, tags, environment = packaging_api()
    selected, converted = {}, []
    for original in packages:
        p = dict(original)
        name, version, _, wheel_tags = parse_wheel(p["filename"])
        url = urlsplit(p["url"])
        allowed = ("download.pytorch.org", "download-r2.pytorch.org") if name == "torch" else ("files.pythonhosted.org",)
        if (name in selected or canonical(p["name"]) != name or str(version) != p["version"]
                or not set(tags).intersection(wheel_tags) or version.is_prerelease
                or url.scheme != "https" or url.hostname not in allowed
                or url.username or url.password or url.port or url.fragment
                or unquote(url.path.rsplit("/", 1)[-1]) != p["filename"]
                or Path(p["filename"]).name != p["filename"]):
            raise SetupError("Dependency wheel identity/URL/compatibility mismatch")
        if name == "torch" and (version.local != "cpu" or not url.path.startswith("/whl/cpu/")):
            raise SetupError("An explicit CPU Torch wheel is required")
        for field in ("sha256", "metadata_sha256"):
            value = p.get(field, "")
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise SetupError("Exact wheel and metadata SHA256 are required")
        p["declared_expanded_bytes"] = p["archive"]["declared_expanded_bytes"]
        if any(type(p[field]) is not int or p[field] < 1 for field in ("compressed_bytes", "declared_expanded_bytes")):
            raise SetupError("Invalid wheel byte sizes")
        scope = p.get("requires_python")
        if scope and not Requirement("python" + scope).specifier.contains(environment["python_full_version"]):
            raise SetupError("Dependency excludes this Python")
        selected[name] = p
        converted.append(p)
    if not {"torch", "numpy", "sentence-transformers"}.issubset(selected):
        raise SetupError("CPU dependency roots missing")
    for p in converted:
        for raw in p["requires_dist"]:
            req = Requirement(raw)
            if req.marker and not req.marker.evaluate(dict(environment, extra="")):
                continue
            target = selected.get(canonical(req.name))
            if (req.url or req.extras or target is None
                    or not req.specifier.contains(target["version"])):
                raise SetupError("Dependency closure mismatch: " + raw)
    for raw in report["roots"]:
        req = Requirement(raw)
        if req.url or req.extras or req.marker or canonical(req.name) not in selected or not req.specifier.contains(selected[canonical(req.name)]["version"]):
            raise SetupError("Frozen root requirements mismatch")
    if sum(p["compressed_bytes"] for p in converted) > CPU_LIMIT:
        raise SetupError("CPU compressed dependency set exceeds 1 GB")
    return converted


def existing_version(package):
    try:
        dist = importlib.metadata.distribution(package["name"])
    except importlib.metadata.PackageNotFoundError:
        return None
    if not Path(dist.locate_file("")).resolve().is_relative_to(Path(sys.prefix).resolve()):
        raise SetupError("Dependency is outside the isolated project environment")
    if dist.version != package["version"]:
        raise SetupError("Existing version differs; preserve it and inspect the dependency constraints")
    return dist.version


def plan(root, inspection_path):
    runtime_check(root)
    report = read_json(inspection_path)
    if report.get("inspector_sha256") != file_hash(root / "scripts/inspect_embedding_setup.py"):
        raise SetupError("Dependency inspector source changed since the report; preserve and regenerate the report")
    model_report = inside(root, root / report.get("model_report_path", "runs/model-setup-inspection-cdn-fix.json"))
    if not model_report.is_relative_to(root / "runs"):
        raise SetupError("Model inspection binding must stay inside project runs")
    if report.get("model_report_sha256") != file_hash(model_report):
        raise SetupError("Model candidate report changed since dependency inspection")
    packages = validate_packages(report)
    work = inside(root, root / ".tools/model-setup")
    ledger_path = inside(root, work / "download-ledger.json")
    if not ledger_path.is_file():
        raise SetupError("Persistent model-setup transfer ledger missing; do not reset the budget")
    ledger = Ledger(ledger_path)
    pending = [p for p in packages if existing_version(p) is None]
    payload = sum(p["compressed_bytes"] + 1 for p in pending)
    if ledger.total + payload > ledger.data["ceiling_bytes"] or dependency_reserved(ledger) + payload > CPU_LIMIT:
        raise SetupError("Remaining transfer allowance cannot cover pending CPU dependencies")
    peak_extra = max((p["compressed_bytes"] for p in pending), default=0) + 2 * sum(p["declared_expanded_bytes"] for p in pending)
    current = check_space(root, peak_extra)
    return packages, {"status": "plan_ready", "inspection_sha256": file_hash(inspection_path),
        "packages": len(packages), "pending_packages": len(pending),
        "remaining_payload_reservation_bytes": payload,
        "conservative_planning_bytes": current + peak_extra + RESERVE,
        "folder_ceiling_bytes": STORAGE_LIMIT, "cpu_dependency_ceiling_bytes": CPU_LIMIT,
        "packages_installed": False, "model_weights_downloaded": False,
        "network_requests_performed": False, "native_imports_verified": False}


def download(package, root, work, ledger, opener=None, verifier=None):
    verifier = verifier or verify_package
    target = inside(root, work / package["filename"])
    if target.exists():
        verifier(target, package)
        return target
    part = inside(root, work / (package["filename"] + "." + uuid4().hex + ".part"))
    opener = opener or build_opener(NoRedirect)
    budget = DependencyBudget(ledger)
    try:
        with opener.open(Request(package["url"], headers={"Accept-Encoding": "identity"}), timeout=30) as response:
            if (response.status != 200 or response.headers.get("Content-Length") != str(package["compressed_bytes"])
                    or response.headers.get("Content-Encoding", "identity") != "identity"):
                raise SetupError("CPU wheel response differs from inspected artifact")
            with part.open("xb") as stream:
                remaining = package["compressed_bytes"]
                while remaining:
                    amount = min(CHUNK, remaining)
                    check_space(root, amount)
                    budget.reserve(amount, package["filename"])
                    data = response.read(amount)
                    if not data or len(data) > amount:
                        raise SetupError("Incomplete CPU wheel transfer")
                    stream.write(data)
                    remaining -= len(data)
                budget.reserve(1, package["filename"])
                if response.read(1):
                    raise SetupError("CPU wheel exceeds expected size")
        verifier(part, package)
        part.replace(target)
        return target
    finally:
        if part.exists() and not part.is_symlink():
            part.unlink()


def verify_package(path, package):
    verify_wheel(path, package)
    with zipfile.ZipFile(path) as archive:
        entries = [e for e in archive.infolist()
                   if e.filename.count("/") == 1 and e.filename.endswith(".dist-info/METADATA")]
        if len(entries) != 1 or entries[0].file_size > 1024 * 1024:
            raise SetupError("Wheel METADATA missing or too large")
        data = archive.read(entries[0])
        if sha256(data).hexdigest() != package["metadata_sha256"]:
            raise SetupError("Full wheel METADATA differs from dependency preflight")
        headers = BytesParser().parsebytes(data)
        if (headers["Name"].lower().replace("_", "-") != package["name"]
                or headers["Version"] != package["version"]
                or headers.get_all("Requires-Dist", []) != package["requires_dist"]
                or headers.get("Requires-Python") != package["requires_python"]):
            raise SetupError("Wheel dependency metadata differs from the locked package identity/edges")


def process(command, root, work, env, label):
    log = inside(root, work / (label + "-" + uuid4().hex + ".log"))
    with log.open("xb") as stream:
        child = subprocess.Popen(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
        started = time.monotonic()
        try:
            while child.poll() is None:
                check_space(root)
                if time.monotonic() - started > 180:
                    raise SetupError("CPU setup subprocess exceeded 180 seconds")
                time.sleep(.25)
            if child.returncode:
                raise SetupError("CPU setup/import failed; inspect " + str(log.relative_to(root)))
            check_space(root)
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
    return log


def install(root, packages, record):
    work = inside(root, root / ".tools/model-setup")
    with evidence_lock(root, work):
        ledger = Ledger(work / "download-ledger.json")
        pip_wheel = bootstrap_pip(root, work)
        env = child_environment(root, work)
        for key, relative in {"HF_HOME": "cache/hf", "HF_HUB_CACHE": "cache/hf/hub",
                              "HF_XET_CACHE": "cache/hf/xet", "TORCH_HOME": "cache/torch"}.items():
            directory = inside(root, work / relative)
            directory.mkdir(parents=True, exist_ok=True)
            env[key] = str(directory)
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        for number, p in enumerate(packages, 1):
            step = {"name": p["name"], "version": p["version"], "status": "pending"}
            record["steps"].append(step)
            print(f"[{number}/{len(packages)}] {p['name']} {p['version']}", flush=True)
            if existing_version(p):
                step.update(status="existing_version_matches", installed_files_independently_verified=False)
                continue
            check_space(root, p["compressed_bytes"] + 2 * p["declared_expanded_bytes"])
            try:
                wheel = download(p, root, work, ledger)
            finally:
                record["transfer_reserved_bytes"] = ledger.total
            requirement = inside(root, work / "current-cpu-wheel.txt")
            requirement.write_text(f"{wheel.as_uri()} --hash=sha256:{p['sha256']}\n", encoding="utf-8")
            bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('pip',run_name='__main__')"
            command = [sys.executable, "-I", "-B", "-c", bootstrap, str(pip_wheel),
                       "--isolated", "install", "--no-index", "--no-deps", "--no-compile",
                       "--require-hashes", "--only-binary=:all:", "--disable-pip-version-check",
                       "--no-input", "--cache-dir", env["PIP_CACHE_DIR"], "-r", str(requirement)]
            process(command, root, work, env, "pip-" + p["name"])
            if existing_version(p) != p["version"]:
                raise SetupError("Package install did not produce expected version")
            step.update(status="installed", artifact_sha256=p["sha256"], wheel_metadata_verified=True)
            wheel.unlink()
            record["transfer_reserved_bytes"] = ledger.total
        names = [p["name"] for p in packages]
        code = ("import importlib,importlib.metadata,json;versions={n:importlib.metadata.version(n) for n in " + repr(names) +
                "};modules={n:str(importlib.import_module(n).__file__) for n in ['torch','numpy','sentence_transformers','transformers','tokenizers']};"
                "print('KNOWLEDGEDELTA_CPU_READY='+json.dumps({'versions':versions,'imports':modules}))")
        log = process([sys.executable, "-I", "-B", "-c", code], root, work, env, "cpu-readiness")
        lines = [line.split("=", 1)[1] for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                 if line.startswith("KNOWLEDGEDELTA_CPU_READY=")]
        if len(lines) != 1:
            raise SetupError("CPU dependency readiness response missing")
        value = json.loads(lines[0])
        if (any(value["versions"].get(p["name"]) != p["version"] for p in packages)
                or any(not Path(p).resolve().is_relative_to(Path(sys.prefix).resolve()) for p in value["imports"].values())):
            raise SetupError("Native readiness versions/import locations differ from the isolated plan")
        record.update(readiness=value, transfer_reserved_bytes=ledger.total)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspection", default="runs/embedding-setup-inspection.json")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args(argv)
    record = {"schema_version": 1, "kind": "cpu_embedding_package_setup", "run_id": uuid4().hex,
              "started_at": datetime.now(timezone.utc).isoformat(), "steps": [],
              "model_weights_downloaded": False, "server_started": False,
              "os_quota_enforced": False, "runtime_containment_verified": False}
    try:
        inspection = inside(ROOT, ROOT / args.inspection)
        if not inspection.is_relative_to(ROOT / "runs"):
            raise SetupError("Select a project-local runs dependency inspection")
        packages, record["plan"] = plan(ROOT, inspection)
        if not args.install:
            print(json.dumps(record["plan"], indent=2))
            return 0
        install(ROOT, packages, record)
        record["status"] = "cpu_imports_verified_models_not_installed"
        code = 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    if args.install:
        report = inside(ROOT, ROOT / "runs/model-setup" / (record["run_id"] + ".json"))
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, indent=2) + "\n")
        record = {"status": record["status"], "report": str(report), "error": record.get("error"),
                  "model_weights_downloaded": False, "server_started": False}
    print(json.dumps(record, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
