# Showcase materials

These screenshots were captured from the actual local application in Chrome.
They show the explicitly labeled scripted fixture workflow. They are not model
benchmark screenshots or fabricated UI mockups. The desktop pet visible in the
right margin is external to KnowledgeDelta.

## Comparison workspace

![Labeled fixture comparison workspace](screenshots/fixture-workspace.png)

## Case explorer

![Fixture comparisons and status filters](screenshots/fixture-comparisons.png)

## Exact evidence inspection

![Scripted answers beside their snapshot evidence](screenshots/fixture-evidence.png)

The example intentionally retains an old answer while the supplied passage
changes from 10 to 20 seconds. Its unresolved judgment is visible; this is a
workflow demonstration, not a human-graded live regression.

## Actual recorded example

For an earlier human-reviewed live example, use the lossless archive in
`docs/evidence/milestone4-human-answer-review/`. The generator
`docs/evidence/milestone5-demo-report/reproduce_report.py` verifies the raw
hash and exact published human-review counts/metrics without calling a model
or opening the private review database. Its generated local HTML/JSON copy
under `docs/portfolio/reviewed-example/` embeds machine-specific Ollama paths,
so that copy is excluded from the portable presentation package. The raw
archive and generator preserve reproducibility.

Use [the demo script](DEMO_SCRIPT.md), [case study](CASE_STUDY.md),
[architecture](ARCHITECTURE.md) and [review provenance](REVIEW_PROVENANCE.md)
alongside these images. A completed video is a separate artifact, not implied
by this gallery or its script.

The [completed 60-case study report](evidence/milestone5-analysis/final-study-report.html)
shows the 240 main records, 36 repeat records, errors and provisional AI-assisted
review coverage. It does not claim human-validated study accuracy. Its
[offline reproduction receipt](evidence/milestone5-study/offline-reproduction-receipt.json)
binds the exact report hashes. The portable showcase bundle in `portfolio/`
contains this final report and the labeled screenshots; historical raw archives
and the full runnable tool remain in the repository.
