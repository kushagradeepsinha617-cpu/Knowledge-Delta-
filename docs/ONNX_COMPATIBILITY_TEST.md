# Approved ONNX Runtime compatibility test

The user explicitly approved this separate CPU backend test on 2026-11-05.
Windows protection remains enabled. The blocked PyTorch DLL and its evidence
remain preserved; this test requests no PyTorch or Sentence Transformers import.

## Purpose and boundary

Check whether an independently installed ONNX Runtime CPU package can import in
the existing project-local Python 3.14.10 environment. NumPy 2.5.4 and tokenizers
0.23.3 have already imported successfully in that environment, with torch absent
from sys.modules. That does not establish ONNX Runtime or model execution.

The upstream MiniLM repository contains an
[ONNX export at the pinned revision](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/onnx).
[ONNX Runtime documents a CPU Python package](https://onnxruntime.ai/docs/get-started/with-python.html).
The proposal is to use that separate runtime with the same model family, not to
load, modify or re-sign the blocked PyTorch DLL.

The Sentence Transformers Python library itself depends on PyTorch, so its
backend option alone is insufficient for this environment. If the runtime test
passes, a separately recorded direct ONNX embedding adapter will still need
tokenization, attention-mask pooling, token limits, artifact provenance and
actual local-model validation. Neither equivalence nor embedding success is
inferred from an import test.

## Explicit command

Default invocation is an offline plan. This authorized compatibility command
resolves metadata, inspects wheel directories, freezes exact identities, installs
only missing compatible wheels, then probes imports and CPU-provider availability:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\setup_onnx_runtime.py" --test
```

No model weight, Ollama runtime or model download occurs in this command. It
writes project-local reports under runs/onnx-setup and shares the approved
12 GB storage / 5 GB global transfer / 1 GB CPU dependency budgets, including
metadata ranges, partials and retries. Existing differing versions are preserved
and cause an actionable stop rather than an automatic replacement.

The package graph excludes torch, sentence-transformers, transformers and
GPU/DirectML runtime variants. The child import list is exactly onnxruntime,
numpy and tokenizers; its output must show torch_imported=false and a
CPUExecutionProvider. Full wheel/METADATA hashes and dependency checks remain
required. A native policy failure is preserved and stops this candidate path;
no Windows security setting or blocked component is altered.

## Evidence and interpretation

Offline contract tests and default-plan execution establish preparation only.
Actual package availability, full-wheel integrity, native import acceptance
and provider availability require the explicit command's report.

Successful imports are a compatibility result, not a real embedding run, answering
model result, correctness score or controlled experiment. Any later ONNX run must
record its backend/model artifact identities and hold that backend fixed across
both retrieval configurations. There are no earlier live PyTorch measurements to
compare against, and no claimed performance improvement.
