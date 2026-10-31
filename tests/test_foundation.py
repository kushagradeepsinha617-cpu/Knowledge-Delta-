"""Offline tests: no model, network, download, or generated input files."""
import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from knowledge_delta.cases import validate_dataset
from knowledge_delta.cli import main
from knowledge_delta.diff import compare
from knowledge_delta.doctor import readiness
from knowledge_delta.snapshots import load_snapshot, parse_snapshot
from knowledge_delta.validation import ValidationError, read_json

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "constructed"


def manifest(slot="before"):
    return json.loads((EXAMPLE / slot / "manifest.json").read_text(encoding="utf-8"))


def snapshot(raw=None, slot="before", overrides=None, root=None):
    raw = copy.deepcopy(manifest(slot) if raw is None else raw)
    bodies = {d["path"]: (EXAMPLE / slot / d["path"]).read_bytes() for d in manifest(slot)["documents"]}
    bodies.update(overrides or {})
    return parse_snapshot(raw, root or EXAMPLE / slot, lambda p: bodies[p.name])


def pair():
    return load_snapshot(EXAMPLE / "before" / "manifest.json"), load_snapshot(EXAMPLE / "after" / "manifest.json")


def dataset():
    return read_json(EXAMPLE / "cases.json")


def test_fixture_changes_and_snapshot_binding():
    before, after = pair()
    diff = compare(before, after)
    changes = {d["document_id"]: d for d in diff["document_changes"]}
    assert set(changes) == {"widget.config", "widget.install", "widget.legacy", "widget.scope", "widget.v2"}
    assert changes["widget.legacy"]["kind"] == "removed"
    assert changes["widget.v2"]["kind"] == "added"
    assert changes["widget.scope"]["metadata_changed"]
    assert not changes["widget.scope"]["content_changed"]
    assert changes["widget.config"]["content_changed"]
    assert changes["widget.config"]["metadata_changed"]
    assert validate_dataset(dataset(), before, after)["draft"] == 7
    assert validate_dataset(dataset(), before, after)["human_reviewed"] == 0


def test_canonical_identity_ignores_order_location_and_display_name():
    raw = manifest()
    raw["documents"][0]["software_versions"] = ["2", "1"]
    first = snapshot(raw)
    raw["name"] = "another label"
    raw["documents"].reverse()
    for doc in raw["documents"]:
        doc["software_versions"].reverse()
    other = snapshot(raw, root=Path("/virtual/other-snapshot"))
    assert first.snapshot_id == other.snapshot_id


def test_content_changes_preserve_document_identity_and_loaded_snapshot():
    before = snapshot()
    modified = snapshot(overrides={"config.md": b"An updated fact.\n"})
    assert before.document("widget.config").document_id == modified.document("widget.config").document_id
    assert before.document("widget.config").content != modified.document("widget.config").content
    assert before.snapshot_id != modified.snapshot_id
    with pytest.raises(FrozenInstanceError):
        before.domain = "mutated"
    assert before.document("widget.config").content.endswith("10 seconds.\n")


def test_exact_bytes_including_line_endings_affect_identity():
    before = snapshot()
    body = before.document("widget.config").content
    after = snapshot(overrides={"config.md": body.replace("\n", "\r\n").encode()})
    assert before.snapshot_id != after.snapshot_id


def test_default_version_change_is_visible_without_document_edits():
    raw = manifest()
    before = snapshot(raw)
    raw["default_version"] = "2"
    after = snapshot(raw)
    diff = compare(before, after)
    assert diff["document_changes"] == []
    assert diff["snapshot_metadata_changes"]["default_version"] == {"before": "1", "after": "2"}
    assert before.snapshot_id != after.snapshot_id


@pytest.mark.parametrize("path", ["../outside.md", "/outside.md", "C:/outside.md",
                                  "a\\b.md", "a//b.md", "./a.md", "a.json", "CON.md", "NUL.txt",
                                  "dir./file.md", "dir /file.md"])
def test_unsafe_paths_fail_before_read(path):
    raw = manifest()
    raw["documents"][0]["path"] = path
    def never_read(path):
        pytest.fail("invalid paths must fail before content is read")
    with pytest.raises(ValidationError, match="path"):
        parse_snapshot(raw, EXAMPLE, never_read)


def test_symlink_component_is_rejected_without_creating_one(monkeypatch):
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "config.md")
    with pytest.raises(ValidationError, match="symlink"):
        snapshot()


@pytest.mark.parametrize("mutation", ["duplicate_id", "duplicate_path", "unknown_field", "bool_schema", "duplicate_versions"])
def test_strict_manifest_rejection(mutation):
    raw = manifest()
    if mutation == "duplicate_id":
        raw["documents"][1]["document_id"] = raw["documents"][0]["document_id"]
    elif mutation == "duplicate_path":
        raw["documents"][1]["path"] = raw["documents"][0]["path"]
    elif mutation == "unknown_field":
        raw["effective_date"] = "invented"
    elif mutation == "bool_schema":
        raw["schema_version"] = True
    else:
        raw["documents"][0]["software_versions"] = ["1", "1"]
    with pytest.raises(ValidationError):
        snapshot(raw)


def test_invalid_utf8_is_actionable():
    with pytest.raises(ValidationError, match="UTF-8"):
        snapshot(overrides={"config.md": b"\xff"})


def test_unknown_version_metadata_is_preserved():
    assert snapshot().document("widget.scope").software_versions == ()


@pytest.mark.parametrize("mutation", ["snapshot", "quote", "missing_document", "version",
                                    "family_split", "review", "duplicate_case", "extra_expectation",
                                    "abstain_answer", "explicit_null"])
def test_invalid_cases_fail_actionably(mutation):
    before, after = pair()
    raw = dataset()
    first = raw["cases"][0]
    if mutation == "snapshot":
        raw["snapshot_ids"]["before"] = "0" * 64
    elif mutation == "quote":
        first["expectations"]["before"]["evidence"][0]["quote"] = "not in this corpus"
    elif mutation == "missing_document":
        first["expectations"]["before"]["evidence"][0]["document_id"] = "missing"
    elif mutation == "version":
        first["requested_version"] = "2"
    elif mutation == "family_split":
        raw["cases"][1]["family_id"] = first["family_id"]
        raw["cases"][1]["split"] = "held_out"
    elif mutation == "review":
        first["review"]["status"] = "human_reviewed"
    elif mutation == "duplicate_case":
        raw["cases"].append(copy.deepcopy(first))
    elif mutation == "extra_expectation":
        first["expectations"]["invented"] = first["expectations"]["after"]
    elif mutation == "abstain_answer":
        raw["cases"][4]["expectations"]["after"]["answer"] = "Fact asserted despite abstention"
    else:
        first["requested_version"] = None
    with pytest.raises(ValidationError):
        validate_dataset(raw, before, after)


def test_default_required_even_for_abstention_without_evidence():
    before, after = pair()
    raw = dataset()
    missing = raw["cases"][5]
    missing["target"] = "snapshot_default"
    missing["requested_version"] = None
    raw["cases"] = [missing]
    before_manifest = manifest()
    before_manifest["default_version"] = None
    no_default = snapshot(before_manifest)
    raw["snapshot_ids"]["before"] = no_default.snapshot_id
    with pytest.raises(ValidationError, match="default version"):
        validate_dataset(raw, no_default, after)


def test_cli_comparison_is_repeatable(capsys):
    args = ["compare", str(EXAMPLE / "before" / "manifest.json"),
            str(EXAMPLE / "after" / "manifest.json")]
    assert main(args) == 0
    first = capsys.readouterr().out
    assert main(args) == 0
    assert capsys.readouterr().out == first


def test_cli_invalid_input_has_nonzero_exit_and_json_error(capsys):
    assert main(["compare", "does-not-exist.json", "also-missing.json"]) == 2
    assert "error" in json.loads(capsys.readouterr().err)


def test_doctor_default_never_calls_service(monkeypatch):
    monkeypatch.setattr("knowledge_delta.doctor.build_opener",
                        lambda *args: pytest.fail("unexpected network call"))
    report = readiness()
    assert report["ollama"]["status"] == "not_checked"
    assert report["downloads_performed"] is False


def test_missing_service_is_explicit_and_no_fallback(monkeypatch):
    class MissingService:
        def open(self, *args, **kwargs):
            raise OSError("simulated local service unavailable")
    monkeypatch.setattr("knowledge_delta.doctor.build_opener", lambda *args: MissingService())
    report = readiness(check_ollama=True)
    assert report["ollama"]["status"] == "unavailable_or_invalid_response"
    assert report["ollama"]["inference_verified"] is False


def test_json_rejects_duplicate_keys_and_nonstandard_numbers(monkeypatch):
    from io import StringIO
    for body in ('{"a":1,"a":2}', '{"a":NaN}'):
        monkeypatch.setattr(Path, "open", lambda *a, **kw: StringIO(body))
        with pytest.raises(ValidationError):
            read_json(Path("virtual.json"))


def test_checked_in_expected_diff_matches_real_command_logic():
    before, after = pair()
    expected = read_json(EXAMPLE / "expected-diff.json")
    assert compare(before, after) == expected


def test_content_only_diff_does_not_claim_metadata_change():
    before = snapshot()
    after = snapshot(overrides={"config.md": b"A changed fact.\n"})
    changes = compare(before, after)["document_changes"]
    assert len(changes) == 1
    assert changes[0]["document_id"] == "widget.config"
    assert changes[0]["content_changed"] is True
    assert changes[0]["metadata_changed"] is False


@pytest.mark.parametrize("error", [PermissionError("denied"), FileNotFoundError("missing")])
def test_document_read_errors_become_validation_errors(error):
    def unreadable(path):
        raise error
    with pytest.raises(ValidationError, match="cannot read UTF-8 document"):
        parse_snapshot(manifest(), EXAMPLE / "before", unreadable)


@pytest.mark.parametrize("error", [PermissionError("denied"), RuntimeError("symlink loop")])
def test_document_resolution_errors_become_validation_errors(monkeypatch, error):
    def unresolvable(*args):
        raise error
    monkeypatch.setattr("knowledge_delta.snapshots.document_path", unresolvable)
    with pytest.raises(ValidationError, match="cannot resolve document path"):
        snapshot()


def test_snapshot_root_resolution_error_is_actionable(monkeypatch):
    raw = manifest()
    def unresolvable(*args, **kwargs):
        raise RuntimeError("symlink loop")
    monkeypatch.setattr(Path, "resolve", unresolvable)
    with pytest.raises(ValidationError, match="cannot resolve snapshot root"):
        parse_snapshot(raw, EXAMPLE)


def test_lone_surrogate_metadata_is_rejected_actionably():
    raw = manifest()
    raw["documents"][0]["title"] = "\ud800"
    with pytest.raises(ValidationError, match="valid UTF-8 text"):
        snapshot(raw)


def test_case_validation_rejects_cross_domain_pair():
    before, after = pair()
    raw = manifest("after")
    raw["domain"] = "another-product"
    different_domain = snapshot(raw, slot="after")
    cases = dataset()
    cases["snapshot_ids"]["after"] = different_domain.snapshot_id
    with pytest.raises(ValidationError, match="same software domain"):
        validate_dataset(cases, before, different_domain)


@pytest.mark.parametrize("models, expected", [
    ([], "model_missing"),
    ([{"name": "qwen3:1.7b", "digest": "test-digest"}], "model_available"),
])
def test_readiness_model_inventory_is_not_inference(monkeypatch, models, expected):
    from io import StringIO
    class LocalInventory:
        def open(self, url, timeout):
            assert url == "http://127.0.0.1:11434/api/tags"
            assert timeout == 3
            return StringIO(json.dumps({"models": models}))
    monkeypatch.setattr("knowledge_delta.doctor.build_opener", lambda *args: LocalInventory())
    result = readiness(check_ollama=True)["ollama"]
    assert result["status"] == expected
    assert result["inference_verified"] is False
    if models:
        assert result["digest"] == "test-digest"


def test_inaccessible_disk_is_unknown_without_crashing(monkeypatch):
    def denied(path):
        raise PermissionError("simulated inaccessible volume")
    monkeypatch.setattr("knowledge_delta.doctor.shutil.disk_usage", denied)
    result = readiness()
    assert result["hardware"]["free_disk_bytes"] is None
    assert "inaccessible volume" in result["disk_error"]
