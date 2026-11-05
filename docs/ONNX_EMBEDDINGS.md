# Direct local ONNX MiniLM embeddings

Status: adapter/download preparation verified offline. Actual model embeddings
remain pending the explicit command below.

ONNX Runtime 1.31.1, NumPy 2.5.4 and tokenizers 0.23.3 actually imported in the
project-local Python 3.14.10 environment. CPUExecutionProvider is available and
torch is absent from sys.modules. The new downloader also passed its current
environment/module-path/version gate without downloading anything.

## Exact local assets

Model: sentence-transformers/all-MiniLM-L6-v2.
Revision: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41.
Selected assets: 91,115,253 bytes total; one ONNX graph plus ten small tokenizer,
configuration, pooling and model-card files. No alternate precision exports,
safetensors/PyTorch weights or duplicate model collection is fetched.

The official pinned LFS pointer records onnx/model.onnx as 90,405,214 bytes,
SHA256 6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/onnx/model.onnx

Small files are checked against their pinned Git blob identities and sizes.
Every actual asset also gets a recorded SHA256. The model card declares Apache-2.0
and is retained locally with attribution/provenance. Model files stay under
.tools/models/minilm-onnx and are excluded from Git.

## Explicit download and smoke

Use normal PowerShell because the agent shell's public-network access is blocked:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\setup_minilm_onnx.py" --download --runtime-report runs/onnx-setup/b110e5cb0af3449983c1962ff48d0022.json
```

This verifies the actual isolated runtime and report binding before networking,
then downloads only the selected assets over bounded HTTPS redirects. Sizes and
digests are mandatory, existing verified files are reused, and incomplete or
corrupt files are not promoted. Partial/retried model bytes count against the
existing 5 GB global ledger; project files remain under the 12 GB folder ceiling.
No new purchase, subscription, global install or security change is required.
No Ollama or answering-model request occurs.

The final check uses actual local model inference on constructed smoke strings:
384-dimensional finite unit vectors, duplicate consistency, single-versus-padded
batch invariance, original-text Unicode offsets, a 256-token boundary and
overlength rejection. Reports retain model/configuration identities, versions,
raw smoke vectors and timings under runs/minilm-setup. These checks do not
establish RAG correctness, industry accuracy, PyTorch bitwise equivalence,
general determinism or a measured speed improvement.

## Adapter decisions

Raw tokenizers disables serialized padding/truncation. Counts include special
tokens; chunks use original-text offsets without special-token offsets. The
effective model limit is 256. Batches are padded explicitly, with the tokenizer's
padding ID and int64 graph inputs.

ONNX sessions request only CPUExecutionProvider, sequential execution and one
intra/inter-op thread. The adapter requires float last_hidden_state[B,T,384],
then applies attention-mask mean pooling over all attended tokens (including
special tokens), followed by L2 normalization. Portable Python accumulation is
converted to float32 for the NumPy index; this is recorded in the backend identity.
Malformed shapes, nonfinite values, zero masks/norms and unsupported graph inputs
are failures, never substitute vectors.

The model card documents this pooling/normalization approach:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md

Answering, hardware-smoke and dataset-run CLIs now accept the explicit option
--embedding-backend onnxruntime with this model directory. The legacy adapter
remains selectable; there is no automatic backend/model fallback. Both retrieval
configurations must use the same fixed ONNX settings for their comparison.
