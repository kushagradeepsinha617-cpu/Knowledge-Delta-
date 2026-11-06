"""Build/verify a draft 20-development/40-held-out study, without model calls.

Existing reviews and runs are preserved. Preparing cases never approves them.
"""
import argparse
from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.cases import validate_dataset
from knowledge_delta.evaluation import validate_relations
from knowledge_delta.snapshots import parse_snapshot, load_snapshot
from knowledge_delta.validation import ValidationError, read_json, digest
from scripts.prepare_pydantic import DRAFT, encoded, extract, verify_sources

BASE = ROOT / "examples/pydantic-evaluation"
REVISION = "df05e69a8a3fb37628a0e3a33518ca0425334bc9"
CONDITIONS = ("other_version_added", "evidence_removed", "wording_only", "unrelated_change")


def source_inventory(root):
    base = root / "examples/pydantic-evaluation"
    inventory = read_json(base / "sources.json")
    if inventory["revision"] != REVISION:
        raise ValidationError("Study documentation revision changed")
    for entry in inventory["sources"]:
        body = (base / "sources" / entry["file"]).read_bytes()
        expected_url = f"https://github.com/pydantic/pydantic/blob/{REVISION}/docs/concepts/{entry['file']}"
        if (entry["revision"] != REVISION or entry["url"] != expected_url or entry["license"] != "MIT"
                or len(body) != entry["bytes"] or sha256(body).hexdigest() != entry["sha256"]
                or sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest() != entry["git_blob_sha1"]):
            raise ValidationError("Study source identity differs: " + entry["file"])
    verify_sources(root / "examples/pydantic")
    return {entry["file"]: entry for entry in inventory["sources"]}


def safe_slug(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", value):
        raise ValidationError("Invalid recipe identity")
    return value


def assemble_bundle(root, name, recipes, split, condition, inventory):
    """Build a single controlled pair, deduplicating overlapping case excerpts."""
    artifacts, documents, contents, cases = {}, {}, {}, []
    for recipe in recipes:
        safe_slug(recipe["id"])
        safe_slug(recipe["family_id"])
        filename = recipe["file"]
        if filename == "v2-migration.md":
            source = root / "examples/pydantic/sources" / filename
            reference = f"https://github.com/pydantic/pydantic/blob/{REVISION}/docs/migration.md"
        else:
            if filename not in inventory:
                raise ValidationError("Unverified recipe source")
            source = root / "examples/pydantic-evaluation/sources" / filename
            reference = inventory[filename]["url"]
        content = extract(source.read_text(encoding="utf-8"), recipe["start"], recipe.get("end"))
        if recipe["quote"] not in content:
            raise ValidationError("Supporting quote outside selected source: " + recipe["id"])
        # Stable source-section identity is independent of content, case and snapshot.
        identity = "pydantic.study." + digest([filename, recipe["start"]])[:16]
        path = identity + ".md"
        metadata = {"document_id": identity, "path": path, "source_reference": reference,
                    "source_revision": REVISION, "software_versions": ["2.10.6"],
                    "title": recipe["start"].lstrip("# ")}
        if identity in contents and contents[identity] != content:
            raise ValidationError("Conflicting excerpt boundaries for one source section")
        documents[identity], contents[identity] = metadata, content
        expectation = {"behavior": "answer", "answer": recipe["answer"], "rubric": recipe["rubric"],
                       "target_context": None, "evidence": [{"document_id": identity, "quote": recipe["quote"]}]}
        after = deepcopy(expectation)
        if condition == "evidence_removed":
            after = {"behavior": "abstain", "answer": None, "target_context": None, "evidence": [],
                     "rubric": "Under the evidence-only policy, say the supplied snapshot lacks applicable supporting evidence. Do not assert the underlying fact became false or that the software behavior changed."}
        cases.append({"case_id": "study-" + recipe["id"], "family_id": recipe["family_id"],
                      "question": recipe["question"], "target": "explicit_version", "requested_version": "2.10.6",
                      "expectations": {"before": expectation, "after": after}, "category": condition,
                      "provenance": "constructed", "split": split, "review": dict(DRAFT)})
    snapshots = {}
    for slot in ("before", "after"):
        selected = [] if slot == "after" and condition == "evidence_removed" else list(documents.values())
        selected = deepcopy(selected)
        for metadata in selected:
            content = contents[metadata["document_id"]]
            if slot == "after" and condition == "wording_only":
                # A constructed whitespace-only edit; no factual text is changed.
                content = "\n\n" + content + "\n"
            artifacts[f"{slot}/{metadata['path']}"] = content.encode("utf-8")
        if slot == "after" and condition == "other_version_added":
            original = read_json(root / "examples/pydantic/after/manifest.json")
            distractor = deepcopy(next(d for d in original["documents"] if d["document_id"] == "pydantic.v1.models"))
            selected.append(distractor)
            artifacts[f"{slot}/{distractor['path']}"] = (root / "examples/pydantic/after" / distractor["path"]).read_bytes()
        if condition == "unrelated_change":
            selected.append({"document_id": "pydantic.study.control-note", "path": "control-note.md",
                             "source_reference": "constructed:study-control", "source_revision": "fixture-v1",
                             "software_versions": [], "title": "Constructed unrelated control note"})
            artifacts[f"{slot}/control-note.md"] = ("Constructed control note. Batch label: " + ("alpha" if slot == "before" else "beta") + ". This note specifies no Pydantic API behavior.\n").encode()
        manifest = {"schema_version": 1, "name": name + "-" + slot, "domain": "pydantic",
                    "default_version": "2.10.6", "provenance": "constructed", "documents": selected}
        snapshots[slot] = parse_snapshot(manifest, root / "examples/pydantic-evaluation" / name / slot,
            lambda path, slot=slot: artifacts[f"{slot}/{path.name}"])
        artifacts[f"{slot}/manifest.json"] = encoded(manifest)
    dataset = {"schema_version": 1, "snapshot_ids": {s: v.snapshot_id for s, v in snapshots.items()}, "cases": cases}
    validate_dataset(dataset, snapshots["before"], snapshots["after"])
    relations = {"schema_version": 1, "dataset_hash": digest(dataset), "relations": [
        {"schema_version": 1, "case_id": c["case_id"], "case_hash": digest(c),
         "relation": "should_change" if condition == "evidence_removed" else "should_remain", "basis": "draft",
         "reviewer": None, "reviewed_at": None,
         "rationale": "Draft evidence-only expectation for explicitly constructed " + condition + " condition."} for c in cases]}
    artifacts["cases.json"], artifacts["relations.json"] = encoded(dataset), encoded(relations)
    return artifacts, dataset


def prepare(root, *, write=False):
    base = root / "examples/pydantic-evaluation"
    if not base.resolve().is_relative_to(root.resolve()):
        raise ValidationError("Study base must remain inside the project")
    inventory = source_inventory(root)
    development = read_json(base / "development-recipes.json")["cases"]
    heldout = read_json(base / "heldout-recipes.json")["cases"]
    if len(development) != 9 or len(heldout) != 40:
        raise ValidationError("Need nine new development and forty distinct held-out cases")
    all_recipes = development + heldout
    if len({r["id"] for r in all_recipes}) != 49 or len({r["question"] for r in all_recipes}) != 49:
        raise ValidationError("Duplicate case ID/question cannot pad study counts")
    old = read_json(root / "examples/pydantic/cases.json")["cases"]
    dev_families = {r["family_id"] for r in development} | {c["family_id"] for c in old}
    dev_families.add("pydantic-generic-upper-bound")
    if dev_families & {r["family_id"] for r in heldout}:
        raise ValidationError("Related families cannot cross the development/test boundary")
    families = sorted({r["family_id"] for r in heldout})
    assignment = {family: CONDITIONS[i % len(CONDITIONS)] for i, family in enumerate(families)}
    bundles = [("development-extension", development, "development", "other_version_added")]
    for condition in CONDITIONS:
        subset = [r for r in heldout if assignment[r["family_id"]] == condition]
        if subset:
            bundles.append(("heldout-" + condition.replace("_", "-"), subset, "held_out", condition))
    study = {"schema_version": 1, "kind": "evaluation_study_plan", "status": "draft_requires_human_review",
             "target": {"development": 20, "held_out": 40}, "family_assignment": assignment,
             "existing_development": ["examples/pydantic", "examples/pydantic-revision"], "new_bundles": []}
    artifacts = {}
    for name, recipes, split, condition in bundles:
        files, dataset = assemble_bundle(root, name, recipes, split, condition, inventory)
        study["new_bundles"].append({"path": "examples/pydantic-evaluation/" + name,
                                     "split": split, "condition": condition, "case_count": len(dataset["cases"])})
        artifacts.update({name + "/" + path: body for path, body in files.items()})
    artifacts["study-plan.json"] = encoded(study)
    # Check every existing destination before writing anything. Reviewed definitions survive.
    for relative, body in artifacts.items():
        path = base / relative
        if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
            raise ValidationError("Unsafe study artifact path")
        if path.exists():
            if relative.endswith("/cases.json"):
                actual = read_json(path)
                normalized = deepcopy(actual)
                for case in normalized["cases"]:
                    case["review"] = dict(DRAFT)
                if normalized != json.loads(body):
                    raise ValidationError("Existing study case definitions differ; preserve reviews")
            elif relative.endswith("/relations.json"):
                validate_relations(read_json(path), read_json(path.with_name("cases.json")))
            elif path.read_bytes() != body:
                raise ValidationError("Existing study artifact differs: " + relative)
        elif not write:
            raise ValidationError("Missing study artifact; explicitly prepare it: " + relative)
    if write:
        for relative, body in artifacts.items():
            path = base / relative
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(body)
    return study


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = prepare(ROOT, write=args.write)
        print(json.dumps(result, indent=2))
        return 0
    except (ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "human_reviews_created": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
