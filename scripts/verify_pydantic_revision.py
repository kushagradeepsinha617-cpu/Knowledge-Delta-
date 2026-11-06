"""Verify the selected genuine documentation revision offline; no semantic grading."""
import json
from hashlib import sha1, sha256
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.cases import validate_dataset
from knowledge_delta.diff import compare
from knowledge_delta.evaluation import validate_relations
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json
from scripts.prepare_pydantic import extract

BEFORE = "55dd8daeb6091b9317b92836765f3f1396b3e9ba"
AFTER = "6f7691b5c1e1838aedf88414a41cd6a9a0caf1d6"
PINS = {"models-before.md": "3dcc86e21711463e61996e843ca68521212e5259d28b2a4bd12a4b01d0ed8ddb",
        "models-after.md": "5a2de50788647934cb8083818542e049c9dfb463ba01f7674054a43c96aa7e7f",
        "version.txt": "31c73cab93c262beda71ccd635a06c5ea5fad7ced8808071e8661ff85c8ca97b",
        "LICENSE.txt": "a9e186f3ca16b5eef84318e7a701721351a00cb7b8ae3a4394b67b49e3529ef3"}


def verify(base):
    inventory = read_json(base / "sources.json")
    if (inventory["before_revision"] != BEFORE or inventory["after_revision"] != AFTER
            or inventory["upstream_change"]["changed_paths"] != ["docs/concepts/models.md"]):
        raise ValidationError("Upstream revision identity differs")
    for name, expected in PINS.items():
        data = (base / "sources" / name).read_bytes()
        if sha256(data).hexdigest() != expected:
            raise ValidationError("Pinned source changed: " + name)
        entries = [e for e in inventory["sources"] if e["file"] == name]
        path = "docs/concepts/models.md" if name.startswith("models-") else ("LICENSE" if name == "LICENSE.txt" else "pydantic/version.py")
        revisions = [BEFORE] if name == "models-before.md" else ([AFTER] if name == "models-after.md" else [BEFORE, AFTER])
        blob = sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if (len(entries) != 1 or entries[0]["sha256"] != expected or entries[0]["bytes"] != len(data)
                or entries[0]["git_blob_sha1"] != blob or entries[0]["path"] != path
                or entries[0]["revisions"] != revisions or entries[0]["license"] != "MIT"):
            raise ValidationError("Source provenance inventory differs: " + name)
    if len(inventory["sources"]) != len(PINS):
        raise ValidationError("Unexpected source inventory entry")
    texts = {slot: (base / "sources" / ("models-" + slot + ".md")).read_text(encoding="utf-8")
             for slot in ("before", "after")}
    start = texts["after"].index("\n!!! warning\n    When parametrizing a model")
    end = texts["after"].index("\nAny [configuration]", start)
    if texts["after"][:start] + texts["after"][end:] != texts["before"]:
        raise ValidationError("Source revision differs beyond the pinned warning addition")
    snapshots = {}
    for slot, revision in (("before", BEFORE), ("after", AFTER)):
        expected = extract(texts[slot], "## Generic models", "\n## Dynamic model creation").encode("utf-8")
        if (base / slot / "generic-models.md").read_bytes() != expected:
            raise ValidationError("Selected section differs from pinned source: " + slot)
        snap = snapshots[slot] = load_snapshot(base / slot / "manifest.json")
        if (snap.provenance != "genuine" or snap.default_version is not None or len(snap.documents) != 1
                or snap.documents[0].document_id != "pydantic.generic-models"
                or snap.documents[0].source_revision != revision
                or snap.documents[0].source_reference != "https://github.com/pydantic/pydantic/blob/" + revision + "/docs/concepts/models.md"
                or snap.documents[0].software_versions != ()):
            raise ValidationError("Snapshot source/version applicability differs")
    dataset = read_json(base / "cases.json")
    summary = validate_dataset(dataset, snapshots["before"], snapshots["after"])
    if (len(dataset["cases"]) != 1 or dataset["cases"][0]["provenance"] != "genuine"
            or dataset["cases"][0]["category"] != "missing_evidence"
            or dataset["cases"][0]["requested_version"] is not None
            or dataset["cases"][0]["target"] != "unspecified"
            or dataset["cases"][0]["split"] != "development"):
        raise ValidationError("Keep genuine clarification scope and unknown release applicability visible")
    if inventory["version_scope"]["release_applicability_verified"] is not False:
        raise ValidationError("Released software applicability has not been verified")
    validate_relations(read_json(base / "relations.json"), dataset)
    return {"status": "verified_source_and_schema", "dataset": summary,
            "changes": compare(snapshots["before"], snapshots["after"]),
            "semantic_expectations_verified": False, "software_behavior_change_claimed": False,
            "nominal_source_version": "2.10.5", "release_applicability_verified": False,
            "downloads_performed": False, "generation_performed": False}


if __name__ == "__main__":
    try:
        print(json.dumps(verify(ROOT / "examples/pydantic-revision"), indent=2))
    except (ValidationError, OSError, KeyError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        raise SystemExit(2)
