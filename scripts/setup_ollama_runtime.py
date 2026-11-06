"""Explicit pinned portable Ollama runtime preparation; no model download/server start."""
import argparse
from hashlib import sha256
import json
from io import BytesIO
from pathlib import Path
import shutil
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.ollama_runtime import runtime_plan
from scripts.inspect_embedding_setup import Ledger, Reader
from scripts.inspect_ui_setup import archive_sizes
from scripts.run_checks import evidence_lock
from scripts.setup_embeddings import check_space, download, process
from scripts.setup_ui import inside, file_hash, verify_wheel, child_environment, SetupError

VERSION = "0.40.14"
URL = "https://github.com/ollama/ollama/releases/download/v0.40.14/ollama-windows-amd64.zip"
SIZE = 1_601_954_968
SHA256 = "65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29"
EXECUTABLE_SHA256 = "14e0fff0449ce3c3a7fe9db8b8b32089274db5f835d4c99f5af7c32dcbf08981"


def validate_url(url):
    p = urlsplit(url)
    if (p.scheme != "https" or p.username or p.password or p.port or p.fragment
            or p.hostname not in ("github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com")):
        raise SetupError("Runtime redirect left approved HTTPS GitHub release hosts")
    return url


class ReleaseRedirects(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2
    def http_error_302(self, req, fp, code, msg, headers):
        fp.close()
        return super().http_error_302(req, BytesIO(), code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class RuntimeBudget:
    def __init__(self, ledger):
        self.ledger = ledger
    def reserve(self, amount, label):
        self.ledger.reserve(amount, "runtime:" + label)


def extract(path, package, target):
    verify_wheel(path, package)
    if target.exists() or target.is_symlink():
        raise SetupError("Runtime target already exists; preserve it")
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            destination = target / item.filename
            if not destination.resolve().is_relative_to(target.resolve()):
                raise SetupError("Runtime archive escapes its owned destination")
        target.mkdir()
        for item in archive.infolist():
            destination = target / item.filename
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
    if not (target / "ollama.exe").is_file():
        raise SetupError("Pinned runtime archive lacks expected ollama.exe")


def verify_cached_runtime(root, target):
    receipt = json.loads(inside(root, target / "KNOWLEDGEDELTA_RUNTIME.json").read_text(encoding="utf-8"))
    if not isinstance(receipt, dict):
        raise SetupError("Existing runtime receipt must be an object; preserve and inspect")
    files = receipt.get("files")
    if (receipt.get("archive_sha256") != SHA256 or receipt.get("release") != VERSION
            or receipt.get("source_archive") != URL or not isinstance(files, dict)
            or files.get("ollama.exe") != EXECUTABLE_SHA256):
        raise SetupError("Existing runtime receipt lacks the pinned executable identity; preserve and inspect")
    actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    if actual != set(files) | {"KNOWLEDGEDELTA_RUNTIME.json"}:
        raise SetupError("Runtime receipt does not cover the exact installed file set")
    for relative, expected in files.items():
        path = inside(root, target / relative)
        if not path.is_relative_to(target) or not path.is_file() or file_hash(path) != expected:
            raise SetupError("Existing runtime file differs from verified receipt")
    return receipt


def prepare(root, record):
    work = inside(root, root / ".tools/model-setup")
    target = inside(root, root / ".tools/runtime/ollama")
    target.parent.mkdir(parents=True, exist_ok=True)
    ledger_path = inside(root, work / "download-ledger.json")
    if not ledger_path.is_file():
        raise SetupError("Shared approved transfer ledger missing; do not reset it")
    with evidence_lock(root, work):
        ledger = Ledger(ledger_path)
        try:
            if not target.exists():
                opener = build_opener(ReleaseRedirects)
                reader = Reader(URL, ledger, opener, reserve=lambda l, n, label: RuntimeBudget(l).reserve(n, label))
                if reader.request(URL, head=True) != SIZE:
                    raise SetupError("Runtime release size differs from the approved pinned artifact")
                archive = archive_sizes(URL, SIZE, fetch=reader.request)
                expanded = archive["declared_expanded_bytes"]
                # Streaming extraction makes one new expanded copy; rename does not duplicate it.
                check_space(root, SIZE + expanded)
                if ledger.total + SIZE + 1 > ledger.data["ceiling_bytes"]:
                    raise SetupError("Remaining transfer allowance cannot cover pinned Ollama runtime")
                package = {"filename": "ollama-windows-amd64.zip", "url": URL, "sha256": SHA256,
                    "compressed_bytes": SIZE, "declared_expanded_bytes": expanded}
                record["archive"] = package
                record["archive_directory"] = archive
                print(json.dumps({"phase": "runtime_transfer", "compressed_bytes": SIZE,
                                  "declared_expanded_bytes": expanded}), flush=True)
                progress_state = [0]
                def progress(written):
                    if written - progress_state[0] >= 64 * 1024 * 1024 or written == SIZE:
                        print(f"Ollama archive: {written}/{SIZE} bytes", flush=True)
                        progress_state[0] = written
                path = download(package, root, work, ledger, opener,
                    verifier=verify_wheel, budget=RuntimeBudget(ledger),
                    space_check_interval=16 * 1024 * 1024, progress=progress)
                staging = inside(root, target.parent / ("ollama-staging-" + uuid4().hex))
                extract(path, package, staging)
                receipt = {"release": VERSION, "source_archive": URL, "archive_sha256": SHA256,
                    "files": {p.relative_to(staging).as_posix(): file_hash(p)
                              for p in staging.rglob("*") if p.is_file()}}
                (staging / "KNOWLEDGEDELTA_RUNTIME.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
                staging.rename(target)
                if path.parent == work and file_hash(path) == SHA256:
                    path.unlink()
            verify_cached_runtime(root, target)
            executable = target / "ollama.exe"
            launch_plan = runtime_plan(root, executable)
            env = child_environment(root, work)
            env.update(launch_plan["environment_overrides"])
            for name in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "OLLAMA_MODELS"):
                Path(env[name]).mkdir(parents=True, exist_ok=True)
            record["runtime_sha256"] = launch_plan["runtime_sha256"]
            record["native_version_attempted"] = True
            log = process([str(executable), "--version"], root, work, env, "ollama-version")
            text = log.read_text(encoding="utf-8", errors="replace")
            if VERSION not in text:
                raise SetupError("Native CLI did not report the pinned Ollama version")
            record.update(native_version_verified=True, version_output=text,
                          runtime_path=str(executable), launch_plan=launch_plan)
        finally:
            record["transfer_reserved_bytes"] = ledger.total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args(argv)
    if not args.prepare:
        print(json.dumps({"status": "offline_plan", "release": VERSION, "url": URL, "bytes": SIZE,
                          "sha256": SHA256, "network_requests": 0, "model_weights_downloaded": False,
                          "server_started": False}, indent=2))
        return 0
    record = {"kind": "pinned_ollama_runtime_preparation", "run_id": uuid4().hex,
        "model_weights_downloaded": False, "server_started": False,
        "native_version_attempted": False, "native_version_verified": False,
        "security_settings_changed": False, "os_quota_enforced": False}
    try:
        prepare(ROOT, record)
        record["status"] = "runtime_verified_version_checked_server_not_started"
        code = 0
    except Exception as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    output = inside(ROOT, ROOT / "runs/ollama-setup" / (record["run_id"] + ".json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "report": str(output), "error": record.get("error"),
        "runtime_sha256": record.get("runtime_sha256"), "model_weights_downloaded": False,
        "server_started": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
