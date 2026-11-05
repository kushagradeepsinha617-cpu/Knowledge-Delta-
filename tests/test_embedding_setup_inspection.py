"""Offline CPU dependency preflight tests; synthetic HTTP metadata only."""
from io import BytesIO
import json
from pathlib import Path

import pytest

from scripts import inspect_embedding_setup as cpu
from scripts.inspect_ui_setup import packaging_api
from knowledge_delta.validation import ValidationError


class Response:
    def __init__(self, status, data=b"", headers=None):
        self.status, self.data, self.headers = status, data, headers or {}
        self.read_sizes = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, amount):
        self.read_sizes.append(amount)
        return self.data[:amount]


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, []
    def open(self, request, **kwargs):
        self.calls.append(request)
        return self.response


def test_offline_default_has_no_downloads(monkeypatch, capsys):
    monkeypatch.setattr(cpu, "inspect", lambda *a: pytest.fail("No network by default"))
    assert cpu.main([]) == 0
    assert json.loads(capsys.readouterr().out)["network_requests"] == 0


def test_ledger_persists_prior_payload_and_never_refunds_failed_reads(tmp_path):
    path = tmp_path / "ledger.json"
    ledger = cpu.Ledger(path, previous=100)
    ledger.reserve(20, "test-metadata")
    assert cpu.Ledger(path).total == 120
    with pytest.raises(ValidationError, match="exhausted"):
        ledger.reserve(cpu.TRANSFER_LIMIT, "oversized")
    assert cpu.Ledger(path).total == 120


def test_reader_rejects_full_wheel_or_untrusted_host_without_open(tmp_path):
    opener = Opener(Response(200))
    reader = cpu.Reader("https://download-r2.pytorch.org/whl/cpu/test.whl",
                        cpu.Ledger(tmp_path / "ledger.json"), opener)
    for url in (reader.cpu_url, "https://example.com/package.whl.metadata"):
        with pytest.raises(ValidationError):
            reader.request(url)
    assert opener.calls == []


def test_range_http200_does_not_read_entire_archive(tmp_path):
    response = Response(200, b"not downloaded")
    reader = cpu.Reader("https://download-r2.pytorch.org/whl/cpu/test.whl",
                        cpu.Ledger(tmp_path / "ledger.json"), Opener(response))
    with pytest.raises(ValidationError, match="Unexpected"):
        reader.request(reader.cpu_url, limit=10, byte_range=(4, 7, 100))
    assert response.read_sizes == []
    assert reader.ledger.total == 0


def test_valid_range_is_reserved_before_read_and_exact_length_checked(tmp_path):
    response = Response(206, b"abcd", {"Content-Range": "bytes 4-7/100", "Content-Length": "4"})
    ledger = cpu.Ledger(tmp_path / "ledger.json")
    reader = cpu.Reader("https://download-r2.pytorch.org/whl/cpu/test.whl", ledger, Opener(response))
    assert reader.request(reader.cpu_url, limit=10, byte_range=(4, 7, 100)) == b"abcd"
    assert reader.payload_bytes == 4
    assert cpu.Ledger(ledger.path).total == 5


def candidate():
    return {"version": "2.15.0+cpu", "filename": "torch-2.15.0+cpu-cp315-cp315-win_amd64.whl",
            "url": "https://download-r2.pytorch.org/whl/cpu/torch-2.15.0%2Bcpu-cp315-cp315-win_amd64.whl#sha256=" + "a" * 64,
            "sha256": "a" * 64}


def test_cpu_metadata_uses_exact_version_and_keeps_whole_archive_unverified():
    class ReaderDouble:
        def request(self, url, **kwargs):
            if kwargs.get("head"):
                return 100_000
            return (b"Name: torch\nVersion: 2.15.0+cpu\nRequires-Python: >=3.11\n"
                    b"Requires-Dist: typing-extensions>=4\n\n")
    result = cpu.cpu_artifact(candidate(), ReaderDouble())
    assert result["version"] == "2.15.0+cpu"
    assert result["requires_dist"] == ["typing-extensions>=4"]
    assert result["metadata_verified"] is False
    assert result["compressed_bytes"] == 100_000


def test_cpu_metadata_rejects_wheel_identity_mismatch_before_network():
    item = candidate()
    item["version"] = "2.14.0+cpu"
    class Forbidden:
        def request(self, *args, **kwargs):
            pytest.fail("Validate CPU artifact identity before opening network")
    with pytest.raises(ValidationError, match="identity/compatibility"):
        cpu.cpu_artifact(item, Forbidden())


def test_all_native_metadata_paths_require_https_and_no_credentials(tmp_path):
    reader = cpu.Reader("https://download-r2.pytorch.org/whl/cpu/test.whl",
                        cpu.Ledger(tmp_path / "ledger.json"), Opener(Response(200)))
    for url in ("http://pypi.org/pypi/a/json", "https://user:secret@pypi.org/pypi/a/json"):
        with pytest.raises(ValidationError, match="Unsafe"):
            reader.validate_url(url)
