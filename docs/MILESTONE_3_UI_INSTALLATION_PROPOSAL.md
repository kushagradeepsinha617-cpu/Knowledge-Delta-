# UI-only setup: explicit budget proposal

Status: awaiting the user's approval. The current limit remains **250 MB**.
No package has been installed. No model download is proposed.

The user ran the bounded inspector in normal PowerShell. The agent read the
saved JSON, matched its inspector source hash, and independently checked the
selected wheel tags, active dependency constraints and size totals offline.
This verifies the recorded preflight, not installed packages or actual peak usage.

## Proposed authorization

- Raise the **total repository-folder ceiling to 750,000,000 bytes (750 MB)**
  for this UI setup, including environments, archives, caches and temporary files.
- Allow **at most 150,000,000 bytes of future package artifact payload**, including
  retries/partial files. The selected 34 wheels total **86,786,535 bytes**.
- Install only the resolved Streamlit/UI dependency candidates in the existing
  project environment. Use project-local profile/cache/temp paths throughout.
- Keep models, Ollama, embedding downloads, global installs, payments and cloud
  services outside this authorization. The old 12 GB model proposal stays deferred.
- Stop and report before exceeding either limit; this is not an open-ended allowance.

## Why 250 MB cannot accommodate this selection

The 34 wheels declare **280,478,795 bytes** of expanded package files. This exceeds
250 MB even before accounting for the repository and environment. These are ZIP
directory declarations, not a measured installation.

The user's inspection recorded an existing folder of 25,240,219 bytes and a
640,953,515-byte plan including an additional full unpacked copy. A later agent
inventory recorded approximately 78.4 MB. We retain both different-time observations
and use the larger one: the corresponding conservative plan is approximately
**694 MB**, including a 25 MB temporary-space reserve. The proposed 750 MB ceiling
provides additional headroom; actual installer behavior remains unverified.

The reserve and extra-copy calculation are planning allowances. They do not prove
that every installer/runtime operation fits. Check current usage before each
stage and stop if its known next-stage needs exceed the approved remainder.

## Concrete scope and checks after approval

1. Recheck the selected artifact lock and actual project usage. Reuse the existing
   interpreter and staged tooling. Reject source builds and unexpected dependencies.
2. Obtain only the selected official wheels, preferably one at a time. Verify each
   complete SHA256 and archive contents/size before extraction or installation.
   The preflight inspected ranges only; it did not authenticate full wheel bodies.
3. Use a hash-locked, offline installation from approved local artifacts, with
   dependency resolution disabled against the separately checked complete closure.
   Account for retained downloads, unpacking, installer copies and generated files.
4. Record actual installed versions and footprint. Then run the real Streamlit
   import, localhost startup and optional AppTest checks. Preserve failures honestly.
5. Keep the twenty cases and all replay outputs labeled fixtures. A functioning
   interface does not establish live inference, genuine human reviews or accuracy.

The agent environment still cannot reach PyPI; the user's normal terminal can.
Any necessary terminal action must be explicit. No installation will start solely
because the user previously granted GitHub push permissions.

## Reviewable inputs

- [Exact wheel candidates, URLs, hashes and dependencies](readiness/ui-wheel-candidates.json)
- [Hash-locked candidate requirements](readiness/requirements-ui.lock.txt)
- [Budget and provenance record](readiness/milestone3-ui-installation-proposal.json)
- [Actual normal-terminal preflight output](evidence/milestone3-ui-preflight-final/normal-terminal-inspection.json)

Keeping the 250 MB limit is also valid: the existing dependency-free fixture CLI
and HTML/JSON reports remain usable, while real Streamlit acceptance stays incomplete.
