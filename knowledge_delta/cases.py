"""Validate answer keys separately from source documents.

No evaluator or answering model exists in Milestone 1. A valid rubric is not
a correctness judgment, and a valid dataset is not a human-reviewed dataset.
"""
from .validation import (ValidationError, choice, fields, nullable_text,
                         schema_version, sequence, text)

CATEGORIES = ("behavior_change", "wording_only", "unrelated_change",
              "other_version_added", "evidence_removed", "conflicting_sources",
              "missing_evidence")


def validate_dataset(raw, before, after):
    fields(raw, ("schema_version", "snapshot_ids", "cases"), "dataset")
    schema_version(raw["schema_version"], "dataset")
    fields(raw["snapshot_ids"], ("before", "after"), "dataset.snapshot_ids")
    snapshots = {"before": before, "after": after}
    for slot, snapshot in snapshots.items():
        if raw["snapshot_ids"][slot] != snapshot.snapshot_id:
            raise ValidationError(f"dataset.{slot}: snapshot ID does not match loaded content")
    cases = sequence(raw["cases"], "dataset.cases")
    if not cases:
        raise ValidationError("dataset.cases: at least one case is required")
    ids, family_splits = set(), {}
    reviewed = 0
    for case in cases:
        fields(case, ("case_id", "family_id", "question", "target", "requested_version",
                      "expectations", "category", "provenance", "split", "review"), "case")
        identity = text(case["case_id"], "case.case_id")
        if identity in ids:
            raise ValidationError(f"duplicate case ID: {identity}")
        ids.add(identity)
        family = text(case["family_id"], f"{identity}.family_id")
        text(case["question"], f"{identity}.question")
        split = choice(case["split"], ("development", "held_out"), f"{identity}.split")
        if family in family_splits and family_splits[family] != split:
            raise ValidationError(f"family {family} crosses development and held-out splits")
        family_splits[family] = split
        choice(case["category"], CATEGORIES, f"{identity}.category")
        choice(case["provenance"], ("constructed", "genuine"), f"{identity}.provenance")
        target = choice(case["target"], ("explicit_version", "snapshot_default", "unspecified"),
                        f"{identity}.target")
        version = nullable_text(case["requested_version"], f"{identity}.requested_version")
        if (target == "explicit_version") != (version is not None):
            raise ValidationError(f"{identity}: explicit_version requires a fixed requested_version; other targets require null")
        review = case["review"]
        fields(review, ("status", "reviewer", "scope"), f"{identity}.review")
        status = choice(review["status"], ("draft", "human_reviewed"), f"{identity}.review.status")
        nullable_text(review["reviewer"], f"{identity}.review.reviewer")
        nullable_text(review["scope"], f"{identity}.review.scope")
        if status == "human_reviewed":
            text(review["reviewer"], f"{identity}.review.reviewer")
            text(review["scope"], f"{identity}.review.scope")
            reviewed += 1
        fields(case["expectations"], ("before", "after"), f"{identity}.expectations")
        for slot, snapshot in snapshots.items():
            expectation = case["expectations"][slot]
            fields(expectation, ("behavior", "answer", "rubric", "target_context", "evidence"),
                   f"{identity}.{slot}")
            behavior = choice(expectation["behavior"], ("answer", "abstain", "conflict"),
                              f"{identity}.{slot}.behavior")
            answer = nullable_text(expectation["answer"], f"{identity}.{slot}.answer")
            if behavior == "answer" and answer is None:
                raise ValidationError(f"{identity}.{slot}: expected answer required")
            if behavior == "abstain" and answer is not None:
                raise ValidationError(f"{identity}.{slot}: abstention must not contain an expected factual answer")
            text(expectation["rubric"], f"{identity}.{slot}.rubric")
            nullable_text(expectation["target_context"], f"{identity}.{slot}.target_context")
            if target == "snapshot_default" and snapshot.default_version is None:
                raise ValidationError(f"{identity}.{slot}: no declared snapshot default version")
            evidence = sequence(expectation["evidence"], f"{identity}.{slot}.evidence")
            if behavior in ("answer", "conflict") and not evidence:
                raise ValidationError(f"{identity}.{slot}: supporting evidence required")
            applicable = version if target == "explicit_version" else (
                snapshot.default_version if target == "snapshot_default" else None)
            for reference in evidence:
                fields(reference, ("document_id", "quote"), f"{identity}.{slot}.evidence item")
                doc = snapshot.document(text(reference["document_id"], "evidence.document_id"))
                quote = text(reference["quote"], "evidence.quote")
                if quote not in doc.content:
                    raise ValidationError(f"{identity}.{slot}: supporting quote not found in {doc.document_id}")
                if applicable is not None and applicable not in doc.software_versions:
                    raise ValidationError(f"{identity}.{slot}: evidence version missing or incompatible")
    return {"case_count": len(cases), "human_reviewed": reviewed,
            "draft": len(cases) - reviewed, "snapshot_ids": dict(raw["snapshot_ids"]),
            "note": "Schema validation only; no answer correctness has been evaluated."}
