# Milestone 2 download proposal

Status: metadata checked; large downloads and an expanded storage allowance are
**not yet approved**. All figures below distinguish published bytes from estimates.

## Requested approval

- **12 GB maximum total project-folder footprint**, including archives, extracted
  runtime, environments, models, caches and temporary files.
- **4 GB maximum initial download budget**, with at most **500 MB of compressed
  embedding-package wheels**. Expected initial transfer is approximately
  **3.2–3.6 GB**, not an exact measured total.
- The 4 GB cap is cumulative artifact payload, including retries, partial and\n  intermediate downloads; it is not a measurement of protocol overhead.\n- Keep all intentional files inside the existing local Knowledge-Delta- folder.
  No global install, paid service, new subscription, API credit or card is needed.
- These are hard ceilings. Stop and revise the proposal before exceeding them.

The current authorization remains 250 MB until the user approves this change.
The folder currently uses about 13.4 MB; observed free disk was about 368 GB.
Disk availability is not authorization and says nothing about inference speed.

## Downloads

| Component | Proposed selection | Download amount |
|---|---|---:|
| Existing Python | Reuse installed CPython 3.15.2 initially | 0 |
| Ollama portable Windows AMD64 | v0.40.13 ZIP, official release | **1,601,969,847 bytes** |
| Local answering model | qwen3:1.7b, Q4_K_M | **about 1.4 GB**, rounded published listing |
| Embedding model | all-MiniLM-L6-v2, pinned revision | **about 91.6 MB** with metadata |
| CPU embedding dependencies | Explicit CPU Torch and resolved Windows wheels | **up to 500 MB reserved** |

The official Ollama ZIP contains NVIDIA libraries; this is not a small CPU-only
archive. No separate ROCm or MLX archive is proposed. Official Windows guidance
mentions at least 4 GB for a binary installation, but the portable archive's exact
expanded size has not been measured. The 12 GB ceiling includes temporary/archive
headroom; it is not an installed-size promise.

The MiniLM safetensors file alone is exactly **90,868,376 bytes**. Its SHA256 is
`53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`.
Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Fetch only this weight plus the listed tokenizer/config/pooling/attribution files.
Do not clone the 977 MB multi-format repository or download duplicate weights,
ONNX, OpenVINO, TensorFlow or Rust exports.

Ollama ZIP SHA256:
`7afa38624fa62ee5d8293422d0ab084c1bb4603134c7f4dafce11a033b57cc19`.

The exact Qwen registry manifest size/full digest and CPU Torch wheel size/hash
remain pending. Do not substitute a generic PyPI Torch artifact for the explicit
CPU wheel. Record and validate actual manifests/digests before model use.

No qwen3:0.6b download is proposed initially. Consider that fallback only after
the required measured speed/memory smoke test.

## Compatibility evidence and installation gates

Published wheels exist for the existing Python candidate:
CPU Torch 2.15.0+cpu (cp315 Windows AMD64), Sentence Transformers 6.2.0,
NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Transformers 5.22.1,
Hugging Face Hub 2.4.0, tokenizers 0.23.3, safetensors 0.8.0 and hf-xet 1.8.0.

These are **installation candidates**, not a verified complete lockfile.
Principal non-Torch wheels total about 80.4 MB from rounded displayed sizes.
Additional dependencies still need resolution. No ML import or embedding run has
succeeded yet. Binary wheel availability alone does not prove compatibility.

Before downloading, resolve the complete Windows wheel closure and inspect exact
sizes, tags, requirements and hashes. Reject source builds or unexpected GPU
dependencies; stop if the 500 MB allowance is insufficient. Reuse the existing
interpreter first rather than downloading another Python unnecessarily.

MiniLM's actual embedding configuration limits sequences to **256 tokens**,
including special tokens, even though its tokenizer metadata says 512.
Chunking must respect the smaller embedding limit.

## Folder-only operation

Proposed ignored paths:
`.tools/ollama`, `.tools/ollama-profile`, `.tools/models/ollama`,
`.tools/models/embeddings`, `.tools/cache`, `.tools/tmp`, and `.tools/envs/milestone2`.

OLLAMA_MODELS alone is insufficient: Ollama initializes a keypair under the
profile's .ollama directory. Plan to isolate USERPROFILE, LOCALAPPDATA, APPDATA,
TEMP and TMP **only in the Ollama child environment**, alongside model/cache
settings. Do not change the caller's HOME/CODEX_HOME, system profile, registry,
global PATH or user settings. This is based on current Ollama/Go source;
runtime containment still needs verification.\n\nBefore the first Python ML import or explicit download, set child-only HF_HOME,\nHF_HUB_CACHE, HF_XET_CACHE, TORCH_HOME, PIP_CACHE_DIR, TEMP and TMP to locations\ninside .tools/cache or .tools/tmp. Do not rely on default home-directory caches.

Bind to 127.0.0.1, disable Ollama cloud features, allow one loaded model and one
generation request at a time. Use CPU inference and verify it in runtime traces.
No model or downloaded runtime will be committed to GitHub.

Inspect archive paths and declared uncompressed totals before extraction.
Check existing folder usage and peak temporary needs before each stage.
Download sizes are not RAM measurements; CPU speed and memory use need actual tests.

## Download route and remaining uncertainty

No large assets have been downloaded. A fresh shell probe to public PyPI still
failed with an unreachable-network error. If that restriction remains, a reviewed
repo-local setup command may need to be run by the user in their normal terminal.
Do not bypass network isolation or the earlier browser safety halt.

Ordinary tests and application startup will not download anything. Once assets
are explicitly installed, normal operation is intended to be offline.

## Primary sources

- [Official Ollama release](https://github.com/ollama/ollama/releases/tag/v0.40.13)
- [Windows operation](https://docs.ollama.com/windows) and [local/cloud configuration](https://docs.ollama.com/faq)
- [Qwen candidate](https://ollama.com/library/qwen3:1.7b)
- [Pinned MiniLM files](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41)
- [Official CPU Torch index](https://download.pytorch.org/whl/cpu/torch/)
- Package publishers' PyPI metadata, listed individually in the machine-readable proposal.
- [Ollama keypair initialization](https://github.com/ollama/ollama/blob/v0.40.13/cmd/cmd.go)
- [Go profile/cache/config resolution](https://go.dev/src/os/file.go)

Machine-readable component, permission, hash and uncertainty records:
[download-proposal.json](readiness/milestone2-download-proposal.json).
