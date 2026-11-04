"""Offline preflight tests: synthetic PyPI metadata, ZIPs and HTTP responses only.

No packages, archives or network responses are fetched by this suite. A resolver
success below demonstrates its contract, not a real install or native import.
"""
from hashlib import sha256
from io import BytesIO
import json
import struct
from types import SimpleNamespace
import zipfile

import pytest

from scripts import inspect_ui_setup as inspect


@pytest.fixture(autouse=True)
def isolated_usage(monkeypatch):
    monkeypatch.setattr(inspect, "HTTP_USAGE", {"requests": 0, "payload_bytes": 0})


def synthetic_zip():
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("package/data.bin", b"x" * 100_000)
        archive.writestr("package/module.py", b"# inert synthetic source\n")
    return output.getvalue()


def archive_fetch(body):
    calls = []
    def fetch(url, *, limit, byte_range):
        start, end, total = byte_range
        assert url == "https://files.pythonhosted.org/test-only.whl"
        assert total == len(body) and end - start + 1 <= limit
        calls.append(byte_range)
        return body[start:end + 1]
    return fetch, calls


def test_real_zip_directory_parsing_counts_declared_bytes_without_extracting(tmp_path):
    body = synthetic_zip()
    fetch, calls = archive_fetch(body)
    result = inspect.archive_sizes("https://files.pythonhosted.org/test-only.whl", len(body), fetch=fetch)
    assert result["declared_expanded_bytes"] == 100_000 + len(b"# inert synthetic source\n")
    assert result["archive_entries"] == 2
    assert len(calls) == 2 and calls[0][0] > 0
    assert result["range_payload_bytes"] == sum(end - start + 1 for start, end, total in calls)
    assert "hash" in result["note"] and "unverified" in result["note"]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fault", ["zip64", "multidisk", "wrong_entry_count", "bad_directory_length", "truncated_end", "unsafe_name", "backslash_name"])
def test_unsupported_or_inconsistent_archive_metadata_fails_closed(fault):
    body = bytearray(synthetic_zip())
    end = body.rfind(b"PK\x05\x06")
    directory = struct.unpack_from("<I", body, end + 16)[0]
    if fault == "zip64":
        struct.pack_into("<HH", body, end + 8, 65535, 65535)
    elif fault == "multidisk":
        struct.pack_into("<H", body, end + 4, 1)
    elif fault == "wrong_entry_count":
        struct.pack_into("<HH", body, end + 8, 3, 3)
    elif fault == "bad_directory_length":
        struct.pack_into("<I", body, end + 12, 1)
    elif fault == "truncated_end":
        del body[-4:]
    elif fault == "unsafe_name":
        body[directory + 46:directory + 49] = b"../"
    else:
        body[directory + 46 + len("package")] = ord("\\")
    fetch, calls = archive_fetch(body)
    with pytest.raises((inspect.PreflightError, struct.error)):
        inspect.archive_sizes("https://files.pythonhosted.org/test-only.whl", len(body), fetch=fetch)


class Response:
    def __init__(self, status, body=b"", headers=None):
        self.status, self.body, self.headers = status, body, headers or {}
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, count):
        self.read_sizes.append(count)
        return self.body[:count]


def install_response(monkeypatch, response):
    requests = []
    def open_request(request, timeout):
        requests.append(request)
        return response
    monkeypatch.setattr(inspect.urllib.request, "build_opener", lambda *args: SimpleNamespace(open=open_request))
    return requests


def test_range_ignored_as_http200_is_rejected_before_reading_archive_body(monkeypatch):
    response = Response(200, b"not downloaded")
    install_response(monkeypatch, response)
    with pytest.raises(inspect.PreflightError, match="body was not read"):
        inspect.request_bytes("https://files.pythonhosted.org/test-only.whl", limit=10, byte_range=(4, 7, 100))
    assert response.read_sizes == []


@pytest.mark.parametrize("fault", ["wrong_total", "encoded", "short_body", "oversized_body"])
def test_range_identity_encoding_and_exact_body_length_are_checked(monkeypatch, fault):
    headers = {"Content-Range": "bytes 4-7/100"}
    body = b"1234"
    if fault == "wrong_total":
        headers["Content-Range"] = "bytes 4-7/101"
    elif fault == "encoded":
        headers["Content-Encoding"] = "gzip"
    elif fault == "short_body":
        body = b"123"
    else:
        body = b"12345"
    response = Response(206, body, headers)
    install_response(monkeypatch, response)
    with pytest.raises(inspect.PreflightError):
        inspect.request_bytes("https://files.pythonhosted.org/test-only.whl", limit=10, byte_range=(4, 7, 100))
    assert response.read_sizes == ([] if fault in ("wrong_total", "encoded") else [5])


def test_simple_api_media_type_and_global_transport_bounds(monkeypatch):
    response = Response(200, b"{}")
    requests = install_response(monkeypatch, response)
    assert inspect.request_bytes("https://pypi.org/simple/streamlit/", limit=100) == b"{}"
    headers = {k.lower(): v for k, v in requests[0].header_items()}
    assert headers["accept"] == "application/vnd.pypi.simple.v1+json"
    assert headers["accept-encoding"] == "identity"
    inspect.HTTP_USAGE["requests"] = inspect.MAX_REQUESTS
    with pytest.raises(inspect.PreflightError, match="network bound"):
        inspect.request_bytes("https://pypi.org/simple/streamlit/")
    assert len(requests) == 1
    inspect.HTTP_USAGE["requests"] = 0
    inspect.HTTP_USAGE["payload_bytes"] = inspect.MAX_NETWORK_PAYLOAD
    with pytest.raises(inspect.PreflightError, match="network bound"):
        inspect.request_bytes("https://pypi.org/simple/streamlit/")
    assert len(requests) == 1


@pytest.mark.parametrize("url", ["http://pypi.org/simple/x/", "https://other.invalid/x", "https://u:p@pypi.org/x", "https://pypi.org:443/x"])
def test_unapproved_hosts_schemes_and_credentials_never_reach_transport(monkeypatch, url):
    def forbidden(*args):
        raise AssertionError("URL validation must precede opening a connection")
    monkeypatch.setattr(inspect.urllib.request, "build_opener", forbidden)
    with pytest.raises(inspect.PreflightError, match="primary HTTPS"):
        inspect.request_bytes(url)


@pytest.fixture
def api():
    requirement, version, canonical, parse_wheel, tags, environment = inspect.packaging_api()
    native = next(iter(parse_wheel("demo-1.0-cp315-cp315-win_amd64.whl")[3]))
    generic = next(iter(parse_wheel("demo-1.0-py3-none-any.whl")[3]))
    target = dict(environment, python_version="3.15", python_full_version="3.15.2",
                  sys_platform="win32", platform_system="Windows", implementation_name="cpython")
    return requirement, version, canonical, parse_wheel, [native, generic], target


class Catalog:
    """Release JSON intentionally lacks PEP658 fields; Simple JSON provides them."""
    def __init__(self):
        self.versions, self.payloads, self.calls = {}, {}, []

    def add(self, name, version, dependencies=(), *, tag="py3-none-any", requires_python=">=3.11", yanked=False):
        filename = f"{name}-{version}-{tag}.whl"
        url = "https://files.pythonhosted.org/test-only/" + filename
        metadata = (f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\nRequires-Python: {requires_python}\n" +
                    "".join("Requires-Dist: " + value + "\n" for value in dependencies) + "\n").encode()
        artifact = {"filename": filename, "url": url, "size": 1234, "digests": {"sha256": "a" * 64},
                    "packagetype": "bdist_wheel", "yanked": yanked}
        simple = {"filename": filename, "url": url, "hashes": {"sha256": "a" * 64},
                  "core-metadata": {"sha256": sha256(metadata).hexdigest()}}
        self.versions.setdefault(name, {}).setdefault(version, []).append((artifact, simple))
        self.payloads[url + ".metadata"] = metadata
        return artifact, simple

    def fetch(self, url, *, limit=inspect.MAX_METADATA, byte_range=None):
        assert byte_range is None
        self.calls.append(url)
        if url in self.payloads:
            body = self.payloads[url]
        else:
            from packaging.version import Version
            pieces = url.removeprefix("https://pypi.org/").strip("/").split("/")
            name = pieces[1]
            versions = self.versions[name]
            if pieces[0] == "simple":
                value = {"meta": {"api-version": "1.3"}, "files": [simple for files in versions.values() for artifact, simple in files]}
            else:
                version = str(max(map(Version, versions))) if len(pieces) == 3 else pieces[2]
                value = {"info": {"version": version, "requires_dist": ["DO-NOT-USE-RELEASE-LEVEL-REQUIRES-DIST"]},
                         "releases": {v: [] for v in versions}, "urls": [a for a, s in versions[version]]}
            body = json.dumps(value).encode()
        assert len(body) <= limit
        return body


def test_full_simple_fallback_closure_uses_hashed_wheel_metadata_and_rebuilds_edges(api):
    catalog = Catalog()
    catalog.add("streamlit", "1.66.1", ["child>=1", "sibling>=1", "ignored[extra]; sys_platform == 'linux'", "optional; extra == 'charts'"])
    catalog.add("child", "2.0", ["obsolete>=1"])
    catalog.add("child", "1.0", ["active>=1"])
    catalog.add("sibling", "1.0", ["child<2"])
    catalog.add("obsolete", "1.0")
    catalog.add("active", "1.0")
    result = inspect.resolve_packages(fetch=catalog.fetch, api=api)
    assert {p["name"]: p["version"] for p in result} == {"streamlit": "1.66.1", "child": "1.0", "sibling": "1.0", "active": "1.0"}
    assert all(p["metadata_verified"] for p in result)
    assert "https://pypi.org/simple/streamlit/" in catalog.calls
    assert not any("ignored" in url or "optional" in url for url in catalog.calls)


@pytest.mark.parametrize("fault", ["conflict", "active_extra", "active_direct_url", "metadata_hash", "simple_identity"])
def test_unsupported_or_conflicting_metadata_never_produces_a_partial_closure(api, fault):
    catalog = Catalog()
    deps = {"conflict": ["child<1", "child>=2"], "active_extra": ["child[extra]>=1"],
            "active_direct_url": ["child @ https://other.invalid/child.whl"]}.get(fault, ["child>=1"])
    catalog.add("streamlit", "1.66.1", deps)
    artifact, simple = catalog.add("child", "2.0")
    if fault == "metadata_hash":
        catalog.payloads[artifact["url"] + ".metadata"] += b"changed"
    elif fault == "simple_identity":
        simple["hashes"]["sha256"] = "b" * 64
    with pytest.raises(inspect.PreflightError):
        inspect.resolve_packages(fetch=catalog.fetch, api=api)


def test_python_scope_yanked_and_wrong_abi_wheels_are_not_substituted(api):
    catalog = Catalog()
    catalog.add("streamlit", "1.66.1", ["child>=1"])
    catalog.add("child", "5.0", tag="cp314-cp314-win_amd64")
    catalog.add("child", "4.0", yanked=True)
    catalog.add("child", "3.0", requires_python=">=3.16")
    catalog.add("child", "2.0", tag="cp315-cp315-win_amd64")
    catalog.add("child", "2.0")
    result = inspect.resolve_packages(fetch=catalog.fetch, api=api)
    selected = next(p for p in result if p["name"] == "child")
    assert selected["version"] == "2.0" and "cp315-cp315-win_amd64" in selected["filename"]


def test_footprint_uses_declared_expansion_and_never_authorizes_an_install():
    packages = [{"compressed_bytes": 1000, "archive": {"declared_expanded_bytes": 260_000_000}}]
    result = inspect.footprint(packages, existing_bytes=10_000)
    assert result["declared_expanded_bytes"] == 260_000_000
    assert result["sequential_plan_fits_with_reserve"] is False
    assert result["sequential_with_additional_unpack_copy_bytes"] > result["sequential_wheel_planning_bytes"]
    assert result["installer_peak_verified"] is result["installation_authorized_by_this_report"] is False


def test_main_writes_only_inspection_json_without_creating_package_or_model_assets(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(inspect, "ROOT", tmp_path)
    package = {"name": "TEST-ONLY", "compressed_bytes": 1000}
    monkeypatch.setattr(inspect, "resolve_packages", lambda: [package])
    monkeypatch.setattr(inspect, "archive_sizes", lambda *args: {"declared_expanded_bytes": 5000})
    package["url"] = "https://files.pythonhosted.org/test-only.whl"
    assert inspect.main([]) == 0
    capsys.readouterr()
    files = [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()]
    assert files == ["runs/ui-setup-inspection.json"]
    report = json.loads((tmp_path / files[0]).read_text())
    assert report["packages_installed"] is report["models_downloaded"] is report["archive_bodies_verified"] is False
    assert report["footprint"]["installation_authorized_by_this_report"] is False


def test_inspection_output_cannot_overwrite_existing_reviews_or_json(tmp_path, monkeypatch):
    monkeypatch.setattr(inspect, "ROOT", tmp_path)
    runs = tmp_path / "runs"
    runs.mkdir()
    database = runs / "manual_reviews.sqlite3"
    database.write_bytes(b"TEST-ONLY existing journal bytes")
    existing = runs / "previous-inspection.json"
    existing.write_bytes(b'{"user_preserved_record":true}\n')
    def forbidden(*args, **kwargs):
        raise AssertionError("Output preservation must be checked before network activity")
    monkeypatch.setattr(inspect, "resolve_packages", forbidden)
    for target in (database, existing):
        original = target.read_bytes()
        with pytest.raises(SystemExit) as error:
            inspect.main(["--output", str(target)])
        assert error.value.code == 2 and target.read_bytes() == original
