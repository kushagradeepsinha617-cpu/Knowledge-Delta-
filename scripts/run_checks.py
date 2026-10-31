"""Explicit offline verification; optional source dependencies are never downloaded.

Use an isolated project Python. Normal mode uses installed test dependencies.
--source-dependencies uses the separately staged, provenance-checked source trees.
--evidence-dir explicitly saves the executed commands and real pytest JUnit XML.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def contained(root, path):
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path must stay inside {root}: {path}")
    return path


def project_source(root):
    paths = []
    for directory in ("knowledge_delta", "scripts", "tests", "examples"):
        paths.extend(path for path in (root / directory).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts)
    paths.extend(root / name for name in ("pyproject.toml", "requirements-test.txt", ".gitattributes"))
    files = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(paths)}
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"algorithm": "sha256", "source_id": hashlib.sha256(encoded).hexdigest(), "files": files}


def source_dependencies(root):
    vendor = root / ".tools" / "vendor"
    import_roots = []
    provenance = []
    for name, suffix in (("pytest", "src"), ("pluggy", "src"),
                         ("iniconfig", "src"), ("colorama", ""), ("pygments", "")):
        directory = vendor / name
        manifest = json.loads((directory / "SOURCE_PROVENANCE.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            path = contained(directory, directory / entry["path"])
            data = path.read_bytes()
            header = b"blob " + str(len(data)).encode("ascii") + b"\0"
            if len(data) != entry["size"] or hashlib.sha1(header + data).hexdigest() != entry["git_blob_sha1"]:
                raise ValueError(f"Dependency source hash mismatch: {path}")
        for entry in manifest["generated_files"]:
            path = contained(directory, directory / entry["path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Generated build metadata hash mismatch: {path}")
        provenance.append({"name": manifest["name"], "release_tag": manifest["release_tag"],
                           "commit": manifest["commit"], "verified_files": len(manifest["files"]),
                           "generated_files": manifest["generated_files"]})
        import_roots.append(str(directory / suffix))
    # Packaging is an unchanged copy from the existing pip installation.
    packaging_root = vendor / "pip-vendor"
    if not (packaging_root / "packaging" / "__init__.py").is_file():
        raise ValueError("Missing explicitly staged packaging dependency")
    copies = json.loads((packaging_root / "SOURCE_PROVENANCE.json").read_text(encoding="utf-8"))
    packaging = next(copy for copy in copies if copy["name"] == "packaging")
    provenance.append({"name": "packaging", "method": "existing pip-vendored source copy",
                       "details": packaging})
    import_roots.append(str(packaging_root))
    return import_roots, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dependencies", action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if sys.prefix == sys.base_prefix:
        parser.error("Run this command with the isolated project environment's Python")
    root = Path(__file__).resolve().parents[1]
    source_before = project_source(root)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONNOUSERSITE="1")
    temporary = root / ".tools" / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = env["TMP"] = str(temporary)
    import_roots, provenance = source_dependencies(root) if args.source_dependencies else ([], [])
    env["PYTHONPATH"] = os.pathsep.join([str(root), *import_roots])
    evidence = contained(root, root / args.evidence_dir) if args.evidence_dir else None
    if evidence:
        evidence.mkdir(parents=True, exist_ok=True)
    pytest_args = ["-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if evidence:
        pytest_args.append(f"--junitxml={evidence / 'pytest.xml'}")
    commands = [pytest_args, ["scripts/verify_foundation.py"]]
    records = []
    for arguments in commands:
        process = subprocess.run([sys.executable, "-B", *arguments], cwd=root, env=env,
                                 capture_output=True, text=True, encoding="utf-8",
                                 timeout=120, check=False)
        records.append({"arguments": arguments, "returncode": process.returncode,
                        "stdout": process.stdout, "stderr": process.stderr})
        if process.returncode:
            print(process.stdout, end="")
            print(process.stderr, end="", file=sys.stderr)
            return process.returncode
    if project_source(root) != source_before:
        raise RuntimeError("Project sources changed during verification; rerun on a stable copy")
    result = {"kind": "foundation_verification", "result": "passed", "python": sys.version,
              "project_source": source_before,
              "dependency_mode": "verified_source_imports" if args.source_dependencies else "installed_packages",
              "source_dependencies": provenance, "commands": records,
              "limits": ["No model inference or assistant benchmark", "Only this Python/runtime configuration was tested"]}
    if evidence:
        (evidence / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (evidence / "cli.json").write_text(records[1]["stdout"], encoding="utf-8")
        (evidence / "source-manifest.json").write_text(json.dumps(source_before, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "passed", "pytest_output": records[0]["stdout"],
                      "dependency_mode": result["dependency_mode"], "evidence_dir": str(evidence) if evidence else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
