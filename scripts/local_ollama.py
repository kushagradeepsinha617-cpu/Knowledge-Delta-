"""Print a read-only Ollama launch plan, or explicitly start the reviewed local binary."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.ollama_runtime import runtime_plan, start_runtime
from knowledge_delta.validation import ValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--start", action="store_true", help="Explicit native execution; never downloads assets")
    parser.add_argument("--expected-sha256", help="Reviewed executable hash, required with --start")
    args = parser.parse_args(argv)
    try:
        if args.start:
            return start_runtime(ROOT, args.runtime, args.expected_sha256)
        plan = runtime_plan(ROOT, args.runtime)
        print(json.dumps(plan, indent=2))
        return 0 if plan["status"] == "ready_for_explicit_start" else 2
    except (ValidationError, OSError) as exc:
        print(json.dumps({"status": "run_error", "error": str(exc), "downloads_performed": False,
                          "native_execution_performed": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
