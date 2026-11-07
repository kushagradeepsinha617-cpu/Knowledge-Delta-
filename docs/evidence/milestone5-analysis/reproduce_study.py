"""Recompute the frozen study's accounting offline from published archives.

This extracts only hash-verified project files into a fresh project-local folder.
It never starts Ollama, downloads models, or changes the current source tree.
"""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from uuid import uuid4
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/evidence/milestone5-study"
ANALYSIS = ROOT / "docs/evidence/milestone5-analysis"


def checked_bytes(path, expected):
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"Archived hash mismatch: {path}")
    return data


def write_contained(target, name, data):
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError(f"Unsafe archive member: {name}")
    output = target.joinpath(*relative.parts)
    if not output.resolve().is_relative_to(target.resolve()):
        raise ValueError(f"Archive member escapes project reproduction: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)


def main():
    protocol_bytes = (EVIDENCE / "protocol-at-start.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    manifest = json.loads((EVIDENCE / "final-artifact-manifest.json").read_text(encoding="utf-8"))
    if (protocol["protocol_id"] != manifest["protocol_id"]
            or sha256(protocol_bytes).hexdigest() != manifest["protocol_sha256"]):
        raise ValueError("Published protocol binding changed")
    output = ROOT / ".tools/r" / ("reproduced-" + uuid4().hex[:8])
    if output.exists():
        raise ValueError("Fresh reproduction path already exists")
    source = protocol["source"]["files"]
    source_archive = EVIDENCE / "frozen-source.zip"
    checked_bytes(source_archive, manifest["frozen_source_archive_sha256"])
    with ZipFile(source_archive) as archive:
        if set(archive.namelist()) != set(source):
            raise ValueError("Frozen source archive member matrix changed")
        for name, expected in sorted(source.items()):
            data = archive.read(name)
            if sha256(data).hexdigest() != expected:
                raise ValueError(f"Frozen source member changed: {name}")
            write_contained(output, name, data)
    write_contained(output, "runs/milestone5-study-protocol.json", protocol_bytes)

    summary_bytes = checked_bytes(EVIDENCE / "summary-final.json", manifest["summary_sha256"])
    summary = json.loads(summary_bytes)
    if (summary["protocol_id"] != protocol["protocol_id"] or len(summary["runs"]) != 7
            or summary["recorded_main_records"] != 240 or summary["missing_main_records"] != 0):
        raise ValueError("Final execution summary lacks the complete main matrix")
    write_contained(output, "runs/milestone5-study/summary.json", summary_bytes)
    for number, run in enumerate(summary["runs"], 1):
        archive_name = manifest["bundle_archive_files"][str(number)]
        if Path(archive_name).name != archive_name or not archive_name.endswith(".zip"):
            raise ValueError("Bundle manifest has an unsafe filename")
        archive_path = EVIDENCE / archive_name
        checked_bytes(archive_path, manifest["bundle_archive_sha256"][str(number)])
        with ZipFile(archive_path) as archive:
            raw = archive.read("raw-run.json")
        if sha256(raw).hexdigest() != run["raw_sha256"]:
            raise ValueError(f"Raw study bundle {number} changed")
        write_contained(output, f"runs/milestone5-study/bundle-{number}.json", raw)
    variation_archive = EVIDENCE / "development-variability.zip"
    checked_bytes(variation_archive, manifest["variability_archive_sha256"])
    with ZipFile(variation_archive) as archive:
        variability = archive.read("raw-run.json")
    if sha256(variability).hexdigest() != summary["variability_raw_sha256"]:
        raise ValueError("Repeated-run raw hash changed")
    write_contained(output, "runs/milestone5-study/development-variability.json", variability)

    analyzer = ANALYSIS / "summarize_study.py"
    analyzer_bytes = checked_bytes(analyzer, manifest["analyzer_sha256"])
    write_contained(output, "docs/evidence/milestone5-analysis/summarize_study.py", analyzer_bytes)
    for name, expected in manifest["assessment_sha256"].items():
        if Path(name).name != name or not name.endswith("-assessments.json"):
            raise ValueError("Assessment manifest has an unsafe filename")
        data = checked_bytes(ANALYSIS / name, expected)
        write_contained(output, "docs/evidence/milestone5-analysis/" + name, data)

    command = [sys.executable, "-I", "-B", str(output / "docs/evidence/milestone5-analysis/summarize_study.py"),
               "--output", "runs/reproduced-report"]
    process = subprocess.run(command, cwd=output, capture_output=True, text=True, timeout=120)
    if process.returncode or not (output / "runs/reproduced-report.json").is_file():
        raise ValueError(f"Offline analysis failed: {process.stdout[-1000:]} {process.stderr[-1000:]}")
    hashes = {suffix: sha256((output / f"runs/reproduced-report.{suffix}").read_bytes()).hexdigest()
              for suffix in ("json", "html")}
    if hashes != manifest["report_sha256"]:
        raise ValueError("Reproduced JSON/HTML report hashes differ")
    print(json.dumps({"status": "offline_reproduced", "protocol_id": protocol["protocol_id"],
                      "source_files": len(source), "main_records": 240, "variability_records": 36,
                      "output": str(output), "report_sha256": hashes}, indent=2))


if __name__ == "__main__":
    main()
