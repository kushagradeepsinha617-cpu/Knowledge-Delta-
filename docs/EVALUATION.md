# Evaluation protocol

Protocol version: `m4-initial-v1`. Planned work is distinct from executed evidence.
The first study uses the ten development families and corpus-assembly condition
described in [MILESTONE_4.md](MILESTONE_4.md). No results are asserted here.

## Freeze inputs before measurement

Record exact snapshot manifests/IDs, case dataset/hash, family/split assignments,
draft or actual human-review records, and expected-change annotations. Expectations
are per snapshot. Preserve each explicit requested version; current/default
questions require an explicit manifest target for each snapshot.

For the initial Pydantic pair, adding v1 documents should leave all ten explicit
v2 answers substantively correct. These are draft hypotheses until a human checks
questions, applicability, expectations, source quotes and rubrics. Agent code
review or source inspection does not constitute human dataset review. Record the
actual reviewer and scope, without claiming independent or blind review unless
that procedure occurred. Keep answer keys/rubrics outside indexes and prompts.

Freeze model identity/digest, embedding identity/assets, chunking, top-k, prompt,
context/output budgets and pipeline versions. Record the actual installed package
versions and security-policy errors. Model/API availability and supported
`think=false` must be verified. Never substitute a hosted provider or silently
change the model. A fallback model requires a separately named experiment.

## Readiness and hardware smoke test

After separately approved setup, verify real embedding import/inference and
separate NumPy indexes, then run the existing ten-question hardware-only smoke
test. Its scripted questions are not reviewed correctness ground truth.
Use one inference request at a time, a modest context window and short outputs.
Record attempted and confirmed-completed generations separately, errors, model
digest, token counts and timings when available.

Label a request cold/warm only when observed residency supports that description.
Record requested CPU settings separately from observed model residency/VRAM.
Do not equate a model file or Ollama residency size with process peak RAM.
Unknown RAM/GPU/peak-memory observations stay unknown. If Windows policy blocks a
runtime, preserve the error and stop that execution path; keep Smart App Control
enabled. Complete source/dataset work independently and report live work pending.

## Controlled experiments

1. **Corpus effect:** hold one model/prompt/retrieval configuration fixed while
   comparing the full same case set against before/after snapshots. Judge each
   answer against its snapshot-specific expectation. The initial added-v1 pair is
   constructed corpus assembly; it does not establish an observed upstream edit.
2. **Retrieval comparison:** run basic semantic retrieval and the same pipeline
   with explicit version filtering. Change only that setting. Ten cases across
   two snapshots and two configurations produce 40 planned answer records per
   repetition. Retain every planned record, including index/service errors.
3. **Variability:** predeclare `pydantic-serialization`, `pydantic-optional` and
   `pydantic-union` as the first fixed case/family subset before running.
   Run three repetitions for both snapshots/configurations: 36 planned records.
   Do not choose the subset after observing interesting failures. Bypass answer
   caching; record `answer_cache_used=false`. Index reuse is a separate concern.

The current batch runner orders basic before version-filtered and before before
after within each case. Record that order. Cold starts, model loading and other
order effects prevent a causal latency-improvement claim from this schedule alone.
If a later experiment counterbalances order, record its schedule as a distinct
protocol revision. Do not change labels or settings to disguise an earlier run.

A previously wrong answer that remains wrong is not a newly introduced
regression. Different wording is not proof of a semantic change. Repeated failures
can support a reproducible observation; one changed output does not isolate a
causal mechanism. Cite traces for suspected causes and describe alternatives,
including general model weakness, retrieval omissions and generation variability.

## Judgments and independent tool assessment

Use deterministic checks for malformed responses, absent supplied citations and
incompatible citation versions. Mechanical success never establishes semantic
correctness. Review correctness/support manually; classify abstentions explicitly
when appropriate. A source removal may require evidence-only abstention without
making the old fact false. Legitimate v1/v2 differences are not same-version
source conflicts.

Store human answer reviews against exact run/trace/case/expectation bindings.
Keep stale history visible and exclude stale records from current judgments.
Derive the seven comparison statuses from per-snapshot judgments and reviewed
expected relations. Failure to adopt an expected change needs an explicit,
supported retained-old-behavior classification, not an arbitrary later failure.

Testing-tool precision/recall requires separately assessed, hash-bound reference
annotations. Do not recycle the operational answer judgment or the mechanical
flag into its own ground truth. A reference may disagree with a flag. The same
person can perform a separate reference procedure; document exposure to flags
and do not imply another person, blinding or authenticated identity. Leave these
metrics unavailable when eligible reference labels do not exist.

## Report every denominator

Separate assistant measures from testing-tool measures. Show planned/recorded/
missing records, run errors, unresolved reviews, review coverage and eligibility
exclusions. Report resolved-human-judgment accuracy alongside confirmed-correct
answers over **all planned reviewed-case records**, retaining errors and unknowns
in that conservative denominator. Missing ground truth yields null, not zero or
an inferred pass. Wrong-version/unsupported classifications must state their
diagnostic basis; a primary failure label is not an exhaustive causal audit.

Preserve full answers, exact recorded request passages, citations, prompts,
retrieval exclusions/settings, source/snapshot IDs, model/digest, timing/errors,
retries and available token statistics. Report pipeline latency separately from
isolated model time and cold/warm observations. Preserve raw run JSON and the
self-contained escaped HTML report alongside source/configuration evidence.

Keep genuine source-revision experiments, constructed source assembly, injected
fault tests, fixture replays and live inference in distinct result groups. The
first Pydantic assembly remains constructed even when its excerpts are genuine
and its model calls are real. Corpus scope, provenance and inference origin are
different properties. Live origin and reviewer identities in imported files are
recorded claims, not authenticated provenance.

## Development, held-out data and claims

Use the first ten families only for development. Reserve new held-out families
before final prompt/threshold decisions; do not split related paraphrases or
move exposed development families into the held-out set. Freeze settings before
held-out runs and retain an honest count of unfinished reviews. Do not invent
forty held-out labels to reach the sixty-case target.

Publish actual observations and limitations, including no improvement or blocked
runtime outcomes. A small curated study supports statements about those tested
cases, not industry prevalence, commercial demand or production readiness.
