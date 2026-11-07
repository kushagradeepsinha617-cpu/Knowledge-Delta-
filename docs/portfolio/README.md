# KnowledgeDelta portfolio package

Open `docs/portfolio/index.html` for the static showcase, then
`docs/evidence/milestone5-analysis/final-study-report.html` to inspect the
completed local study. The three screenshots in `docs/screenshots/` show the
actual browser interface in **scripted fixture replay** mode. The report and
screenshots have different provenance; a fixture screen is not a live result.

## What the project demonstrates

KnowledgeDelta compares versioned documentation snapshots, runs the same
questions against both, and retains the assistant's answers, citations and
exact supplied passages. It helps a developer inspect whether a documentation
change calls for a different answer or exposes an answer failure. The reference
assistant uses local MiniLM ONNX embeddings and Qwen through Ollama.

## Recorded evidence

- Frozen study: 60 case definitions, 20 development and 40 held out.
- Main execution: 240/240 records, four run errors, 24 deterministic
  evidence-only abstentions, 216 chat attempts and 212 completed responses.
- Repeated subset: 36/36 records, zero errors; five of twelve cells had more
  than one distinct structured answer object. Meaning differences were not
  judged from object inequality.
- AI-assisted provisional proposals: 125 pass (24 policy, 101 generated),
  95 fail, 16 need human review, four run errors. These are **not** human
  benchmark accuracy or independent evaluator reference labels.
- Case-definition review: owner blanket approval of 60, with 11 individual
  human case reviews and one individually reviewed expected relation. The
  new study has zero human answer judgments. Four human answer judgments
  from an earlier run remain bound to that earlier run.

The `docs/evidence/milestone5-study/final-artifact-manifest.json` file binds
the raw archives and frozen source. An offline reproduction generated the same
JSON/HTML report hashes; its receipt is next to the manifest. The full
repository contains all raw runs and the local application.

## Presentation materials

- `README.md`: setup and scope.
- `docs/CASE_STUDY.md`: problem, implementation, observations and limits.
- `docs/ARCHITECTURE.md`: components and design decisions.
- `docs/DATASET_CARD.md`: source attribution, split and review provenance.
- `docs/EXPERIMENT_RESULTS.md`: controlled results and denominators.
- `docs/DEMO_SCRIPT.md`: a 60–90 second recording script.
- `docs/SHOWCASE.md`: labeled screenshot gallery.

The package is a portable presentation set, **not** the runnable Python repo
or a hosted AI endpoint. To run the tool locally, use the
[full repository](https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-)
and its README. A video, if supplied separately, should show the same provenance
labels and avoid personal browser tabs. No video is implied by this package.
