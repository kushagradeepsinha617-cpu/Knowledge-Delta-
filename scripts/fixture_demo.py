"""Export an explicitly simulated fixture report. No models, services or downloads."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.workflow import export_report, fixture_report
from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, default=ROOT / "examples/mvp/before/manifest.json")
    parser.add_argument("--after", type=Path, default=ROOT / "examples/mvp/after/manifest.json")
    parser.add_argument("--dataset", type=Path, default=ROOT / "examples/mvp/cases.json")
    parser.add_argument("--relations", type=Path, default=ROOT / "examples/mvp/relations.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "runs/fixture-demo")
    parser.add_argument("--simulate-judgments", action="store_true",
                        help="Include clearly labeled simulated correctness judgments; never human reviews")
    parser.add_argument("--include-manual-reviews", action="store_true",
                        help="Load current human inspections from the local review journal; retain fixture provenance")
    args = parser.parse_args(argv)
    try:
        if args.include_manual_reviews:
            evaluation = ReviewSession(ROOT, before=args.before, after=args.after, dataset=args.dataset,
                relations=args.relations, simulate_judgments=args.simulate_judgments).evaluate()
        else:
            evaluation = fixture_report(args.before, args.after, args.dataset, args.relations,
                                         simulate_judgments=args.simulate_judgments)
        files = export_report(ROOT, args.output_dir, evaluation)
        print(json.dumps({"mode": "SIMULATED FIXTURE", "files": files, "counts": evaluation["counts"],
                          "live_inference_performed": False}, indent=2))
        return 0
    except (ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "live_inference_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
