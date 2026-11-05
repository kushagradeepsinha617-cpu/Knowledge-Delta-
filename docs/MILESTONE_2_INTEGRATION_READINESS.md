# Milestone 2 integration readiness - explicit unavailable checks

**Historical checkpoint below.** Later bounded setup superseded the 250 MB
limit and verified actual NumPy, MiniLM ONNX and ten Qwen CPU requests. See
[current local inference results](LOCAL_INFERENCE_RESULTS.md) for those distinct
observations; the earlier unavailable attempt remains preserved here.

Status: reviewed readiness checkpoint published as
[`ddc9862`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/ddc9862540157c45a51da303701b578d8ba95924),
with all 59 remote source hashes reconciled. This is not completed ML integration.
Larger downloads remain deferred; the 250 MB allowance holds.

## Real NumPy checks are separate

`scripts/integration_tests.py` contains 15 explicit checks that exercise actual
NumPy calculations and array behavior. It is outside the ordinary test directory.
Tokenizer/vector fixtures remain labeled doubles; even successful numeric tests
would not prove sentence-transformers, tokenizer assets, or Ollama integration.

An actual optional attempt is preserved in
[evidence/milestone2-optional-integration/attempt.json](evidence/milestone2-optional-integration/attempt.json):
NumPy was unavailable (`No module named 'numpy'`), the subprocess returned 1 with
a setup error, and **zero numeric integration checks were verified**. No substitute
NumPy implementation, skip, or green integration result is claimed.

After separately authorized setup has created the environment and installed both
pytest and real NumPy, run from the project root in PowerShell:

```powershell
.tools/envs/milestone2/Scripts/python.exe -B -m pytest scripts/integration_tests.py -q -p no:cacheprovider
```

This environment is a future setup prerequisite, not a claim that it exists.
The command does not install dependencies. Preserve any missing-dependency or
import failure as a failed/unavailable integration observation.

## Read-only Windows Ollama launch plan

The current isolated foundation Python can inspect a plan without starting native
code or creating state directories:

```powershell
.venv/Scripts/python.exe -B scripts/local_ollama.py
```

Planning is the default; there is no `--plan` switch. Missing runtime produces a
JSON `missing_runtime` status and exit code 2. That is an actionable readiness
result, not a failed inference request or proof that Ollama has been installed.
The contained launcher is Windows-only; other platforms remain unverified.

The proposed executable must be a regular `.exe` inside the project. Planning
records its SHA256 if present. A matching hash identifies bytes; it does not
authenticate the publisher. Verify the approved upstream archive/provenance
separately before any native execution.

## Explicit future start - not executed here

Only after the user authorizes setup and the executable's provenance and reviewed
SHA256 are established may `--start --expected-sha256 <reviewed-executable-sha256>`
be added to the planning command. This is an explicit native-execution action,
not an installation command. The placeholder is not a usable or preapproved hash.
No real Ollama runtime has been executed for these readiness checks.

The start path checks the fixed localhost port before creating state, launches
`serve` as a foreground child without shell interpretation, and sets project-local
profile/AppData/model/cache/temp locations for that child. It requests localhost
binding, disabled cloud operation, one parallel request, one loaded model and a
4096-token context. Parent/global environment settings are not modified.

These are launch controls, not a demonstrated sandbox around an unverified
binary. A later port-binding race must fail visibly in the runtime. Mocked native
process/socket tests do not prove actual Windows runtime behavior or universal
write containment. No automatic downloads, model switches, or global installs
are performed by planning/startup code.

## Offline checks and review

The new offline evidence lives in
[evidence/milestone2-integration-readiness](evidence/milestone2-integration-readiness/).
Final recorded evidence is detailed below; independent review is complete. Doctor regressions cover malformed
HTTP responses and invalid UTF-8 model names/digests. Launcher tests replace native
execution and socket operations explicitly; those tests are not live execution.

The final frozen source was exercised in three separately scoped checks:

1. **Ordinary offline verification:** 206 executed pytest tests, zero failures,
   errors or skips (1.64s), plus real foundation CLI checks, using Windows/Python
   3.15.2 and verified source-import test dependencies.
2. **Actual read-only launcher command:** exit 2 with `missing_runtime`, native
   execution false, and three checked state paths unchanged. Evidence:
   `docs/evidence/milestone2-integration-readiness/runtime-plan.json`.
3. **Explicit optional NumPy attempt:** exit 1 with a missing-NumPy setup error;
   zero numeric checks verified. This is not part of the 206 passing tests and
   must not be described as 15 successful numeric integrations.

The observations are bound to source ID
`6d56aeec4f6fb6e242aada783465786d01e8ea2205fbd325f4f1da18b0dde188`.
Ordinary verification run: `f196d7458a5f46d894857666e69224ca`.
Brain approved the limited checkpoint and independently verified all 59 source
hashes plus the shared source identity across all three recorded observations.
No downloads, global installations, or actual native runtime launches occurred.

The published pipeline checkpoint [`74ca2f6`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/74ca2f615592ed4c0d55fcc84bfeb802f6c814d8)
recorded 183 offline tests with all 49 remote source hashes reconciled. The smoke
checkpoint [`e9ff0c0`](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-/commit/e9ff0c023e9657aca1e4d287c05995b277886d23)
recorded 195 offline tests with all 55 remote source hashes reconciled. Their
evidence remains historical; neither claims live ML integration.

Independent implementation, preflight and scaffolding are complete. Remaining
Milestone 2 acceptance is blocked by missing local ML dependencies/runtime/assets
and deferred resource authorization. No renewed approval request is pending now.
Actual numeric/embedding imports, live inference/correctness, CPU measurements
and native write containment remain unverified. No Milestone 3 work is started.

When the user later authorizes setup, verify these real integrations and preserve
their observed results separately from the offline checks. The existing folder
uses approximately 14.6 MB within the 250 MB limit; spending remains zero and no
new model/runtime assets were downloaded.
