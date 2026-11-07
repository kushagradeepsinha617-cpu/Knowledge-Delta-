# KnowledgeDelta — 60–90 second demonstration

Use actual running software and recorded reports. Do not substitute a fixture
screen for measured inference. Capture only the app/report window; hide personal
browser content. A continuous public inference endpoint is unnecessary.

## Preparation

Start the local UI from the repository root:

```powershell
& '.\.venv\Scripts\python.exe' -B scripts/run_web.py --serve --port 8501
```

Open `http://127.0.0.1:8501`. Load scripted fixture replay with simulated
correctness judgments unchecked. This part demonstrates interaction, not model
quality. Keep the simulated-output banner visible. Have the real reviewed
dict-pairs report open separately, sourced from the lossless archive documented
in HUMAN_REVIEW.md. Use recorded live results for the measured-results segment.

## Narration and actions

| Time | Narration | Action |
| --- | --- | --- |
| 0–10s | “When documentation changes, an assistant's answer might need to change—or remain correct for an older software version. KnowledgeDelta tests that distinction.” | Show the app title and comparison workspace. |
| 10–25s | “I select two snapshots and a fixed set of questions. This screen is a labeled scripted example, so I can demonstrate the workflow without running a model.” | Show provenance, snapshot changes and the comparison table. |
| 25–45s | “Each comparison keeps both answers, the expected behavior, citations and the exact supplied evidence. A changed answer alone isn't classified as a regression.” | Inspect a case; show the before/after evidence and review controls. Do not submit invented human labels. |
| 45–65s | “For actual experiments, I run MiniLM retrieval and Qwen locally on the CPU. Here is a recorded case with four actual human answer judgments: basic retrieval regressed, while the version-filtered configuration remained correct in this example.” | Switch to the real, human-reviewed dict-pairs report. Show the requested version, source passages and four judgments. |
| 65–80s | “The export preserves answers, configuration and errors. I keep mechanical checks separate from semantic review, and report review coverage rather than treating unknown answers as correct.” | Show HTML/JSON export and review counts. |
| 80–90s | “The result is a reproducible local testing workflow with evidence you can inspect. This small exploratory study supports the recorded examples, not a general accuracy or market claim.” | End on evidence/report view. |

## Claims checklist before recording

- Fixture UI screenshots are labeled fixture demonstrations.
- Only actual archived/live-run numbers are narrated as measurements.
- User blanket case approval is distinct from item-level human review.
- The completed 60-case execution retained 240/240 main records and 36/36
  repeated records, with four main run errors. If those figures appear on
  screen, label the 125/95/16/4 semantic counts as provisional AI-assisted
  proposals, not human accuracy. The new run has zero human answer judgments.
- No claim of independent validation, production readiness or unique invention.

This is an executable recording script, not evidence that a video has already
been recorded. Final recording artifacts and visual checks must be listed in the
Milestone 5 completion audit.
