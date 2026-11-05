"""Explicit pinned Qwen model cache download, with Ollama stopped.

No model pull API, server start or inference. Uses Ollama v0.40.14's Windows
regular-file V2 manifest layout, verified from official manifest/paths.go.
"""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import socket
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_embedding_setup import Ledger, Reader
from scripts.run_checks import evidence_lock
from scripts.setup_embeddings import check_space, download
from scripts.setup_ui import inside, file_hash, SetupError

MODEL = "qwen3:1.7b"
MANIFEST_SHA256 = "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7"
PAYLOAD_BYTES = 1_359_293_444
MANIFEST_URL = "https://registry.ollama.ai/v2/library/qwen3/manifests/1.7b"
BLOB_BASE = "https://registry.ollama.ai/v2/library/qwen3/blobs/"
NAMED_MANIFEST = "manifests-v2/ollama.com/library/qwen3/1.7b"


def validate_url(url):
    p = urlsplit(url)
    host = p.hostname or ""
    if (p.scheme != "https" or p.username or p.password or p.port or p.fragment
            or not (host in ("registry.ollama.ai", "ollama.com", "registry.ollama.com")
                    or host.endswith(".r2.cloudflarestorage.com"))):
        raise SetupError("Qwen artifact redirect left approved HTTPS registry/storage hosts")
    return url


class RegistryRedirects(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2
    def http_error_302(self, req, fp, code, msg, headers):
        # urllib normally drains redirect bodies without a size bound. Close
        # the real response, then let its standard validated/limited redirect
        # logic operate on an empty local stream instead. No body is consumed.
        fp.close()
        return super().http_error_302(req, BytesIO(), code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class ModelBudget:
    def __init__(self, ledger):
        self.ledger = ledger
    def reserve(self, amount, label):
        self.ledger.reserve(amount, "model:qwen3-1.7b:" + label)


class ManifestReader(Reader):
    """Reuse bounded accounting without relaxing CPU-wheel preflight rules."""
    def validate_url(self, url, byte_range=None, head=False):
        if url != MANIFEST_URL or byte_range is not None or head:
            raise SetupError("Only the pinned Qwen manifest metadata endpoint is supported")
        validate_url(url)


@contextmanager
def stopped_server_guard():
    # A positive exclusive bind, held throughout writes, avoids guessing from
    # network timeouts and prevents the repository launcher binding mid-import.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as guard:
        if not hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            raise SetupError("This cache preparer currently requires Windows exclusive port guarding")
        guard.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            guard.bind(("127.0.0.1", 11434))
        except OSError as exc:
            raise SetupError("Stop the local Ollama server before populating its model cache") from exc
        yield


def manifest_parts(raw, expected_digest=MANIFEST_SHA256, expected_payload=PAYLOAD_BYTES):
    if sha256(raw).hexdigest() != expected_digest:
        raise SetupError("Registry tag differs from the pinned manifest; do not silently change experiments")
    data = json.loads(raw)
    if (not isinstance(data, dict) or data.get("schemaVersion") != 2 or "manifests" in data
            or not isinstance(data.get("config"), dict)
            or not isinstance(data.get("layers"), list) or not data["layers"]):
        raise SetupError("Only the pinned single-model schema-2 manifest is supported")
    parts = [data["config"], *data["layers"]]
    digests = set()
    for part in parts:
        if not isinstance(part, dict):
            raise SetupError("Invalid model layer descriptor")
        digest = part.get("digest", "")
        if (not isinstance(digest, str) or not re.fullmatch("sha256:[a-f0-9]{64}", digest) or digest in digests
                or type(part.get("size")) is not int or part["size"] < 1):
            raise SetupError("Invalid model layer digest or size")
        digests.add(digest)
    if sum(part["size"] for part in parts) != expected_payload:
        raise SetupError("Pinned model payload total differs")
    return parts


def verify_blob(path, package):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != package["compressed_bytes"] or file_hash(path) != package["sha256"]:
        raise SetupError("Model cache blob differs from pinned size/SHA256")


def write_exact(path, data):
    if path.exists():
        if path.is_symlink() or path.read_bytes() != data:
            raise SetupError("Preserve existing different model manifest; inspect it before proceeding")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(uuid4().hex + ".part")
    try:
        with part.open("xb") as stream:
            stream.write(data)
        part.replace(path)
    finally:
        if part.exists() and not part.is_symlink():
            part.unlink()


def prepare(root, record):
    work = inside(root, root / ".tools/model-setup")
    cache = inside(root, root / ".tools/models/ollama")
    ledger_path = inside(root, work / "download-ledger.json")
    if not ledger_path.is_file():
        raise SetupError("Existing approved transfer ledger required; do not reset allowance")
    with evidence_lock(root, work), stopped_server_guard():
        ledger = Ledger(ledger_path)
        budget = ModelBudget(ledger)
        try:
            opener = build_opener(RegistryRedirects)
            reader = ManifestReader(MANIFEST_URL, ledger, opener, reserve=lambda l,n,label: ModelBudget(l).reserve(n,label))
            raw = reader.request(MANIFEST_URL, limit=1024 * 1024)
            parts = manifest_parts(raw)
            named = inside(root, cache / NAMED_MANIFEST)
            if named.exists() and named.read_bytes() != raw:
                raise SetupError("Existing named manifest differs; preserve it")
            pending = 0
            packages = []
            for part in parts:
                digest = part["digest"].split(":", 1)[1]
                package = {"filename": "sha256-" + digest, "sha256": digest,
                           "compressed_bytes": part["size"], "url": validate_url(BLOB_BASE + part["digest"])}
                path = inside(root, cache / "blobs" / package["filename"])
                if path.exists():
                    verify_blob(path, package)
                else:
                    pending += package["compressed_bytes"] + 1
                packages.append(package)
            if ledger.total + pending > ledger.data["ceiling_bytes"]:
                raise SetupError("Remaining global artifact allowance cannot cover pinned Qwen blobs")
            check_space(root, pending + len(raw) * 2)
            blobs = inside(root, cache / "blobs")
            blobs.mkdir(parents=True, exist_ok=True)
            for package in packages:
                print("Qwen blob: " + package["filename"] + " (" + str(package["compressed_bytes"]) + " bytes)", flush=True)
                progress_state = [0]
                def progress(written):
                    if written - progress_state[0] >= 64 * 1024 * 1024 or written == package["compressed_bytes"]:
                        print(f"Qwen transfer: {written}/{package['compressed_bytes']} bytes", flush=True)
                        progress_state[0] = written
                path = download(package, root, blobs, ledger, opener,
                    verifier=verify_blob, budget=budget, space_check_interval=16 * 1024 * 1024, progress=progress)
                verify_blob(path, package)
                record["blobs"].append({"digest": "sha256:" + package["sha256"],
                                       "bytes": path.stat().st_size, "verified": True})
            # Raw bytes preserve the upstream manifest digest. Named file is last.
            manifest_blob = inside(root, blobs / ("sha256-" + MANIFEST_SHA256))
            write_exact(manifest_blob, raw)
            for package in packages:
                verify_blob(blobs / package["filename"], package)
            write_exact(named, raw)
            record.update(manifest_sha256=MANIFEST_SHA256, model=MODEL, payload_bytes=PAYLOAD_BYTES,
                          named_manifest=str(named), model_cache_verified=True,
                          raw_manifest_bytes=len(raw))
        finally:
            record["transfer_reserved_bytes"] = ledger.total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args(argv)
    if not args.download:
        print(json.dumps({"status": "offline_plan", "model": MODEL, "payload_bytes": PAYLOAD_BYTES,
                          "manifest_sha256": MANIFEST_SHA256, "cache_manifest": NAMED_MANIFEST,
                          "network_requests": 0, "server_started": False, "inference_performed": False}, indent=2))
        return 0
    record = {"kind": "pinned_qwen_local_cache_setup", "run_id": uuid4().hex, "blobs": [],
              "model_cache_verified": False, "server_started": False, "inference_performed": False,
              "security_settings_changed": False}
    try:
        prepare(ROOT, record)
        record["status"] = "pinned_model_cache_verified_discovery_pending"
        code = 0
    except Exception as exc:
        record.update(status="partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        code = 2
    output = inside(ROOT, ROOT / "runs/qwen-setup" / (record["run_id"] + ".json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "report": str(output), "error": record.get("error"),
                      "model_cache_verified": record["model_cache_verified"],
                      "server_started": False, "inference_performed": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
