# Test setup and reproduction

## Intended ordinary route

Use an isolated Python environment from the repository root:

```powershell
# Select your existing Python executable. Python 3.15.2 was tested.
$basePython = "C:\path\to\python.exe"
New-Item -ItemType Directory -Path ".tools\tmp" -Force | Out-Null
$env:TEMP = (Resolve-Path ".tools\tmp").Path
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = "1"
& $basePython -B -m venv .venv
.\.venv\Scripts\python.exe -B -m pip install --no-cache-dir -r requirements-test.txt
.\.venv\Scripts\python.exe -B scripts/run_checks.py
```

Setup requires internet access. Ordinary checks need neither network nor Ollama
after dependencies are installed. The package is imported directly from the
repository root; no editable installation or wheel build is necessary.
The sandbox prevented the pip installation step here, so that step is unverified.
Only the actual source-run configuration below was exercised.

## Exact source-only method used for verification

The existing interpreter was:
`%LOCALAPPDATA%/Python/pythoncore-3.15-64/python.exe`, version 3.15.2.

An isolated environment was created with `-B -m venv --without-pip .venv`.
All dependency assets and temporary files were kept in the same permitted
repository folder under %TEMP%/Knowledge-Delta-.

Through the GitHub connector, the agents explicitly fetched the listed package
source files, licenses and project metadata at these revisions. Each UTF-8 byte
length and Git blob SHA1 was verified before writing:

| Local directory | Repository / revision | Import root |
|---|---|---|
| .tools/vendor/pytest | pytest-dev/pytest @ ae1d0ff57b8bd4252da9ade7353523ac0ac73281 (9.2.0) | src |
| .tools/vendor/pluggy | pytest-dev/pluggy @ fd08ab5f811a9b2fa9124ae8cbbd393221151e2c (1.6.0) | src |
| .tools/vendor/iniconfig | pytest-dev/iniconfig @ 7faed13ae50bad7c5da3f5782f254a8a7736bb84 (v2.3.0) | src |
| .tools/vendor/colorama | tartley/colorama @ 3de9f013df4b470069d03d250224062e8cf15c49 (0.4.6) | directory itself |
| .tools/vendor/pygments | pygments/pygments @ 708197d82827ba2d5ca78bcbb653c7102ce86dcd (2.20.0) | directory itself |

Tracked package files and exact hashes are enumerated in
[dependency-sources.json](evidence/milestone1/dependency-sources.json).
Sources came from each repository at the recorded commit, not mutable main.
Pytest/pluggy build-generated version files are separately identified and hashed.

The existing Python installation's pip 26.2.2 supplied an unchanged packaging
26.2 source copy at .tools/vendor/pip-vendor/packaging. Its file SHA256 hashes and
origin are also recorded. The older trimmed Pygments copy in that directory is
not used: the complete official Pygments import root precedes it.

Per-package SOURCE_PROVENANCE.json files remain as local staging records.
The current runner instead trusts the checked-in tests/dependency-sources.json
pins, including packaging SHA256 records, and verifies all six dependency copies
and generated metadata before executing genuine pytest. The code assets stay
ignored; their pins are included in the project source manifest.

The authoritative pin/metadata file is tests/dependency-sources.json; it includes
the exact generated version-file contents as well as their hashes.

To reconstruct this special setup, obtain the enumerated source files at the
recorded revisions without line-ending conversion, verify their blob hashes,
place them at the import roots above, preserve licenses, and retain their
source revision records. Generated version files
contain the release versions/tuples recorded in provenance; their exact contents
must match the recorded hashes. This is a forensic reproduction recipe, rather
than an automatically tested download/bootstrap script. For normal use, prefer
the ordinary pip route.

## Verified command on the prepared local copy

```powershell
# Run from the already-open repository root; setup may have changed TEMP.
.\.venv\Scripts\python.exe -B scripts/run_checks.py --source-dependencies --evidence-dir docs/evidence/milestone1-audit
```

Latest result: 92 tests executed and passed, followed by successful real subprocess CLI checks.
No test starts a model service or downloads dependencies/models.
The explicit evidence option starts a fresh run ID and updates current evidence
on failure as well as success; prior raw artifacts are invalidated before setup.
Only one writer may own an output directory at a time. File-write failures are
reported, but an unwritable destination cannot be guaranteed an updated record.
Use a new output directory to preserve a previous run.
The runner confines its chosen evidence directory to the project and requires
an isolated interpreter.

Keep source mode and installed-package mode distinct when recording future runs.
A successful source run does not prove pip installation or wheel-building works.
