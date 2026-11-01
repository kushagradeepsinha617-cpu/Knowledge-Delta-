"""Explicit offline checks with current-run evidence on success or failure."""
import argparse
from contextlib import contextmanager
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET


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
    pins = json.loads((root / "tests" / "dependency-sources.json").read_text(encoding="utf-8"))
    import_roots, provenance = [], []
    for name, suffix in (("pytest", "src"), ("pluggy", "src"),
                         ("iniconfig", "src"), ("colorama", ""), ("pygments", "")):
        directory, manifest = vendor / name, pins[name]
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
    packaging_root, packaging = vendor / "pip-vendor", pins["packaging"]
    if not packaging["files"]:
        raise ValueError("Packaging provenance must list its source hashes")
    for entry in packaging["files"]:
        path = contained(packaging_root, packaging_root / entry["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Packaging source hash mismatch: {path}")
    provenance.append({"name": "packaging", "version": packaging["version"],
                       "method": packaging["method"], "verified_files": len(packaging["files"])})
    import_roots.append(str(packaging_root))
    return import_roots, provenance


def evidence_directory(root, requested):
    directory = contained(root, root / requested)
    for name in ("knowledge_delta", "scripts", "tests", "examples"):
        source = (root / name).resolve()
        if directory == source or directory.is_relative_to(source):
            raise ValueError("Evidence must not be written inside hashed source directories")
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("checks.json", "cli.json", "source-manifest.json", "pytest.xml"):
        path = directory / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Evidence artifact must be an ordinary file: {path}")
    return directory


def write_artifact(directory, name, content, run_id):
    destination = contained(directory, directory / name)
    temporary = contained(directory, directory / f".{name}.{run_id}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(destination)


def save_checks(directory, result):
    if directory:
        write_artifact(directory, "checks.json", json.dumps(result, indent=2) + "\n", result["run_id"])


@contextmanager
def evidence_lock(root, directory):
    """OS-held lock; a leftover lock file is not evidence of a running process."""
    if directory is None:
        yield
        return
    lock_root = contained(root, root / ".tools" / "locks")
    lock_root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(os.path.normcase(str(directory.resolve())).encode("utf-8")).hexdigest()
    path = contained(lock_root, lock_root / f"{key}.lock")
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Evidence directory is busy or cannot be locked; use another output directory") from exc
        # Closing this handle releases the lock, including after exceptions.
        yield


def junit_summary(path):
    xml = ET.parse(path).getroot()
    if xml.tag not in ("testsuites", "testsuite"):
        raise ValueError("Unsupported JUnit root element")
    if any(element.tag in ("failure", "error") for element in xml.iter()):
        raise ValueError("JUnit contains a failure/error despite a zero process exit code")
    for suite in xml.iter():
        if suite.tag not in ("testsuite", "testsuites"):
            continue
        children = list(suite.iter("testcase"))
        derived = {"tests": len(children), "failures": 0, "errors": 0,
                   "skipped": sum(case.find("skipped") is not None for case in children)}
        for label, value in derived.items():
            if label in suite.attrib:
                declared = int(suite.attrib[label])
                if declared < 0 or declared != value:
                    raise ValueError(f"JUnit declared {label} does not match testcase contents")
    cases = list(xml.iter("testcase"))
    counts = {"tests": len(cases), "skipped": 0, "failures": 0, "errors": 0}
    for case in cases:
        for label, element in (("skipped", "skipped"), ("failures", "failure"), ("errors", "error")):
            counts[label] += case.find(element) is not None
    counts["executed"] = counts["tests"] - counts["skipped"]
    if counts["executed"] <= 0:
        raise ValueError("Pytest did not execute any tests; collection-only is not a passing run")
    if counts["failures"] or counts["errors"]:
        raise ValueError("JUnit reports failures/errors despite a zero process exit code")
    return counts


def verification(root, evidence=None, source_mode=False):
    root = root.resolve()
    evidence = evidence_directory(root, evidence) if evidence is not None else None
    with evidence_lock(root, evidence):
        return _verification_locked(root, evidence, source_mode)


def _verification_locked(root, evidence, source_mode):
    """Run checks; testable boundary also records setup/execution failures."""
    result = {"kind": "foundation_verification", "run_id": uuid.uuid4().hex,
              "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "result": "running", "python": sys.version, "commands": [],
              "dependency_mode": "verified_source_imports" if source_mode else "installed_packages",
              "limits": ["No model inference or assistant benchmark",
                         "Only this Python/runtime configuration was tested"]}
    exit_code = 1
    try:
        # Invalidate the previous success before any dependency/source/test work.
        save_checks(evidence, result)
        if evidence:
            for name in ("cli.json", "source-manifest.json", "pytest.xml"):
                (evidence / name).unlink(missing_ok=True)
        source_before = project_source(root)
        result["project_source"] = source_before
        temporary = contained(root, root / ".tools" / "tmp" / result["run_id"])
        temporary.mkdir(parents=True, exist_ok=True)
        junit = temporary / "pytest.xml"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
                   PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONNOUSERSITE="1",
                   TEMP=str(temporary), TMP=str(temporary))
        ignored = ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONOPTIMIZE",
                   "PYTHONINSPECT", "PYTHONSTARTUP")
        result["ignored_environment_overrides"] = [key for key in ignored if key in env]
        for key in ignored:
            env.pop(key, None)
        roots, provenance = source_dependencies(root) if source_mode else ([], [])
        result["source_dependencies"] = provenance
        env["PYTHONPATH"] = os.pathsep.join([str(root), *roots])
        commands = [
            ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", str(root / "pyproject.toml"),
             str(root / "tests"), f"--junitxml={junit}"],
            ["scripts/verify_foundation.py"],
        ]
        for index, arguments in enumerate(commands):
            record = {"arguments": arguments, "result": "running"}
            result["commands"].append(record)
            save_checks(evidence, result)
            try:
                process = subprocess.run([sys.executable, "-B", *arguments], cwd=root, env=env,
                                         capture_output=True, text=True, encoding="utf-8",
                                         timeout=120, check=False)
            except subprocess.TimeoutExpired as exc:
                def decoded(value):
                    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
                record.update(result="timeout", stdout=decoded(exc.stdout), stderr=decoded(exc.stderr))
                raise RuntimeError(f"Check timed out after {exc.timeout} seconds") from exc
            except OSError as exc:
                record.update(result="error", error=str(exc))
                raise
            record.update(returncode=process.returncode, stdout=process.stdout,
                          stderr=process.stderr, result="passed" if process.returncode == 0 else "failed")
            if index == 0 and junit.is_file() and evidence:
                write_artifact(evidence, "pytest.xml", junit.read_text(encoding="utf-8"), result["run_id"])
            if process.returncode:
                result["result"] = "failed"
                exit_code = process.returncode if process.returncode > 0 else 1
                break
            if index == 0:
                result["junit"] = junit_summary(junit)
            else:
                cli = json.loads(process.stdout)
                if cli.get("result") != "passed" or cli.get("kind") != "foundation_cli_verification":
                    raise ValueError("CLI verification did not return an explicit passing result")
                if evidence:
                    write_artifact(evidence, "cli.json", process.stdout, result["run_id"])
        else:
            if project_source(root) != source_before:
                raise RuntimeError("Project sources changed during verification; rerun on a stable copy")
            if evidence:
                write_artifact(evidence, "source-manifest.json",
                               json.dumps(source_before, indent=2) + "\n", result["run_id"])
            result["result"], exit_code = "passed", 0
    except Exception as exc:
        result.update(result="error", error=f"{type(exc).__name__}: {exc}")
        exit_code = 1
    result["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        # Write the terminal status last, after its matching artifacts are ready.
        save_checks(evidence, result)
    except OSError as exc:
        result.update(result="error", error=f"Cannot persist verification evidence: {exc}")
        exit_code = 1
    return exit_code, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dependencies", action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    if sys.prefix == sys.base_prefix:
        parser.error("Run with the isolated project environment's Python")
    root = Path(__file__).resolve().parents[1]
    try:
        code, result = verification(root, args.evidence_dir, args.source_dependencies)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"result": "error", "error": str(exc)}))
        return 2
    print(json.dumps({"result": result["result"], "run_id": result["run_id"],
                      "junit": result.get("junit"), "error": result.get("error"),
                      "dependency_mode": result["dependency_mode"],
                      "pytest_output": result["commands"][0].get("stdout", "") if result["commands"] else ""}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
