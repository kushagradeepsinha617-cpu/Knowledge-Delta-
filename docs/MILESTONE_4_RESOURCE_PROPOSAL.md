# Milestone 4 local runtime proposal — bounded limits approved

Prepared 2026-11-05. The user explicitly approved the limits below on 2026-11-05.
Compatibility, hashes, expansion and native execution remain unverified.

The user authorized Milestone 4 implementation. The previous allowance was UI-only: 750,000,000 bytes storage and
150,000,000 bytes artifact payload. The subsequent explicit approval below
authorizes bounded model setup; it does not establish readiness.

## Requested separate limits

- At most **12,000,000,000 bytes total inside the existing project folder**,
  including the current environment, archives, models, extracted files,
  caches, temporary files and results.
- At most **5,000,000,000 bytes of additional artifact payload**, counting failed,
  partial and retried transfers. Reserve at most **1,000,000,000 bytes** within
  this total for CPU embedding dependencies.
- This is a maximum allowance, not an instruction to consume it. Before an
  artifact download, require an exact compatible artifact list, hashes and
  storage/temporary-space plan that fits both limits. Stop if it does not fit.
- No global installation, hosted API, paid service or security-policy change.
  Keep all intentional project files inside the existing repository folder.
- Download only qwen3:1.7b and one MiniLM weight format initially. Do not fetch
  qwen3:0.6b unless a measured smoke test justifies a separately recorded choice.

## Current evidence

The local Python probe on 2026-11-05 observed CPython 3.15.2 AMD64,
12 logical CPUs, processor identifier Intel64 Family 6 Model 154 Stepping 3,
GenuineIntel; it did not establish an exact CPU marketing name, physical RAM
or GPU capability. User-reported RAM is 16 GB; assume CPU-only.

Observed free disk: 357,458,087,936 bytes. Observed project logical files:
409,570,933 bytes before the small Pydantic bundle. Disk availability is not
authorization or an inference-speed prediction. Ollama was not found on this
process's PATH; that does not prove it is absent everywhere.

Official Ollama release API metadata checked 2026-11-05:
- v0.40.14, published 2026-11-03.
- Standard portable Windows AMD64 ZIP: **1,601,954,968 bytes**.
- SHA256: `65d68cade6cf6375f398b518224f8c8a15e062387f38cf477abfc848de7e7e29`.
- Source: https://github.com/ollama/ollama/releases/tag/v0.40.14
- Expanded archive size and native execution remain unverified.
  The smaller MLX/ROCm archives are not assumed to be valid CPU substitutes.

Official qwen3:1.7b listing still advertises Q4_K_M at about **1.4 GB**:
https://ollama.com/library/qwen3:1.7b
The exact registry manifest, layer sizes and full digest remain pending;
a rounded web listing is insufficient for an installer lock.

Existing MiniLM candidate is pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, with one
90,868,376-byte safetensors weight and approximately 91.6 MB including assets.
Verify the full asset inventory before downloading or asserting provenance:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41

The previous CPU wheel candidates in MILESTONE_2_DOWNLOAD_PROPOSAL.md are
historical metadata observations, not a verified current dependency lock.
CPU Torch, sentence-transformers and the complete Windows/Python compatibility
closure still require fresh metadata resolution and a measured space plan.
The 1 GB dependency reservation is a ceiling, not a size prediction.

## Execution gates and success evidence

1. Verify current asset metadata and hashes; inspect archive expansion without
   running its contents; preflight total and temporary storage.
2. Download only explicitly approved artifacts with cumulative accounting.
3. Verify complete bytes/digests and applicable publisher/security status.
   Keep Smart App Control On. If Windows blocks a native component, preserve
   evidence and stop that execution path; do not bypass the policy.
4. Verify actual CPU embedding and tokenizer imports, local MiniLM loading,
   offline embeddings and separate NumPy indexes.
5. Start Ollama bound to 127.0.0.1 with project-local model/cache/temp paths.
   Validate containment and installed API capabilities.
6. Run the ten-question hardware smoke test sequentially. Record failures,
   available timings/tokens/model digest and observed resources.
7. Freeze human-reviewed case definitions and run the controlled protocol in
   MILESTONE_4.md. Preserve raw outputs. Do not claim scores before real reviews.

No assets were downloaded, models installed or live inference performed to prepare
this proposal. Approval of resource ceilings would not establish compatibility,
security-policy acceptance, model quality, measured speed or milestone completion.


## Subsequent metadata observations

The corrected normal-terminal model inspection succeeded for all five sources.
Exact Qwen layer/config payload is 1,359,293,444 bytes, with manifest
SHA256 8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7.
Pinned MiniLM selected assets total 91,578,415 bytes. The CPU wheel candidate is
torch 2.15.0+cpu for cp315 Windows AMD64 from PyTorch's official CDN, with SHA256
5c21ee962b6f67821dac0bc882f5ee1539a4edeabe736284d2ff1d652e595ed1.
These supersede the earlier rounded/pending observations above; they do not prove
full dependency compatibility or native execution. Original reports are preserved.

The next explicit, bounded inspection is:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\inspect_embedding_setup.py" --inspect
```

It resolves the proposed CPU embedding dependency closure and reads ZIP directory
ranges to plan expansion. It does not install packages or download model weights.
Partial wheel metadata/directory payload is conservatively reserved in the
project-local model-setup ledger against the approved 5 GB allowance, including
the two earlier successful normal-terminal metadata transfers. Repeated or failed
reads retain their reservations. Its default operation is an offline plan.
The combined Ollama/runtime/model expansion gate remains separate and pending.
