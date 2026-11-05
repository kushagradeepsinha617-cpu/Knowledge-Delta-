# Explicit Qwen model download

**Current checkpoint:** the download succeeded, but the agent-launched server
could not read the manifest. Do not repeat the download. See the
[discovery findings and normal-terminal diagnostic](QWEN_DISCOVERY_STATUS.md).

The portable Ollama 0.40.14 runtime was downloaded, hash verified and executed.
A temporary project-local server returned version 0.40.14 and an empty model
list over localhost. It was stopped; a subsequent exclusive IPv4 bind to
127.0.0.1:11434 succeeded. No answering inference has run yet.

Run the next explicit setup command in normal Windows PowerShell:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\setup_qwen_cache.py" --download
```

This downloads the pinned **qwen3:1.7b** config and layers, totaling
**1,359,293,444 bytes** (about 1.36 GB), plus a bounded manifest read. Progress
prints every 64 MiB. Default invocation without `--download` is an offline plan.
No native model pull, server startup or inference happens in this command.

The raw manifest SHA256 must match:
`8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
If the upstream tag changes, setup stops rather than changing the experiment.
Every new and reused blob is checked against its exact size and SHA256.
The named manifest is written only after every required blob verifies.
Existing different files are preserved for inspection.

Downloads share the persistent 5 GB artifact-transfer ledger, including partial
attempt reservations. At the runtime-preparation checkpoint, 2,052,402,609 bytes
were reserved; the pinned model fits the remaining allowance. Do not delete or
reset the ledger. The 12 GB folder planning check includes reserve space and
runs during transfer; it is not an operating-system disk quota. Runtime/model
payload is separate from the 1 GB CPU dependency sub-budget. Files stay inside
the repository. No protection setting changes and no paid service are required.

The importer holds an exclusive bind on **127.0.0.1:11434** while changing the
cache. Stop the project-local Ollama server first. This guards that address and
port, not every possible Ollama server or unrelated cache writer. The shared
setup lock serializes the project's own setup commands. Do not run another
cache writer during setup.

HTTPS redirects are limited and checked against the registry/storage host list.
Redirect bodies are closed without reading them; artifact reads are reserved
before consumption. Failed attempts produce a new JSON report under
`runs/qwen-setup`. Verified complete blobs are reusable; an interrupted current
blob is discarded and a retry consumes additional allowance. Stop if the report
says the allowance cannot cover the remaining payload.

## Cache format and verification limits

This preparer targets the pinned runtime's Windows regular-file V2 layout:
`.tools/models/ollama/manifests-v2/ollama.com/library/qwen3/1.7b`, with SHA256
blobs under the same cache's `blobs` directory. The manifest's original bytes
are preserved. This follows the official version-pinned
[path helpers](https://github.com/ollama/ollama/blob/v0.40.14/manifest/paths.go)
and [manifest implementation](https://github.com/ollama/ollama/blob/v0.40.14/manifest/manifest.go).

Offline tests use small synthetic bytes and fake HTTP responses. They establish
validation, budget accounting, interruption handling, redirect bounds and
manifest promotion behavior; they are not model benchmark results. Brain
reviewed the redirect fix after finding an unaccounted redirect-body read in
the initial implementation.

Successful status is `pinned_model_cache_verified_discovery_pending`. A real
server must still discover the expected model/digest, and the ten-question CPU
hardware smoke must run before claiming that Qwen answering works. Embedding
success alone does not establish answering speed, memory use or correctness.
