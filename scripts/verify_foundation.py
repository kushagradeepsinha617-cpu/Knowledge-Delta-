"""Run the real foundation CLI and check its sample output. No downloads.

Run from any directory with the project environment's Python. JSON is emitted
to stdout; save it explicitly if you want a verification artifact.
"""
import json
import os
from pathlib import Path
import subprocess
import sys


def verify():
    root = Path(__file__).resolve().parents[1]
    before = "examples/constructed/before/manifest.json"
    after = "examples/constructed/after/manifest.json"
    dataset = "examples/constructed/cases.json"
    commands = [
        ["compare", before, after],
        ["validate-cases", before, after, dataset],
        ["doctor"],
        ["compare", "does-not-exist.json", "also-missing.json"],
    ]
    records = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    for arguments in commands:
        process = subprocess.run(
            [sys.executable, "-B", "-m", "knowledge_delta", *arguments],
            cwd=root, env=env, capture_output=True, text=True,
            encoding="utf-8", timeout=15, check=False,
        )
        records.append({"arguments": arguments, "returncode": process.returncode,
                        "stdout": process.stdout, "stderr": process.stderr})
    for record in records[:3]:
        if record["returncode"] != 0:
            raise RuntimeError(f"CLI failed: {record}")
    expected = json.loads((root / "examples/constructed/expected-diff.json").read_text(encoding="utf-8"))
    actual = json.loads(records[0]["stdout"])
    if actual != expected:
        raise RuntimeError("Comparison output differs from the checked-in expected diff")
    cases = json.loads(records[1]["stdout"])
    if (cases["case_count"], cases["draft"], cases["human_reviewed"]) != (7, 7, 0):
        raise RuntimeError("Unexpected sample case counts/review status")
    doctor = json.loads(records[2]["stdout"])
    if doctor["downloads_performed"] or doctor["ollama"]["status"] != "not_checked":
        raise RuntimeError("Default doctor performed unexpected setup/service checks")
    invalid = records[3]
    if invalid["returncode"] != 2 or "error" not in json.loads(invalid["stderr"]):
        raise RuntimeError("Invalid input did not produce a JSON error with exit code 2")
    return {"kind": "foundation_cli_verification", "result": "passed",
            "python": sys.version, "commands": records,
            "checks": ["exact expected diff", "seven draft cases; zero human reviews",
                       "default doctor without downloads or service calls",
                       "invalid input returns JSON error and exit code 2"]}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, ensure_ascii=True))
