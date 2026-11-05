"""Explicit read-only UI preflight: metadata/range requests, no installation or models."""
import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
LIMIT = 250_000_000
MAX_METADATA = 16 * 1024 * 1024
MAX_DIRECTORY = 2 * 1024 * 1024
HTTP_USAGE = {"requests": 0, "payload_bytes": 0}
MAX_REQUESTS = 400
MAX_NETWORK_PAYLOAD = 128 * 1024 * 1024


class PreflightError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PreflightError("Redirect refused; inspect the published artifact URL")


def request_bytes(url, *, limit=MAX_METADATA, byte_range=None):
    if HTTP_USAGE["requests"] >= MAX_REQUESTS or HTTP_USAGE["payload_bytes"] >= MAX_NETWORK_PAYLOAD:
        raise PreflightError("Metadata investigation reached its network bound")
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ("pypi.org", "files.pythonhosted.org")
            or parsed.username or parsed.password or parsed.port is not None):
        raise PreflightError("Only primary HTTPS PyPI/artifact URLs are permitted")
    headers = {"User-Agent": "KnowledgeDelta-UI-preflight/1", "Accept-Encoding": "identity"}
    if parsed.hostname == "pypi.org" and parsed.path.startswith("/simple/"):
        headers["Accept"] = "application/vnd.pypi.simple.v1+json"
    if byte_range is not None:
        start, end, total = byte_range
        if not 0 <= start <= end < total or end - start + 1 > limit:
            raise PreflightError("Invalid or oversized archive metadata range")
        headers["Range"] = f"bytes={start}-{end}"
    HTTP_USAGE["requests"] += 1
    with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url, headers=headers), timeout=15) as response:
        expected_status = 206 if byte_range else 200
        if response.status != expected_status:
            raise PreflightError("Expected bounded HTTP206 for archive metadata; response body was not read" if byte_range else "Metadata request failed")
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise PreflightError("Encoded response prevents exact byte accounting")
        if byte_range and response.headers.get("Content-Range") != f"bytes {start}-{end}/{total}":
            raise PreflightError("Archive Content-Range differs from the requested metadata")
        read_bound = min(limit, end - start + 1) if byte_range else limit
        data = response.read(min(read_bound + 1, MAX_NETWORK_PAYLOAD - HTTP_USAGE["payload_bytes"]))
        HTTP_USAGE["payload_bytes"] += len(data)
        if len(data) > limit or (byte_range and len(data) != end - start + 1):
            raise PreflightError("Metadata response exceeded its bound or was incomplete")
        return data


def archive_sizes(url, size, fetch=request_bytes):
    """Read ZIP directory declarations, never extract or execute package contents."""
    if type(size) is not int or size < 22:
        raise PreflightError("Invalid wheel size")
    start = max(0, size - 65557)
    tail = fetch(url, limit=65557, byte_range=(start, size - 1, size))
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise PreflightError("ZIP end record missing")
    sig, disk, cd_disk, on_disk, count, length, position, comment = struct.unpack_from("<4s4H2IH", tail, offset)
    if offset + 22 + comment != len(tail) or disk or cd_disk or on_disk != count:
        raise PreflightError("Unsupported or inconsistent ZIP end record")
    if count == 65535 or length == 0xffffffff or position == 0xffffffff:
        raise PreflightError("ZIP64 is unsupported by this bounded inspector")
    if not 0 < length <= MAX_DIRECTORY or position + length != start + offset:
        raise PreflightError("Oversized or inconsistent ZIP directory")
    directory = fetch(url, limit=MAX_DIRECTORY, byte_range=(position, position + length - 1, size))
    cursor = total = compressed = 0
    names = set()
    for _ in range(count):
        if cursor + 46 > len(directory) or directory[cursor:cursor + 4] != b"PK\x01\x02":
            raise PreflightError("Malformed ZIP directory entry")
        flags, method = struct.unpack_from("<HH", directory, cursor + 8)
        packed, expanded, name_len, extra_len, comment_len, disk_start = struct.unpack_from("<II4H", directory, cursor + 20)
        external, local_offset = struct.unpack_from("<II", directory, cursor + 38)
        end = cursor + 46 + name_len + extra_len + comment_len
        if end > len(directory) or expanded == 0xffffffff or packed == 0xffffffff or local_offset == 0xffffffff:
            raise PreflightError("Truncated or ZIP64 directory entry")
        name = directory[cursor + 46:cursor + 46 + name_len].decode("utf-8" if flags & 2048 else "cp437")
        parts = name.replace("\\", "/").split("/")
        if (flags & 1 or method not in (0, 8) or disk_start or "\\" in name or name.startswith("/")
                or ":" in name or ".." in parts or name.casefold() in names
                or ((external >> 16) & 0o170000) == 0o120000 or local_offset >= position):
            raise PreflightError("Unsafe, duplicate or unsupported wheel entry")
        names.add(name.casefold())
        total += expanded
        compressed += packed
        if compressed > size:
            raise PreflightError("ZIP declarations exceed artifact size")
        cursor = end
    if cursor != len(directory):
        raise PreflightError("ZIP directory has unaccounted bytes")
    return {"declared_expanded_bytes": total, "archive_entries": count,
            "range_payload_bytes": len(tail) + len(directory),
            "note": "Directory declarations only; artifact body/hash, extraction and runtime remain unverified."}


def packaging_api():
    """Reuse hash-verified project sources; never install a resolver dependency."""
    manifest = json.loads((ROOT / "tests/dependency-sources.json").read_text(encoding="utf-8"))["packaging"]
    vendor = ROOT / ".tools/vendor/pip-vendor"
    if not vendor.resolve().is_relative_to(ROOT.resolve()):
        raise PreflightError("Staged dependency sources escape the project")
    for entry in manifest["files"]:
        path = (vendor / entry["path"]).resolve()
        if not path.is_relative_to(vendor.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise PreflightError("Staged packaging source differs from its recorded hash")
    sys.path.insert(0, str(vendor))
    from packaging.requirements import Requirement
    from packaging.version import Version
    from packaging.utils import canonicalize_name, parse_wheel_filename
    from packaging.tags import sys_tags
    from packaging.markers import default_environment
    return Requirement, Version, canonicalize_name, parse_wheel_filename, list(sys_tags()), default_environment()


def resolve_packages(fetch=request_bytes, api=None, *, root_requirements=None, external_wheels=None):
    """Bounded fixed-point resolver; unsupported forms/conflicts fail explicitly."""
    Requirement, Version, canonical, parse_wheel, tags, environment = api or packaging_api()
    rank = {tag: index for index, tag in enumerate(tags)}
    catalog_cache, release_cache, selection_cache, simple_cache = {}, {}, {}, {}
    environment = dict(environment, extra="")

    def metadata(url):
        return json.loads(fetch(url))

    def select(name, requirements):
        if name in (external_wheels or {}):
            artifact = external_wheels[name]
            if (canonical(artifact["name"]) != name
                    or not all(req.specifier.contains(artifact["version"]) for req in requirements)):
                raise PreflightError("External wheel does not satisfy dependency constraints: " + name)
            return artifact
        signature = (name, tuple(sorted(str(r.specifier) for r in requirements)))
        if signature in selection_cache:
            return selection_cache[signature]
        if name not in catalog_cache:
            catalog_cache[name] = metadata("https://pypi.org/pypi/" + name + "/json")
        catalog = catalog_cache[name]
        versions = []
        for raw in catalog["releases"]:
            version = Version(raw)
            if not version.is_prerelease and not version.is_devrelease and all(r.specifier.contains(version, prereleases=False) for r in requirements):
                versions.append(version)
        for version in sorted(versions, reverse=True)[:30]:
            key = (name, str(version))
            if key not in release_cache:
                release_cache[key] = (catalog if catalog["info"]["version"] == str(version) else
                    metadata(f"https://pypi.org/pypi/{name}/{version}/json"))
            release = release_cache[key]
            candidates = []
            for artifact in release["urls"]:
                if artifact.get("yanked") or artifact.get("packagetype") != "bdist_wheel":
                    continue
                project, wheel_version, build, wheel_tags = parse_wheel(artifact["filename"])
                matching = [rank[tag] for tag in wheel_tags if tag in rank]
                if canonical(project) == name and wheel_version == version and matching:
                    candidates.append((min(matching), artifact["filename"], artifact))
            for _, _, artifact in sorted(candidates):
                metadata_hash = artifact.get("core-metadata", artifact.get("dist-info-metadata"))
                if not isinstance(metadata_hash, dict):
                    if name not in simple_cache:
                        simple_cache[name] = metadata("https://pypi.org/simple/" + name + "/")
                    matching_files = [item for item in simple_cache[name]["files"] if item["filename"] == artifact["filename"]]
                    if len(matching_files) != 1:
                        raise PreflightError("Selected wheel is absent or ambiguous in the Simple API")
                    simple = matching_files[0]
                    simple_url = urllib.parse.urljoin("https://pypi.org/simple/" + name + "/", simple["url"])
                    if simple_url != artifact["url"] or simple["hashes"]["sha256"] != artifact["digests"]["sha256"]:
                        raise PreflightError("Release and Simple API artifact identities disagree")
                    metadata_hash = simple.get("core-metadata", simple.get("dist-info-metadata"))
                if not isinstance(metadata_hash, dict) or not re.fullmatch("[a-f0-9]{64}", metadata_hash.get("sha256", "")):
                    continue
                data = fetch(artifact["url"] + ".metadata", limit=1024 * 1024)
                if hashlib.sha256(data).hexdigest() != metadata_hash["sha256"]:
                    raise PreflightError("Wheel metadata hash mismatch")
                headers = BytesParser().parsebytes(data)
                if canonical(headers["Name"]) != name or Version(headers["Version"]) != version:
                    raise PreflightError("Wheel metadata identity mismatch")
                python_scope = headers.get("Requires-Python")
                if python_scope and not Requirement("python" + python_scope).specifier.contains(environment["python_full_version"]):
                    continue
                dependencies = headers.get_all("Requires-Dist", [])
                selected = {"name": name, "version": str(version), "filename": artifact["filename"],
                    "url": artifact["url"], "compressed_bytes": artifact["size"], "sha256": artifact["digests"]["sha256"],
                    "metadata_sha256": metadata_hash["sha256"], "requires_python": python_scope,
                    "requires_dist": dependencies, "metadata_verified": True}
                selection_cache[signature] = selected
                return selected
        raise PreflightError(f"No compatible hashed-metadata wheel found for {name}; bounded resolver does not substitute a source build")

    roots = [Requirement(raw) for raw in (root_requirements if root_requirements is not None else ["streamlit==1.66.1"])]
    root_constraints = {}
    for req in roots:
        if req.url or req.extras or req.marker:
            raise PreflightError("Root requirements must be explicit plain package constraints")
        root_constraints.setdefault(canonical(req.name), []).append(req)
    constraints = {name: list(reqs) for name, reqs in root_constraints.items()}
    seen = set()
    for iteration in range(20):
        signature = tuple((name, tuple(sorted(set(map(str, reqs))))) for name, reqs in sorted(constraints.items()))
        if signature in seen:
            raise PreflightError("Dependency constraints oscillate; use a separately reviewed resolver")
        seen.add(signature)
        if len(constraints) > 80:
            raise PreflightError("Dependency closure exceeds the 80-package investigation bound")
        selected = {name: select(name, reqs) for name, reqs in constraints.items()}
        following = {name: list(reqs) for name, reqs in root_constraints.items()}
        for package in selected.values():
            for raw in package["requires_dist"]:
                req = Requirement(raw)
                if req.marker and not req.marker.evaluate(environment):
                    continue
                if req.url or req.extras:
                    raise PreflightError("Direct URLs or transitive extras need separate review: " + raw)
                following.setdefault(canonical(req.name), []).append(req)
        next_signature = tuple((name, tuple(sorted(set(map(str, reqs))))) for name, reqs in sorted(following.items()))
        if next_signature == signature:
            return [selected[name] for name in sorted(selected)]
        constraints = following
    raise PreflightError("Dependency resolution did not stabilize within 20 rounds")


def footprint(packages, existing_bytes, reserve_bytes=25_000_000):
    packed = sum(p["compressed_bytes"] for p in packages)
    expanded = sum(p["archive"]["declared_expanded_bytes"] for p in packages)
    retained = existing_bytes + packed + expanded + reserve_bytes
    sequential = existing_bytes + max((p["compressed_bytes"] for p in packages), default=0) + expanded + reserve_bytes
    unpack_copy = sequential + expanded
    return {"existing_project_bytes": existing_bytes, "compressed_wheel_bytes": packed,
        "declared_expanded_bytes": expanded, "temporary_reserve_bytes": reserve_bytes,
        "retained_wheels_planning_bytes": retained, "sequential_wheel_planning_bytes": sequential,
        "sequential_with_additional_unpack_copy_bytes": unpack_copy,
        "approved_ceiling_bytes": LIMIT, "sequential_plan_fits_with_reserve": sequential <= LIMIT,
        "additional_unpack_copy_plan_fits_with_reserve": unpack_copy <= LIMIT,
        "installation_authorized_by_this_report": False,
        "installer_peak_verified": False,
        "note": "Planning totals, not measured installed/peak storage. Native behavior and installer overhead require separate checks."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="runs/ui-setup-inspection.json")
    args = parser.parse_args(argv)
    requested_output = ROOT / args.output
    output = requested_output.resolve()
    runs = (ROOT / "runs").resolve()
    if not runs.is_relative_to(ROOT.resolve()) or not output.is_relative_to(runs) or output == runs:
        parser.error("Output must stay inside this project's ignored runs folder")
    if output.suffix.lower() != ".json" or requested_output.is_symlink() or output.exists():
        parser.error("Choose a new .json output filename; existing files and symlinks are preserved")
    record = {"schema_version": 1, "kind": "ui_setup_inspection", "packages_installed": False,
              "models_downloaded": False, "archive_bodies_verified": False,
              "python": sys.version, "platform": sys.platform,
              "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "network_note": "Reads PyPI metadata and bounded wheel byte ranges; no archives are saved or extracted."}
    try:
        packages = resolve_packages()
        record["packages"] = packages
        for package in packages:
            package["archive"] = archive_sizes(package["url"], package["compressed_bytes"])
        existing = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
        record.update(status="preflight_inspected_not_installed", dependency_closure_verified=True,
                      footprint=footprint(packages, existing))
        code = 0
    except Exception as exc:
        record.update(status="unavailable_or_unsupported", error_type=type(exc).__name__, error=str(exc),
                      dependency_closure_verified=False)
        code = 2
    record["http_usage"] = dict(HTTP_USAGE)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, indent=2, allow_nan=False) + "\n")
    except OSError as exc:
        print(json.dumps({"status": "report_not_written", "error": str(exc),
                          "packages_installed": False, "models_downloaded": False}))
        return 2
    print(json.dumps({"status": record["status"], "output": str(output), "footprint": record.get("footprint"),
                      "error": record.get("error"), "packages_installed": False, "models_downloaded": False}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
