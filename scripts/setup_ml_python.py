"""Set up a project-local Python 3.14 ML environment; no system registration.

Default is an offline plan. --setup downloads the pinned official runtime,
creates .venv-ml, then runs bounded model/dependency metadata inspections.
It does not install ML packages, download model weights or change security.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_embedding_setup import Ledger, Reader
from scripts.inspect_model_setup import MAX_RESPONSE
from scripts.inspect_ui_setup import archive_sizes
from scripts.run_checks import evidence_lock
from scripts.setup_embeddings import check_space, download, process
from scripts.setup_ui import inside, verify_wheel, file_hash, child_environment, PIP_NAME, PIP_SHA256, SetupError
from knowledge_delta.validation import read_json

VERSION = "3.14.10"
URL = "https://www.python.org/ftp/python/3.14.10/python-3.14.10-amd64.zip"
ARCHIVE_SHA256 = "cc28026a650970cc1570bb127312f1f9634eb67abfe157ae6ca1acbbc627d091"
SOURCE = "https://www.python.org/ftp/python/3.14.10/windows-3.14.10.json"
MAX_ARCHIVE = 100_000_000
ENVIRONMENT_RESERVE = 100_000_000


def reserve_model_metadata(ledger):
    # Five bounded requests; retain the upper bound on interruption/retry.
    ledger.reserve(5 * (MAX_RESPONSE + 1), "model:ml314-candidate-metadata")


def extract(archive_path, package, target):
    """Validate every entry before creating a new, owned extraction directory."""
    verify_wheel(archive_path, package)
    if target.exists() or target.is_symlink():
        raise SetupError("Preserve existing Python target; select a fresh owned directory")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        # verify_wheel has already rejected traversal, symlinks and Windows hazards.
        for entry in entries:
            destination = target / entry.filename
            if not destination.resolve().is_relative_to(target.resolve()):
                raise SetupError("Runtime extraction escapes its target")
        target.mkdir()
        for entry in entries:
            destination = target / entry.filename
            if entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
    if not (target / "python.exe").is_file() or not (target / "Lib/venv/__init__.py").is_file():
        raise SetupError("Official runtime lacks expected executable/venv; preserve partial evidence")


def perform(root, record):
    work = inside(root, root / ".tools/model-setup")
    target = inside(root, root / ".tools/python-3.14")
    environment = inside(root, root / ".venv-ml")
    model_report = root / "runs/model-setup-inspection-ml314.json"
    dependency_report = root / "runs/embedding-setup-inspection-ml314.json"
    if model_report.exists() or dependency_report.exists():
        raise SetupError("Preserve existing ML inspection reports; review them before repeating setup")
    with evidence_lock(root, work):
        work.mkdir(parents=True, exist_ok=True)
        ledger_path = inside(root, work / "download-ledger.json")
        if not ledger_path.is_file():
            raise SetupError("Existing model-setup transfer ledger required; do not reset the allowance")
        ledger = Ledger(ledger_path)
        env = child_environment(root, work)
        if not target.exists():
            reader = Reader(URL, ledger)
            size = reader.request(URL, head=True)
            if size > MAX_ARCHIVE:
                raise SetupError("Python runtime archive exceeds its explicit 100 MB bound")
            declarations = archive_sizes(URL, size, fetch=reader.request)
            package = {"filename": URL.rsplit("/", 1)[-1], "url": URL,
                       "compressed_bytes": size, "sha256": ARCHIVE_SHA256,
                       "declared_expanded_bytes": declarations["declared_expanded_bytes"]}
            check_space(root, size + 2 * package["declared_expanded_bytes"] + ENVIRONMENT_RESERVE)
            record["archive"] = package
            archive_path = download(package, root, work, ledger, verifier=verify_wheel)
            staging = inside(root, root / ".tools" / ("python-3.14-staging-" + uuid4().hex))
            extract(archive_path, package, staging)
            receipt = {"version": VERSION, "url": URL, "archive_sha256": ARCHIVE_SHA256,
                       "files": {p.relative_to(staging).as_posix(): file_hash(p)
                                 for p in staging.rglob("*") if p.is_file()}}
            (staging / "KNOWLEDGEDELTA_RUNTIME.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            staging.rename(target)
            if archive_path.parent == work and file_hash(archive_path) == ARCHIVE_SHA256:
                archive_path.unlink()
        receipt = read_json(target / "KNOWLEDGEDELTA_RUNTIME.json")
        if receipt.get("archive_sha256") != ARCHIVE_SHA256:
            raise SetupError("Existing runtime receipt differs; preserve and inspect")
        for relative, expected in receipt["files"].items():
            path = inside(root, target / relative)
            if not path.is_relative_to(target) or file_hash(path) != expected:
                raise SetupError("Existing runtime file changed: " + relative)
        record["runtime_files_verified"] = True
        # Reuse the already verified project-local pip wheel; no global ensurepip.
        pip_source = inside(root, root / ".tools/ui-setup" / PIP_NAME)
        pip_target = inside(root, work / PIP_NAME)
        if not pip_target.exists():
            if file_hash(pip_source) != PIP_SHA256:
                raise SetupError("Project pip bootstrap hash mismatch")
            shutil.copyfile(pip_source, pip_target)
        if file_hash(pip_target) != PIP_SHA256:
            raise SetupError("ML pip bootstrap hash mismatch")
        if not environment.exists():
            check_space(root, ENVIRONMENT_RESERVE)
            process([str(target / "python.exe"), "-I", "-B", "-m", "venv", "--without-pip", str(environment)],
                    root, work, env, "create-ml-environment")
        executable = inside(root, environment / "Scripts/python.exe")
        probe = ("import json,sys,platform;print('KNOWLEDGEDELTA_ML_PYTHON='+json.dumps("
                 "{'version':list(sys.version_info[:3]),'prefix':sys.prefix,'base_prefix':sys.base_prefix,'machine':platform.machine()}))")
        log = process([str(executable), "-I", "-B", "-c", probe], root, work, env, "ml-python-probe")
        rows = [line.split("=", 1)[1] for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.startswith("KNOWLEDGEDELTA_ML_PYTHON=")]
        if len(rows) != 1:
            raise SetupError("ML Python probe response missing")
        value = json.loads(rows[0])
        if (value["version"] != [3, 14, 10] or Path(value["prefix"]).resolve() != environment
                or Path(value["base_prefix"]).resolve() != target or value["machine"].lower() != "amd64"):
            raise SetupError("ML Python runtime/prefix differs from the project-local plan")
        record["python"] = value
        record["transfer_reserved_bytes"] = ledger.total
    # Candidate metadata reads also consume the global approved transfer budget.
    with evidence_lock(root, work):
        reserve_model_metadata(Ledger(work / "download-ledger.json"))
    # The dependency inspection acquires the shared ledger lock itself.
    process([str(executable), "-I", "-B", str(root / "scripts/inspect_model_setup.py"),
             "--online-metadata", "--output", str(model_report)], root, work, env, "ml-model-metadata")
    process([str(executable), "-I", "-B", str(root / "scripts/inspect_embedding_setup.py"),
             "--inspect", "--model-report", str(model_report), "--output", str(dependency_report)],
            root, work, env, "ml-dependency-metadata")
    record["model_report"] = str(model_report)
    record["dependency_report"] = str(dependency_report)
    record["dependency_status"] = read_json(dependency_report)["status"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true")
    args = parser.parse_args(argv)
    if not args.setup:
        print(json.dumps({"status": "offline_plan", "runtime_version": VERSION, "archive_url": URL,
                          "archive_sha256": ARCHIVE_SHA256, "source_manifest": SOURCE,
                          "archive_limit_bytes": MAX_ARCHIVE, "network_requests": 0,
                          "system_registration_performed": False, "model_weights_downloaded": False}, indent=2))
        return 0
    record = {"kind": "project_local_ml_python_setup", "run_id": uuid4().hex,
              "source_manifest": SOURCE, "runtime_version": VERSION,
              "system_registration_performed": False, "ml_packages_installed": False,
              "model_weights_downloaded": False, "security_settings_changed": False}
    try:
        perform(ROOT, record)
        record["status"] = "python_ready_dependency_metadata_inspected"
        code = 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    report = inside(ROOT, ROOT / "runs/ml-python-setup" / (record["run_id"] + ".json"))
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "report": str(report), "error": record.get("error"),
                      "ml_packages_installed": False, "model_weights_downloaded": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
