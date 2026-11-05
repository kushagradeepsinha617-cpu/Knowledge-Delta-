# Milestone 4 native runtime block

Observed 2026-11-05 on the user's personal Windows computer.

## Result

All 42 resolved CPU dependency versions are installed in the project-local
Python 3.14.10 environment. The final readiness subprocess failed on its first
requested import, torch. Later imports in that subprocess were not reached;
their success must not be inferred.

The traceback reports WinError 4551, Application Control blocking
torch/lib/torch_python.dll or a dependency. Code Integrity event 3077 identifies
torch_python.dll itself and policy VerifiedAndReputableDesktop, GUID
0283ac0f-fff1-49ae-ada1-8a933130cad6.

The DLL is 20,495,360 bytes and SHA256:
f623069dad76898243a64ecc05b3aa53d3e1496829f2c0c8a42ff4da61127ca4.
Its bytes and size match its installed RECORD. Authenticode reports NotSigned.
The installer recorded a matching full CPU wheel SHA256:
8c145170f1ad54edd1ef1da3c872a4a8ada202e24894893df4ed2fc75a8322af,
torch-2.15.0+cpu-cp314-cp314-win_amd64.whl.

These are file-consistency and policy observations. They are not independent
malware analysis, proof that a file is safe, or a claim that Microsoft misclassified it.
This native DLL error is distinct from PowerShell failing to locate a bare
script name and is not a reason to change PowerShell execution policy.

## Evidence

See evidence/milestone4-torch-policy-block:

- actual-package-setup-report.json: 31 existing version matches plus 11 packages
  installed in the final attempt.
- cpu-readiness-error.log: original subprocess traceback.
- policy-observation.json: selected event fields, signature result and flat hash.
- file-integrity-observation.json: actual RECORD/size comparison and wheel identity.

The observed project logical footprint was 1,469,571,044 bytes, global transfer
reservations 328,879,784 bytes and CPU dependency reservations 317,696,941 bytes.
All remain inside the approved ceilings. These are observations, not peak
process RAM, peak installer storage or a filesystem quota guarantee.

## Boundary and next action

The blocked PyTorch execution path is stopped. Do not repeat installation/imports
as a proposed fix for this same signing block. Windows protection remains unchanged.
No alternate DLL loader, relocation, re-signing, exclusion or policy change was
used. No model weights were downloaded, no Ollama server was started, and no
live embedding/inference or benchmark success is claimed.

A legitimate publisher/Microsoft review or a policy-compatible approved path is
needed before this live stack can proceed. No external upload, issue or message
has been authorized or sent. The evidence above can support a review if the user
later authorizes it.

Microsoft explains the relevant reputation/signing checks in its
[developer documentation](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview)
and states that Smart App Control currently has no per-app exception in its
[FAQ](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions).
Keep protection enabled under the project's existing instruction.

Fixture/replay, source validation and genuine human dataset review remain separate
workflows. They do not satisfy Milestone 4's real local model/embedding acceptance.
Current Pydantic review status remains seven reviewed cases and three drafts,
with no human judgments of live answers and no controlled live results.
