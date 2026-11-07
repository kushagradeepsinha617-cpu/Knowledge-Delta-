# Automated local demo capture

This optional Python/Playwright helper uses a separate hidden Chromium context.
It starts its own localhost app with a fresh copied fixture workspace, so it
does not share personal browser tabs or existing review journals. It loads five
constructed cases, verifies fixture accounting and pending review status, then
saves two screenshots per case and a WebM of that browser session. The final
scene shows the static showcase with the actual study summary. No model calls,
human review submissions or simulated human labels are added.

Run explicit setup once in normal PowerShell:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\record_demo.py" --setup
```

Setup pins Playwright 1.64.1 and installs only its Chromium headless shell and
video tooling. Packages, browser files and temporary files stay under
`.tools/demo-recording/` in the repository. It uses the existing verified pip
wheel and does not install globally. Setup requires internet and adds browser
tooling downloads; it does not download AI models or change Windows protection.

Then record (no setup downloads during this command):

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\record_demo.py"
```

The command prints a new folder under `docs/portfolio/captures/` containing
`knowledge-delta-demo.webm`, ten PNGs and `capture.json`. Do not close the terminal
until it finishes. The recording has no audio. Each run owns its servers and
closes them afterward. Existing localhost8501 is unaffected.

Before presentation, watch the WebM and inspect the PNGs. A successful receipt
means capture and fixture assertions passed; it retains `visual_review: pending`
until the actual artifacts have been inspected. A launch/security error remains
`capture_failed`; do not disable protection or claim that it produced a video.

Offline preflight without Playwright:

```powershell
& "$env:TEMP\Knowledge-Delta-\.venv-ml\Scripts\python.exe" -B "$env:TEMP\Knowledge-Delta-\scripts\record_demo.py" --check
```

The user subsequently installed the pinned tools and ran the complete walkthrough.
All ten screenshots and a 75.12-second 1440x900 silent video were produced. The
last save operation failed because browser.close preceded video.save_as. The
generated video was recovered locally; sampled decoded frames and selected
evidence screenshots were inspected. The original failure receipt is preserved.
The helper now saves after context closure and before browser closure, with
three lifecycle regressions covered in the 592-test offline suite. A new live
run of that fix remains unverified because the agent account cannot read the
user-installed package directory. See `evidence/playwright-video-save-fix/`.
Official references: [video finalization](https://playwright.dev/python/docs/videos)
and [browser selection/storage](https://playwright.dev/python/docs/browsers).
