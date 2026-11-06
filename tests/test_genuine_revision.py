"""Pinned revision integrity; no human labels or live inference are invented."""
import json
from pathlib import Path
import shutil

import pytest

from scripts.verify_pydantic_revision import verify
from knowledge_delta.validation import ValidationError

SOURCE = Path(__file__).resolve().parents[1] / "examples/pydantic-revision"


def test_genuine_revision_has_stable_document_identity_and_only_draft_labels():
    result = verify(SOURCE)
    assert result["dataset"]["draft"] == 1
    assert result["dataset"]["human_reviewed"] == 0
    assert result["semantic_expectations_verified"] is False
    assert result["software_behavior_change_claimed"] is False
    assert result["nominal_source_version"] == "2.10.5"
    assert result["release_applicability_verified"] is False
    change, = result["changes"]["document_changes"]
    assert change["document_id"] == "pydantic.generic-models"
    assert change["kind"] == "modified"
    assert change["content_changed"] and change["metadata_changed"]


@pytest.mark.parametrize("tamper", ["source", "excerpt", "inventory", "version"])
def test_revision_evidence_tampering_is_detected(tmp_path, tamper):
    base = tmp_path / "revision"
    shutil.copytree(SOURCE, base)
    if tamper in ("source", "excerpt"):
        path = base / ("sources/models-before.md" if tamper == "source" else "before/generic-models.md")
        path.write_bytes(path.read_bytes() + b"changed")
    else:
        path = base / ("sources.json" if tamper == "inventory" else "before/manifest.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        if tamper == "inventory": data["sources"][0]["revisions"] = ["wrong"]
        else: data["documents"][0]["software_versions"] = ["2.10.6"]
        path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        verify(base)
