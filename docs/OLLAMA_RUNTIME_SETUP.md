# Ollama portable runtime preparation

The MiniLM ONNX model now runs locally. The actual smoke produced finite 4x384
unit embeddings, passed duplicate/padding invariance on its fixed strings,
validated Unicode offsets, and rejected input beyond its 256-token limit.
A separate offline retrieval check executed 40 real embedding queries against
distinct 26/86-chunk snapshot indexes. No answering model was called and no
answer-correctness or configuration-improvement score was measured.

## Next explicit step

The approved resource proposal includes this official Windows AMD64 runtime:
Ollama v0.40.14, ZIP 1,601,954,968 bytes, SHA256
65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29.

Source: https://github.com/ollama/ollama/releases/tag/v0.40.14

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\setup_ollama_runtime.py" --prepare
```

Default invocation is an offline plan. Explicit --prepare reads bounded archive
directory metadata first. It refuses a storage/transfer plan that does not fit
the existing 12 GB total-folder and 5 GB additional artifact allowances. Runtime
payload uses the global allowance rather than the 1 GB embedding-package limit.

If the plan fits, it downloads and verifies the entire pinned ZIP, validates
every archive path, and streams extraction to one fresh project-local staging
directory before renaming it to .tools/runtime/ollama. Rename makes no extra
expanded copy. Failed partials retain their transfer reservations; files and
partial extraction evidence remain project-local. Progress prints every 64 MiB.

The version command runs only after archive/file verification. Child profile,
AppData, model and temporary paths are inside the repository. Windows security
remains unchanged; a policy rejection stops this execution path. This tests
ollama.exe --version only: it does not establish engine/model readiness.

No server starts and no Qwen model is downloaded by this command. Qwen will be
a separate explicitly budgeted stage. Before inference, the server must bind
127.0.0.1, model/cache provenance must be checked, and the ten-question hardware
smoke must actually run. No hosted/cloud fallback is permitted.

## Verification boundaries

Offline tests use inert ZIPs and fake HTTP responses; they do not execute native
Ollama or download runtime/model artifacts. Preserve the real runtime preparation
report and any policy/native error rather than claiming success from unit tests.
The existing PyTorch block remains documented; the ONNX embedding implementation
does not load that blocked component.

The optional actual retrieval reproduction is:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\check_onnx_retrieval.py" --output runs/onnx-retrieval-check-new.json
```

It uses already installed/downloaded local assets and makes no model downloads
or answering-model calls. Outputs retain exact passages and source/index IDs.
