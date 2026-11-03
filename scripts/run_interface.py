"""Print UI readiness, or explicitly serve the local fixture interface; never downloads."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.interface_runtime import interface_plan, start_interface
from knowledge_delta.validation import ValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="Explicitly start the already installed local Streamlit package")
    args = parser.parse_args(argv)
    try:
        if args.serve:
            return start_interface(ROOT)
        plan = interface_plan(ROOT)
        print(json.dumps(plan, indent=2))
        return 0 if plan["status"] == "ready_for_explicit_start" else 2
    except (ValidationError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "downloads_performed": False, "ui_launched": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
