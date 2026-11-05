"""Explicit ONNX Runtime CPU compatibility test; downloads no model weights.

Default is offline. --test resolves/inspects pinned-compatible wheels, installs
only missing dependencies locally, and tests runtime imports. It requests no PyTorch import, starts no Ollama service, changes no policy and
claims no embedding/model result.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_embedding_setup import Ledger, Reader, CPU_LIMIT, STORAGE_LIMIT
from scripts.inspect_ui_setup import archive_sizes, resolve_packages
from scripts.run_checks import evidence_lock
from scripts.setup_embeddings import (check_space, dependency_reserved, existing_version,
    install, runtime_check, validate_packages)
from scripts.setup_ui import inside, SetupError

ROOTS = ("onnxruntime", "numpy==2.5.4", "tokenizers==0.23.3")
REQUIRED = ("onnxruntime", "numpy", "tokenizers")
FORBIDDEN = {"torch", "sentence-transformers", "transformers", "onnxruntime-gpu", "onnxruntime-directml"}
MODULES = ("onnxruntime", "numpy", "tokenizers")


def inspect_dependencies(reader, existing_bytes):
    packages = resolve_packages(fetch=reader.request, root_requirements=ROOTS)
    if FORBIDDEN.intersection(p["name"] for p in packages):
        raise SetupError("ONNX compatibility graph must not include the blocked PyTorch stack")
    for package in packages:
        package["archive"] = archive_sizes(package["url"], package["compressed_bytes"], fetch=reader.request)
    packed = sum(p["compressed_bytes"] for p in packages)
    expanded = sum(p["archive"]["declared_expanded_bytes"] for p in packages)
    temporary_plan = existing_bytes + packed + 2 * expanded + 250_000_000
    if packed > CPU_LIMIT or temporary_plan > STORAGE_LIMIT:
        raise SetupError("ONNX dependency inspection exceeds approved CPU/storage limits")
    report = {"schema_version": 1, "kind": "cpu_embedding_dependency_inspection",
        "backend": "onnxruntime_cpu_candidate", "status": "dependency_metadata_inspected",
        "roots": list(ROOTS), "packages": packages, "python": sys.version,
        "dependency_closure_metadata_verified": True, "archive_bodies_verified": False,
        "compressed_wheel_bytes": packed, "declared_expanded_bytes": expanded,
        "dependency_temporary_planning_bytes": temporary_plan,
        "model_weights_downloaded": False, "packages_installed": False}
    validate_packages(report, required_roots=REQUIRED)
    return report


def validate_readiness(value):
    if value.get("torch_imported") is not False:
        raise SetupError("ONNX compatibility check must not import PyTorch")
    if set(value.get("imports", {})) != set(MODULES):
        raise SetupError("ONNX readiness must include the runtime, NumPy and tokenizer")
    if "CPUExecutionProvider" not in value.get("onnx_providers", []):
        raise SetupError("ONNX CPU execution provider unavailable")
    return value


def perform(root, record):
    runtime_check(root)
    if sys.version_info[:3] != (3, 14, 10):
        raise SetupError("Use the existing project-local .venv-ml Python 3.14.10")
    work = inside(root, root / ".tools/model-setup")
    ledger_path = inside(root, work / "download-ledger.json")
    if not ledger_path.is_file():
        raise SetupError("Existing shared model-setup ledger required; do not reset budget")
    with evidence_lock(root, work):
        ledger = Ledger(ledger_path)
        reader = Reader("", ledger)
        try:
            inspection = inspect_dependencies(reader, check_space(root))
        finally:
            record.update(metadata_requests=reader.requests,
                metadata_payload_bytes=reader.payload_bytes,
                transfer_reserved_bytes=ledger.total)
        packages = validate_packages(inspection, required_roots=REQUIRED)
        pending = [p for p in packages if existing_version(p) is None]
        payload = sum(p["compressed_bytes"] + 1 for p in pending)
        if dependency_reserved(ledger) + payload > CPU_LIMIT or ledger.total + payload > ledger.data["ceiling_bytes"]:
            raise SetupError("Remaining global/CPU transfer allowance cannot cover ONNX package test")
        check_space(root, max((p["compressed_bytes"] for p in pending), default=0)
                    + 2 * sum(p["declared_expanded_bytes"] for p in pending))
        record["inspection"] = inspection
        record["pending_packages"] = len(pending)
        record["pending_payload_bytes"] = payload
        # Freeze exact identities and dependencies before transferring full wheels.
        frozen = inside(root, root / "runs/onnx-setup" / (record["run_id"] + "-inspection.json"))
        frozen.parent.mkdir(parents=True, exist_ok=True)
        with frozen.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(inspection, indent=2) + "\n")
        record["inspection_path"] = str(frozen.relative_to(root))
    install(root, packages, record, import_modules=MODULES)
    validate_readiness(record["readiness"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args(argv)
    if not args.test:
        print(json.dumps({"status": "offline_plan", "backend": "onnxruntime_cpu_candidate",
            "dependency_roots": ROOTS, "import_modules": MODULES, "network_requests": 0,
            "model_weights_downloaded": False, "torch_import_requested": False}, indent=2))
        return 0
    record = {"schema_version": 1, "kind": "onnx_cpu_runtime_compatibility",
        "run_id": uuid4().hex, "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [], "model_weights_downloaded": False, "inference_performed": False,
        "torch_import_attempted": False, "security_settings_changed": False,
        "server_started": False}
    try:
        perform(ROOT, record)
        record["status"] = "onnx_runtime_imports_verified_model_not_tested"
        code = 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    report = inside(ROOT, ROOT / "runs/onnx-setup" / (record["run_id"] + ".json"))
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "report": str(report), "error": record.get("error"),
        "model_weights_downloaded": False, "inference_performed": False,
        "torch_import_attempted": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
