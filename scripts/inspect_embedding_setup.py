"""Explicit CPU embedding dependency preflight; no install or model-weight download.

Reads bounded metadata and wheel ZIP directories only. Default prints a plan.
"""
import argparse
from datetime import datetime, timezone
from email.parser import BytesParser
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from urllib.parse import urldefrag, urlsplit
from urllib.request import Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_model_setup import NoRedirect
from scripts.inspect_ui_setup import archive_sizes, packaging_api, resolve_packages, PreflightError
from scripts.run_checks import evidence_lock
from knowledge_delta.validation import ValidationError, read_json

TRANSFER_LIMIT = 5_000_000_000
CPU_LIMIT = 1_000_000_000
STORAGE_LIMIT = 12_000_000_000
METADATA_LIMIT = 128_000_000


class Ledger:
    """Reserve before reading; interruptions and retries never reset the allowance."""
    def __init__(self, path, previous=0):
        if path.is_symlink():
            raise ValidationError("Ledger must not be a symlink")
        self.path = path
        self.data = read_json(path) if path.exists() else {
            "schema_version": 1, "ceiling_bytes": TRANSFER_LIMIT,
            "reservations": ([{"label": "earlier-model-metadata", "bytes": previous}] if previous else [])}
        entries = self.data.get("reservations")
        if (self.data.get("schema_version") != 1 or self.data.get("ceiling_bytes") != TRANSFER_LIMIT
                or not isinstance(entries, list)
                or any(type(e.get("bytes")) is not int or e["bytes"] <= 0 for e in entries)):
            raise ValidationError("Invalid model setup ledger; preserve and inspect it")
        self.total = sum(e["bytes"] for e in entries)
        if self.total > TRANSFER_LIMIT:
            raise ValidationError("Model setup transfer allowance exceeded")

    def reserve(self, amount, label):
        if type(amount) is not int or amount < 1 or self.total + amount > TRANSFER_LIMIT:
            raise ValidationError("Model setup transfer allowance exhausted")
        self.data["reservations"].append({"label": label, "bytes": amount})
        temporary = self.path.with_name(self.path.name + "." + uuid4().hex + ".tmp")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(self.data, indent=2) + "\n")
            temporary.replace(self.path)
        finally:
            if temporary.exists():
                temporary.unlink()
        self.total += amount


def cpu_dependency_reserved(ledger):
    return sum(e["bytes"] for e in ledger.data["reservations"]
               if e["label"] != "earlier-model-metadata"
               and not e["label"].startswith(("runtime:", "model:", "minilm:")))


def reserve_cpu_dependency(ledger, amount, label):
    if cpu_dependency_reserved(ledger) + amount > CPU_LIMIT:
        raise ValidationError("CPU dependency payload including retries exceeds the approved 1 GB allowance")
    ledger.reserve(amount, label)


class Reader:
    def __init__(self, cpu_url, ledger, opener=None):
        self.cpu_url, self.ledger = cpu_url, ledger
        self.opener = opener or build_opener(NoRedirect)
        self.requests, self.payload_bytes, self.reserved_bytes = 0, 0, 0

    def validate_url(self, url, byte_range=None, head=False):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port or parsed.fragment:
            raise ValidationError("Unsafe dependency metadata URL")
        if url in (self.cpu_url, self.cpu_url + ".metadata"):
            if url == self.cpu_url and not (head or byte_range):
                raise ValidationError("Full CPU wheel download forbidden in preflight")
        elif parsed.hostname == "pypi.org":
            if not (parsed.path.startswith("/pypi/") or parsed.path.startswith("/simple/")) or head or byte_range:
                raise ValidationError("Unsupported PyPI metadata endpoint")
        elif parsed.hostname == "files.pythonhosted.org":
            if not (parsed.path.endswith(".whl.metadata") or (parsed.path.endswith(".whl") and byte_range)):
                raise ValidationError("Only wheel metadata or bounded directory ranges allowed")
        else:
            raise ValidationError("Dependency metadata URL is outside primary sources")

    def request(self, url, *, limit=16 * 1024 * 1024, byte_range=None, head=False):
        self.validate_url(url, byte_range, head)
        if self.requests >= 400:
            raise ValidationError("Dependency metadata request bound reached")
        headers = {"Accept-Encoding": "identity", "User-Agent": "KnowledgeDelta-CPU-preflight/1"}
        if "/simple/" in url:
            headers["Accept"] = "application/vnd.pypi.simple.v1+json"
        if byte_range:
            start, end, total = byte_range
            if not 0 <= start <= end < total or end - start + 1 > limit:
                raise ValidationError("Invalid archive directory range")
            headers["Range"] = f"bytes={start}-{end}"
        self.requests += 1
        with self.opener.open(Request(url, headers=headers, method="HEAD" if head else "GET"), timeout=15) as response:
            expected_status = 206 if byte_range else 200
            if response.status != expected_status or response.headers.get("Content-Encoding", "identity") != "identity":
                raise ValidationError("Unexpected dependency metadata response")
            if head:
                raw = response.headers.get("Content-Length", "")
                if not raw.isdigit() or int(raw) < 22:
                    raise ValidationError("CPU archive size is unavailable")
                return int(raw)
            if byte_range and response.headers.get("Content-Range") != f"bytes {start}-{end}/{total}":
                raise ValidationError("Archive directory response range mismatch")
            bound = end - start + 1 if byte_range else limit
            length = response.headers.get("Content-Length")
            if length is not None:
                if not length.isdigit() or int(length) > bound:
                    raise ValidationError("Oversized metadata response; no body read")
                bound = int(length)
            reservation = bound + 1
            if self.reserved_bytes + reservation > METADATA_LIMIT:
                raise ValidationError("Metadata/range payload budget exhausted")
            reserve_cpu_dependency(self.ledger, reservation, url)
            self.reserved_bytes += reservation
            data = response.read(reservation)
            self.payload_bytes += len(data)
            if len(data) > bound or (byte_range and len(data) != end - start + 1):
                raise ValidationError("Incomplete or oversized metadata/range body")
            return data


def cpu_artifact(candidate, reader, api=None):
    Requirement, Version, canonical, parse_wheel, tags, environment = api or packaging_api()
    url, fragment = urldefrag(candidate["url"])
    name, version, _, wheel_tags = parse_wheel(candidate["filename"])
    parsed = urlsplit(url)
    if (parsed.hostname not in ("download.pytorch.org", "download-r2.pytorch.org")
            or not parsed.path.startswith("/whl/cpu/") or canonical(name) != "torch"
            or version.local != "cpu" or not set(tags).intersection(wheel_tags)
            or fragment != "sha256=" + candidate["sha256"]
            or not re.fullmatch("[a-f0-9]{64}", candidate["sha256"])
            or str(version) != candidate["version"]):
        raise ValidationError("CPU wheel identity/compatibility differs from the inspected candidate")
    size = reader.request(url, head=True)
    data = reader.request(url + ".metadata", limit=1024 * 1024)
    headers = BytesParser().parsebytes(data)
    if canonical(headers["Name"]) != "torch" or Version(headers["Version"]) != version:
        raise ValidationError("CPU wheel metadata name/version mismatch")
    scope = headers.get("Requires-Python")
    if scope and not Requirement("python" + scope).specifier.contains(environment["python_full_version"]):
        raise ValidationError("CPU wheel metadata excludes this Python")
    return {"name": "torch", "version": str(version), "filename": candidate["filename"],
            "url": url, "compressed_bytes": size, "sha256": candidate["sha256"],
            "metadata_sha256": sha256(data).hexdigest(), "requires_python": scope,
            "requires_dist": headers.get_all("Requires-Dist", []),
            "metadata_verified": False,
            "metadata_note": "TLS metadata identity checked; compare against the full hash-verified wheel before installation."}


def inspect(report, reader, existing_bytes):
    if report.get("status") != "metadata_inspected_setup_still_pending":
        raise ValidationError("Require the successful corrected model metadata report")
    cpu = cpu_artifact(report["cpu_torch"], reader)
    roots = ["sentence-transformers==" + report["sentence_transformers"]["candidate_version"],
             "torch==" + cpu["version"], "numpy==2.5.4"]
    packages = resolve_packages(fetch=reader.request, root_requirements=roots, external_wheels={"torch": cpu})
    for package in packages:
        package["archive"] = archive_sizes(package["url"], package["compressed_bytes"], fetch=reader.request)
    packed = sum(p["compressed_bytes"] for p in packages)
    expanded = sum(p["archive"]["declared_expanded_bytes"] for p in packages)
    # This is a dependency-only plan. Runtime/model archive expansion is a separate gate.
    temporary_plan = existing_bytes + packed + 2 * expanded + 250_000_000
    return {"schema_version": 1, "kind": "cpu_embedding_dependency_inspection",
            "status": "dependency_metadata_inspected" if packed <= CPU_LIMIT and temporary_plan <= STORAGE_LIMIT
                      else "dependency_plan_exceeds_limit",
            "python": sys.version, "roots": roots, "packages": packages,
            "dependency_closure_metadata_verified": True, "archive_bodies_verified": False,
            "compressed_wheel_bytes": packed, "declared_expanded_bytes": expanded,
            "dependency_temporary_planning_bytes": temporary_plan,
            "cpu_compressed_ceiling_bytes": CPU_LIMIT, "project_ceiling_bytes": STORAGE_LIMIT,
            "runtime_model_expansion_plan_verified": False, "installation_authorized_by_report": False,
            "packages_installed": False, "model_weights_downloaded": False,
            "note": "Metadata/range reads only. Full wheel hashes, METADATA, native behavior and total combined installer peak remain unverified."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--model-report", default="runs/model-setup-inspection-cdn-fix.json")
    parser.add_argument("--output", default="runs/embedding-setup-inspection.json")
    args = parser.parse_args(argv)
    if not args.inspect:
        print(json.dumps({"status": "offline_plan", "network_requests": 0,
                          "next": "Explicit --inspect reads dependency metadata and wheel directories; no installation."}))
        return 0
    report_path, output = (ROOT / args.model_report).resolve(), (ROOT / args.output).resolve()
    work = ROOT / ".tools/model-setup"
    if (not report_path.is_relative_to(ROOT / "runs") or not output.is_relative_to(ROOT / "runs")
            or output.suffix != ".json" or output.exists() or not work.resolve().is_relative_to(ROOT)):
        parser.error("Use existing project-local model report and new runs/*.json output; no symlinks")
    report = read_json(report_path)
    url = urldefrag(report.get("cpu_torch", {}).get("url", ""))[0]
    previous = 0
    for name in ("model-setup-inspection.json", "model-setup-inspection-cdn-fix.json"):
        path = ROOT / "runs" / name
        if path.exists():
            previous += read_json(path).get("metadata_payload_bytes", 0)
    record = {"schema_version": 1, "kind": "cpu_embedding_dependency_inspection",
              "packages_installed": False, "model_weights_downloaded": False}
    work.mkdir(parents=True, exist_ok=True)
    with evidence_lock(ROOT, work):
        ledger = Ledger(work / "download-ledger.json", previous)
        reader = Reader(url, ledger)
        try:
            existing = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
            record = inspect(report, reader, existing)
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
            record.update(status="metadata_partial_or_unavailable", error_type=type(exc).__name__, error=str(exc))
        record.update(metadata_requests=reader.requests, metadata_payload_bytes=reader.payload_bytes,
                      transfer_reserved_bytes=ledger.total,
                      model_report_sha256=sha256(report_path.read_bytes()).hexdigest(),
                      model_report_path=report_path.relative_to(ROOT).as_posix(),
                      inspector_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                      inspected_at=datetime.now(timezone.utc).isoformat())
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record.get(key) for key in (
        "status", "error", "compressed_wheel_bytes", "declared_expanded_bytes",
        "dependency_temporary_planning_bytes", "metadata_requests", "metadata_payload_bytes",
        "transfer_reserved_bytes", "packages_installed", "model_weights_downloaded")}, indent=2))
    return 0 if record["status"] == "dependency_metadata_inspected" else 2


if __name__ == "__main__":
    raise SystemExit(main())
