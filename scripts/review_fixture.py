"""Inspect a fixture review binding or explicitly save your human review; never runs a model."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--kind", choices=("answer", "relation"), default="answer")
    parser.add_argument("--configuration", choices=("basic", "version_filtered"), default="basic")
    parser.add_argument("--slot", choices=("before", "after"), default="after")
    parser.add_argument("--save", action="store_true", help="Explicit human-review action; otherwise inspect only")
    parser.add_argument("--expected-binding")
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--outcome", choices=("pass", "fail", "needs_human_review"))
    parser.add_argument("--failure-kind")
    parser.add_argument("--relation", choices=("should_change", "should_remain", "undetermined"))
    parser.add_argument("--reviewer")
    parser.add_argument("--rationale")
    args = parser.parse_args(argv)
    try:
        session = ReviewSession(ROOT)
        info = session.answer_info(args.case_id, args.configuration, args.slot) if args.kind == "answer" else session.relation_info(args.case_id)
        if not args.save:
            print(json.dumps({"mode": "FIXTURE REVIEW INSPECTION", "subject": info["subject"],
                "binding_hash": info["binding_hash"], "revision": info["revision"],
                "question": info["case"]["question"], "expectations": info["case"]["expectations"],
                "trace": info.get("trace"), "stored_review": info["stored_review"], "writes_performed": False}, indent=2))
            return 0
        if args.expected_binding is None or args.expected_revision is None:
            raise ValidationError("Inspect first; saving requires its displayed binding hash and revision")
        common = {"reviewer": args.reviewer, "rationale": args.rationale,
                  "expected_binding_hash": args.expected_binding, "expected_revision": args.expected_revision}
        if args.kind == "answer":
            revision = session.save_answer(args.case_id, args.configuration, args.slot,
                outcome=args.outcome, failure_kind=args.failure_kind, **common)
        else:
            revision = session.save_relation(args.case_id, relation=args.relation, **common)
        print(json.dumps({"status": "saved", "revision": revision, "origin": "fixture",
                          "notice": "You reviewed a scripted fixture; no live inference or case-label review is implied."}))
        return 0
    except (ValidationError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "live_inference_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
