# Streamlit setup proposal: metadata stage only

Update: the normal-terminal preflight has now resolved 34 wheels and inspected
their size declarations. They exceed the current 250 MB limit. See the separate
[UI-only installation proposal](MILESTONE_3_UI_INSTALLATION_PROPOSAL.md), which
requests a new ceiling but does not change the current authorization. The initial
metadata-stage investigation below is retained as history.

Checked 2026-11-04. This proposal concerns the local fixture/review interface.
It does not authorize Ollama, embedding weights, answering models, a storage
increase, global installations, or a GitHub push. The deferred
[Milestone 2 model proposal](MILESTONE_2_DOWNLOAD_PROPOSAL.md) remains separate.

## Recommendation

Keep the existing 250,000,000-byte ceiling. First obtain a complete, compatible
Windows/CPython 3.15 dependency manifest and inspect its storage requirements.
Do not start a general `pip install streamlit` while those requirements are unknown.
No binary download is proposed as the next action. No budget increase is requested.

The project measured 58,364,804 logical bytes before recording the new probe,
leaving approximately 191.6 MB within the ceiling. This includes the existing
environment, dependency sources and ignored test/report artifacts. It is not a
measurement of filesystem allocation or available RAM.

## Verified candidates, not an installation lock

| Package | Candidate | Windows CPython 3.15 artifact | Published compressed size |
| --- | --- | --- | --- |
| Streamlit | 1.66.1 | py3-none-any | 10,364,948 bytes |
| PyArrow | 26.0.1 | cp315-cp315-win_amd64 | approximately 29.8 MB |
| pandas | 3.1.0 | cp315-cp315-win_amd64 | approximately 10.9 MB |
| NumPy | 2.5.4 | cp315-cp315-win_amd64 | approximately 12.7 MB |

This is approximately 63.8 MB for four compressed files only. It is neither the
complete download total nor an installed-size or peak-storage estimate. These
artifact tags are candidates for the observed interpreter; successful imports
and actual runtime compatibility remain unverified.

Streamlit also requires Altair, Click, packaging, Pillow, PyDeck, protobuf,
requests, typing-extensions, Starlette, Uvicorn, AnyIO, python-multipart,
websockets, itsdangerous and watchdog on Windows, plus transitive dependencies.
Optional Snowflake, authentication, charting, SQL and performance extras are not
needed for this interface. Do not resolve `streamlit[all]`.

## Required evidence before installation

1. Resolve the entire dependency closure for the actual interpreter, Windows
   architecture and base Streamlit dependencies (no optional extras). Record exact versions, URLs,
   artifact SHA256 values, wheel tags and dependency/environment markers.
2. Reject incompatible wheels, source builds and unexpected optional extras.
   Check existing assets without assuming globally installed packages can be used.
3. Inspect the wheels' declared expanded file sizes before extraction, using
   bounded archive-metadata requests where supported. An ignored HTTP Range
   request must not silently become an unbounded full download. If this cannot
   be measured safely, stop; do not infer expanded size from compressed bytes.
4. Account for existing files, downloads retained during extraction, installed
   files, installer/profile/cache state and a stated temporary-space reserve.
   The complete peak must fit 250 MB before any install can proceed. Request a
   separate concrete budget change only if measured requirements exceed it.
5. Use project-local environment/profile/cache/temp paths. Verify real imports,
   localhost startup and the optional AppTest checks after explicit setup.
   Passing controller tests does not establish those runtime observations.

## Current execution blocker

The actual bounded metadata request to PyPI on 2026-11-04 failed with
`URLError` / `WinError 10051` (unreachable network). It downloaded no wheel or
model. The ordinary user terminal's connectivity remains unknown; the earlier
read-only connectivity check was subsequently reported as HTTP 200 by the user
in their normal PowerShell terminal. This is a user-reported observation, not
an agent-side package installation or a verified complete dependency download.
The agent environment still cannot make the request. The normal terminal can
now be used for the explicit read-only inspector below.

## Next explicit inspection command

From any normal PowerShell terminal, use the existing isolated interpreter:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\inspect_ui_setup.py"
```

This resolves the base Streamlit dependency candidates against the actual
interpreter and checks hashed wheel-specific metadata. It reads bounded byte
ranges from wheel archives to sum their declared expanded file sizes. It does
not save/extract archives, install packages, or download models. For very small
wheels, an archive-metadata range may span the whole small archive; the output
does not claim to have verified full artifact bodies or their hashes.

The script writes only `runs/ui-setup-inspection.json` inside this repository.
Existing files are preserved. For a later inspection, use a new filename such as
`--output runs/ui-setup-inspection-2.json`. Share the printed summary after running it.
Unsupported constraints, unverified
metadata, bad ranges, ZIP64 and conflicting records produce an explicit failure,
not a guessed compatible package or installation. This bounded preflight is not
a general-purpose pip resolver or an installer.

Its storage report includes existing files, compressed wheel sizes, declared
expanded sizes and a stated 25 MB temporary-space reserve. The reserve is a
planning allowance, not measured installer overhead. No package installation or
storage increase is authorized by a successful preflight alone.

The next useful observation is a usable metadata/setup route, followed by full
resolution and expanded-size accounting. Until then the dependency-free fixture
CLI and self-contained reports remain usable, and real Streamlit acceptance is
incomplete. No larger footprint or installation success is claimed.

## Primary sources

- [Streamlit release metadata](https://pypi.org/pypi/streamlit/1.66.1/json)
- [PyPA Simple API and hashed wheel metadata](https://packaging.python.org/en/latest/specifications/simple-repository-api/)
- [Published Streamlit dependency declaration](https://github.com/streamlit/streamlit/blob/ca6718b7d3d788c31c97d1bc9144fd8388168f57/lib/pyproject.toml)
- [PyArrow 26.0.1 files](https://pypi.org/project/pyarrow/26.0.1/)
- [pandas 3.1.0 files](https://pypi.org/project/pandas/3.1.0/)
- [NumPy 2.5.4 files](https://pypi.org/project/numpy/2.5.4/)

Machine-readable candidates and the actual connectivity observation are recorded
in [UI readiness](readiness/milestone3-ui-download-proposal.json). These two new
proposal files are separate artifacts from the 16-file measurement checkpoint.
The user's later blanket push authorization permits publishing both records;
it does not authorize downloads or an increased storage limit.
