"""JSON-to-stdout commands. No writes, downloads, or model inference."""
import argparse
import json
import sys
from pathlib import Path

from .cases import validate_dataset
from .diff import compare
from .doctor import readiness
from .snapshots import load_snapshot
from .validation import ValidationError, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(prog="knowledge-delta")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("compare", "validate-cases"):
        command = commands.add_parser(name)
        command.add_argument("before", type=Path)
        command.add_argument("after", type=Path)
        if name == "validate-cases":
            command.add_argument("dataset", type=Path)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--check-ollama", action="store_true",
                        help="Explicit read-only request to local /api/tags; never generates")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = readiness(args.check_ollama)
        else:
            before, after = load_snapshot(args.before), load_snapshot(args.after)
            result = compare(before, after) if args.command == "compare" else validate_dataset(
                read_json(args.dataset), before, after)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except ValidationError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
