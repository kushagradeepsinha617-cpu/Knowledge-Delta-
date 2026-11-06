"""Explicit pinned MiniLM ONNX download plus real offline embedding smoke.

Default is an offline plan. --download requires a successful runtime report.
No PyTorch, Ollama, hosted inference or automatic model substitutions.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from io import BytesIO
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.onnx_embeddings import ASSETS, MODEL_REVISION, inspect_assets, verify_asset
from knowledge_delta.validation import read_json
from scripts.inspect_embedding_setup import Ledger
from scripts.run_checks import evidence_lock
from scripts.setup_embeddings import check_space
from scripts.setup_ui import inside, SetupError
from scripts.smoke_onnx_embeddings import check as embedding_smoke

BASE = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/" + MODEL_REVISION + "/"
CHUNK = 1024 * 1024


def validate_url(url):
    p = urlsplit(url)
    host = p.hostname or ""
    if (p.scheme != "https" or p.username or p.password or p.port is not None or p.fragment
            or not (host == "huggingface.co" or host.endswith(".hf.co")
                    or host == "cdn-lfs.huggingface.co")):
        raise SetupError("Model redirect left approved HTTPS Hugging Face/CDN hosts")
    return url


class HuggingFaceRedirects(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2
    def http_error_302(self, req, fp, code, msg, headers):
        fp.close()
        return super().http_error_302(req, BytesIO(), code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def runtime_ready(report, root):
    if report.get("status") != "onnx_runtime_imports_verified_model_not_tested":
        raise SetupError("Require the successful ONNX runtime compatibility report")
    expected_prefix = (root / ".venv-ml").resolve()
    if (sys.prefix == sys.base_prefix or not expected_prefix.is_relative_to(root.resolve())
            or Path(sys.prefix).resolve() != expected_prefix):
        raise SetupError("Run the download with this project .venv-ml isolated Python")
    value = report.get("readiness", {})
    if value.get("torch_imported") is not False or "CPUExecutionProvider" not in value.get("onnx_providers", []):
        raise SetupError("Runtime report lacks CPU-only candidate readiness")
    for name in ("onnxruntime", "numpy", "tokenizers"):
        location = Path(value["imports"][name]).resolve()
        if not location.is_relative_to((root / ".venv-ml").resolve()):
            raise SetupError("Runtime imports must come from project .venv-ml")
        actual_module = importlib.import_module(name)
        if not Path(actual_module.__file__).resolve().is_relative_to(expected_prefix):
            raise SetupError("Current runtime import is outside the project environment: " + name)
        if importlib.metadata.version(name) != value["versions"][name]:
            raise SetupError("Runtime version changed since compatibility test: " + name)
    import onnxruntime as ort
    import numpy
    import tokenizers
    ort.disable_telemetry_events()
    if "CPUExecutionProvider" not in ort.get_available_providers() or "torch" in sys.modules:
        raise SetupError("Current ONNX CPU runtime unavailable or PyTorch unexpectedly imported")


def fetch_asset(relative, pin, directory, root, ledger, record, opener=None):
    target = inside(root, directory / relative)
    if target.exists():
        actual = verify_asset(target, pin)
        return {"path": relative, "status": "existing_verified", "sha256": actual, "bytes": pin[0]}
    target.parent.mkdir(parents=True, exist_ok=True)
    part = inside(root, target.with_name(target.name + "." + uuid4().hex + ".part"))
    source = validate_url(BASE + relative)
    opener = opener or build_opener(HuggingFaceRedirects)
    if relative == "onnx/model.onnx":
        record["model_weights_download_attempted"] = True
    received = 0
    try:
        with opener.open(Request(source, headers={"Accept-Encoding": "identity",
                "User-Agent": "KnowledgeDelta-approved-local-model-setup/1"}), timeout=60) as response:
            validate_url(response.geturl())
            length = response.headers.get("Content-Length")
            if (response.status != 200 or response.headers.get("Content-Encoding", "identity") != "identity"
                    or (length is not None and length != str(pin[0]))):
                raise SetupError("Model asset response size/encoding differs from the pinned artifact")
            with part.open("xb") as stream:
                while received < pin[0]:
                    amount = min(CHUNK, pin[0] - received)
                    check_space(root, amount)
                    ledger.reserve(amount, "minilm:" + relative)
                    data = response.read(amount)
                    if not data or len(data) > amount:
                        raise SetupError("Incomplete pinned model asset transfer")
                    stream.write(data)
                    received += len(data)
                ledger.reserve(1, "minilm:" + relative)
                if response.read(1):
                    raise SetupError("Pinned model response exceeds expected bytes")
        actual = verify_asset(part, pin)
        part.replace(target)
        return {"path": relative, "status": "downloaded_verified", "sha256": actual, "bytes": received}
    finally:
        record["transfer_reserved_bytes"] = ledger.total
        record["asset_payload_written_bytes"] = record.get("asset_payload_written_bytes", 0) + received
        if part.exists() and not part.is_symlink():
            part.unlink()


def perform(root, runtime_report, record):
    runtime_ready(read_json(runtime_report), root)
    record["runtime_revalidated"] = True
    directory = inside(root, root / ".tools/models/minilm-onnx")
    work = inside(root, root / ".tools/model-setup")
    ledger_path = inside(root, work / "download-ledger.json")
    if not ledger_path.is_file():
        raise SetupError("Shared model-setup ledger missing; do not reset allowance")
    with evidence_lock(root, work):
        ledger = Ledger(ledger_path)
        pending = sum(pin[0] + 1 for relative, pin in ASSETS.items() if not (directory / relative).exists())
        if ledger.total + pending > ledger.data["ceiling_bytes"]:
            raise SetupError("Remaining approved artifact allowance cannot cover pinned MiniLM assets")
        check_space(root, 2 * pending)
        for relative, pin in ASSETS.items():
            print("MiniLM asset: " + relative, flush=True)
            result = fetch_asset(relative, pin, directory, root, ledger, record)
            record["assets"].append(result)
            if relative == "onnx/model.onnx":
                record["model_weights_verified"] = True
        _, hashes = inspect_assets(directory, root)
        provenance = {"model": "sentence-transformers/all-MiniLM-L6-v2", "revision": MODEL_REVISION,
                      "backend_artifact": "onnx/model.onnx", "sha256": hashes,
                      "license": "Apache-2.0", "model_card": "README.md", "source": BASE}
        (directory / "KNOWLEDGEDELTA_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        record["assets_verified"] = True
        record["model_directory"] = str(directory)
        record["transfer_reserved_bytes"] = ledger.total
    record["embedding_smoke_attempted"] = True
    record["embedding_smoke"] = embedding_smoke(directory, root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--runtime-report", type=Path)
    args = parser.parse_args(argv)
    if not args.download:
        print(json.dumps({"status": "offline_plan", "model_revision": MODEL_REVISION,
                          "artifact_bytes": sum(p[0] for p in ASSETS.values()), "files": list(ASSETS),
                          "network_requests": 0, "download_performed": False}, indent=2))
        return 0
    if args.runtime_report is None:
        parser.error("--download requires --runtime-report pointing to the successful ONNX test")
    record = {"schema_version": 1, "kind": "minilm_onnx_local_setup", "run_id": uuid4().hex,
              "started_at": datetime.now(timezone.utc).isoformat(), "assets": [],
              "model_weights_download_attempted": False, "model_weights_verified": False,
              "embedding_smoke_attempted": False, "answering_model_called": False,
              "security_settings_changed": False}
    try:
        runtime_report = inside(ROOT, ROOT / args.runtime_report)
        if not runtime_report.is_relative_to(ROOT / "runs"):
            raise SetupError("Select a project-local runtime compatibility report")
        perform(ROOT, runtime_report, record)
        record["status"] = "pinned_assets_and_real_embeddings_verified"
        code = 0
    except Exception as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    output = inside(ROOT, ROOT / "runs/minilm-setup" / (record["run_id"] + ".json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "report": str(output), "error": record.get("error"),
                      "model_weights_verified": record["model_weights_verified"],
                      "embedding_smoke_attempted": record["embedding_smoke_attempted"],
                      "answering_model_called": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
