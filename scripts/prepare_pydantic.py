"""Offline, reproducible assembly of the first Pydantic development batch.

No network, inference or human review is performed. --write creates missing
artifacts only; differing existing files are never overwritten.
"""
import argparse
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.cases import validate_dataset
from knowledge_delta.diff import compare
from knowledge_delta.evaluation import validate_relations
from knowledge_delta.snapshots import parse_snapshot
from knowledge_delta.validation import ValidationError, read_json, digest

SOURCE_PINS = {
    "v1-models.md": ("93a04c0e93631d0e7be8910014a3176b07502b4852e5ba606ffa693d7c2a6c21", "0cbba0f9774c470e8d8a2a62abb921b8cea4027d", "docs/usage/models.md"),
    "LICENSE-v1.txt": ("9e3946690ac88b6b73e8f001a0586af13568be8852fd514e4393f39761764387", "0cbba0f9774c470e8d8a2a62abb921b8cea4027d", "LICENSE"),
    "v2-migration.md": ("9e51980256231ceb88bf3d4a87a6e7b1513e636b165744f7a566c88734e9c9a0", "df05e69a8a3fb37628a0e3a33518ca0425334bc9", "docs/migration.md"),
    "LICENSE-v2.txt": ("a9e186f3ca16b5eef84318e7a701721351a00cb7b8ae3a4394b67b49e3529ef3", "df05e69a8a3fb37628a0e3a33518ca0425334bc9", "LICENSE"),
}

DRAFT = {"status": "draft", "reviewer": None, "scope": None}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def verify_sources(base):
    inventory = read_json(base / "sources.json")
    if (len(inventory["sources"]) != len(SOURCE_PINS)
            or {item["file"] for item in inventory["sources"]} != set(SOURCE_PINS)):
        raise ValidationError("Source inventory differs from the pinned file set")
    for entry in inventory["sources"]:
        expected_hash, revision, upstream_path = SOURCE_PINS[entry["file"]]
        if (entry["sha256"], entry["revision"], entry["path"], entry["license"], entry["url"]) != (
                expected_hash, revision, upstream_path, "MIT",
                "https://github.com/pydantic/pydantic/blob/" + revision + "/" + upstream_path):
            raise ValidationError("Source inventory differs from the verified upstream pin")
        data = (base / "sources" / entry["file"]).read_bytes()
        blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        if (len(data) != entry["bytes"] or sha256(data).hexdigest() != entry["sha256"]
                or sha1(blob).hexdigest() != entry["git_blob_sha1"]):
            raise ValidationError("Pinned source changed: " + entry["file"])
    return {entry["file"]: entry for entry in inventory["sources"]}


def extract(source, start, end=None):
    if source.count(start) != 1:
        raise ValidationError("Excerpt start must occur exactly once: " + start)
    offset = source.index(start)
    if end:
        boundary = source.find(end, offset + len(start))
        if boundary < 0:
            raise ValidationError("Excerpt end not found: " + end)
    else:
        following = re.search(r"^#{1,4} ", source[offset + len(start):], re.MULTILINE)
        boundary = (offset + len(start) + following.start()) if following else len(source)
    return source[offset:boundary].rstrip() + "\n"


def draft_relations(dataset):
    return {"schema_version": 1, "dataset_hash": digest(dataset), "relations": [
        {"schema_version": 1, "case_id": case["case_id"], "case_hash": digest(case),
         "relation": "should_remain", "basis": "draft", "reviewer": None,
         "reviewed_at": None,
         "rationale": "Draft expectation: adding v1 documentation does not change the explicit v2 target."}
        for case in dataset["cases"]]}


def build_artifacts(base):
    sources = verify_sources(base)
    migration = (base / "sources/v2-migration.md").read_text(encoding="utf-8")
    recipes = read_json(base / "recipe.json")
    if len({item["id"] for item in recipes}) != len(recipes):
        raise ValidationError("Duplicate case family")
    artifacts, documents, cases = {}, [], []
    for item in recipes:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", item["id"]):
            raise ValidationError("Unsafe case/excerpt identity")
        content = extract(migration, item["start"], item["end"])
        if item["quote"] not in content:
            raise ValidationError("Supporting quote outside excerpt: " + item["id"])
        identity, filename = "pydantic.v2." + item["id"], item["id"] + ".md"
        for slot in ("before", "after"):
            artifacts[slot + "/" + filename] = content.encode("utf-8")
        documents.append({"document_id": identity, "path": filename,
                          "source_reference": sources["v2-migration.md"]["url"],
                          "source_revision": sources["v2-migration.md"]["revision"],
                          "software_versions": ["2.10.6"], "title": item["title"]})
        expectation = {"behavior": "answer", "answer": item["answer"], "rubric": item["rubric"],
                       "target_context": None,
                       "evidence": [{"document_id": identity, "quote": item["quote"]}]}
        cases.append({"case_id": "pydantic-" + item["id"], "family_id": "pydantic-" + item["id"],
                      "question": item["question"], "target": "explicit_version",
                      "requested_version": "2.10.6", "expectations": {
                          "before": expectation, "after": dict(expectation)},
                      "category": "other_version_added", "provenance": "constructed",
                      "split": "development", "review": dict(DRAFT)})
    manifests, snapshots = {}, {}
    for slot in ("before", "after"):
        selected = list(documents)
        if slot == "after":
            artifacts["after/v1-models.md"] = (base / "sources/v1-models.md").read_bytes()
            selected.append({"document_id": "pydantic.v1.models", "path": "v1-models.md",
                             "source_reference": sources["v1-models.md"]["url"],
                             "source_revision": sources["v1-models.md"]["revision"],
                             "software_versions": ["1.10.21"], "title": "Pydantic v1 models"})
        manifest = {"schema_version": 1, "name": "pydantic-distractors-" + slot,
                    "domain": "pydantic", "default_version": "2.10.6",
                    "provenance": "constructed", "documents": selected}
        manifests[slot] = manifest
        snapshots[slot] = parse_snapshot(manifest, base / slot,
            read_bytes=lambda p, slot=slot: artifacts[slot + "/" + p.name])
        artifacts[slot + "/manifest.json"] = encoded(manifest)
    dataset = {"schema_version": 1,
               "snapshot_ids": {slot: snapshot.snapshot_id for slot, snapshot in snapshots.items()},
               "cases": cases}
    validate_dataset(dataset, snapshots["before"], snapshots["after"])
    artifacts["cases.json"] = encoded(dataset)
    artifacts["relations.json"] = encoded(draft_relations(dataset))
    return artifacts, snapshots, dataset


def verify_bundle(base, write=False):
    artifacts, snapshots, expected = build_artifacts(base)
    # Preflight every destination before creating anything. Human reviews survive.
    for relative, data in artifacts.items():
        path = base / relative
        if not path.resolve().is_relative_to(base.resolve()) or path.is_symlink():
            raise ValidationError("Unsafe artifact destination: " + relative)
        if path.is_file():
            if relative == "cases.json":
                actual = read_json(path)
                validate_dataset(actual, snapshots["before"], snapshots["after"])
                normalized = json.loads(json.dumps(actual))
                for case in normalized["cases"]:
                    case["review"] = dict(DRAFT)
                if normalized != expected:
                    raise ValidationError("Case definitions differ from pinned recipe")
            elif relative == "relations.json":
                validate_relations(read_json(path), read_json(base / "cases.json"))
            elif path.read_bytes() != data:
                raise ValidationError("Existing artifact differs; preserved: " + relative)
        elif not write:
            raise ValidationError("Missing artifact: " + relative + "; use --write explicitly")
    if write:
        for relative, data in artifacts.items():
            path = base / relative
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(data)
    actual = read_json(base / "cases.json")
    summary = validate_dataset(actual, snapshots["before"], snapshots["after"])
    return {"status": "verified", "kind": "constructed_pydantic_corpus_assembly",
            "source_material": "genuine pinned MIT documentation",
            "dataset": summary, "changes": compare(snapshots["before"], snapshots["after"]),
            "downloads_performed": False, "generation_performed": False,
            "human_reviews_created": False, "artifact_count": len(artifacts)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Create missing project artifacts only")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_bundle(ROOT / "examples/pydantic", args.write), indent=2))
        return 0
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
