"""Record the actual project-owner blanket authorization; never creates human reviews."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluation_study import inventory, approval_coverage
from knowledge_delta.validation import digest

AUTHORIZATION = "complte milestone 5. you are free to acses google chrome, do whatever you want with github and i aprove of all the cases dont ask me for me to approve them assume i have already aporved them. ofc gving you accses to gothub and chrome is only for project related tasks."


def record(root):
    entries, counts, _ = inventory(root)
    records = []
    for entry in entries:
        relations = {r["case_id"]: r for r in entry["relations"]["relations"]}
        for case in entry["dataset"]["cases"]:
            records.append({"case_id": case["case_id"], "case_hash": digest(case),
                "relation_hash": digest(relations.get(case["case_id"])), "dataset_hash": digest(entry["dataset"]),
                "snapshot_ids": entry["dataset"]["snapshot_ids"]})
    ledger = {"schema_version": 1, "kind": "user_blanket_case_approval",
        "recorded_at": datetime.now(timezone.utc).isoformat(), "authorization_source": "Explicit project-owner goal instruction",
        "authorization_text": AUTHORIZATION, "approval_scope": "case definitions and expected relations",
        "item_by_item_human_review_verified": False, "preserved_review_counts": counts,
        "agent_source_check": "Pinned sources and exact quote/extraction boundaries verified; AI-assisted recipe/rubric review. Not independent human ground truth or actual-answer grading.",
        "records": records}
    path = root / "examples/pydantic-evaluation/user-approval.json"
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Approval ledger must remain project-local")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(ledger, stream, indent=2)
        stream.write("\n")
    return {"user_approved": approval_coverage(root, entries), "human_review_counts_unchanged": counts,
            "item_by_item_human_reviews_created": 0}


if __name__ == "__main__":
    print(json.dumps(record(ROOT), indent=2))
