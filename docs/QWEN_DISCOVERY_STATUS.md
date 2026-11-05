# Actual Qwen cache and discovery checkpoint

**Later result:** the normal-terminal launcher below successfully exposed the
expected model digest. The ten-question CPU smoke subsequently completed with
ten structured answers and zero run errors. No ACL/security changes were made.
See [actual inference results](LOCAL_INFERENCE_RESULTS.md). The failed
agent-launch evidence and its unproven cause remain preserved below.

The explicit Qwen downloader succeeded. All five config/layer blobs passed their
pinned size and SHA256 checks. The raw manifest matched
`8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
The setup receipt reports 3,411,696,918 bytes reserved in the shared 5 GB artifact
ledger. No inference was performed by setup.

An agent-launched native server subsequently returned version 0.40.14, but its
model list was empty. Its startup and inventory logs reported:

```text
bad manifest name=registry.ollama.ai/library/qwen3:1.7b error="Access is denied."
```

The cache receipt is therefore not evidence of native model readiness.
The owned server was stopped; a subsequent exclusive IPv4 bind on
127.0.0.1:11434 succeeded.

Read-only checks confirmed an ordinary, non-symlink 859-byte V2 manifest with
the expected SHA256. Python could read it. Its ACL grants the user FullControl
and CodexSandboxUsers Modify. Brain checked official version-pinned source:
the V2 path is correct and regular-file reads do not require migration or
symlink replacement. Native path resolution also examines ancestor paths.
The error does not identify the failing operation. A sandbox access difference
is a hypothesis; no security-policy diagnosis has been established.

## Next diagnostic in normal Windows PowerShell

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\local_ollama.py" --start --expected-sha256 14e0fff0449ce3c3a7fe9db8b8b32089274db5f835d4c99f5af7c32dcbf08981
```

Leave that terminal open. This foreground server intentionally keeps running.
It uses the same verified executable and project-local cache/profile/temp
paths, binds 127.0.0.1:11434 and disables cloud operation. No download occurs.
After it starts, inspect inventory and model digest before the ten-question
CPU smoke. If normal-terminal startup still reports the access error, preserve
the output and diagnose it before inference. No ACL or protection changes are
part of this diagnostic.

The structured discovery response and original cache receipt are retained in
`docs/evidence/milestone4-qwen-discovery`. Ordinary offline checks are unchanged
from the 494-test verified checkpoint; no live-answer benchmark exists yet.
