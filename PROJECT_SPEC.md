# KnowledgeDelta project specification

## Purpose and scope

A local tool that tests whether changes to software documentation cause incorrect
answers in an AI documentation assistant. The primary product is the testing and
evidence-review workflow; the reference RAG assistant is the experimental subject.
RAG retrieves source passages before generation.

Audience: developers maintaining software-documentation assistants.
Scope: English Markdown/text, one software domain, one local answering model,
small corpora. Commercial demand and novelty are unvalidated.

User context: intermediate developer, 10–15 hours/week, 1–2 months, user-reported
16 GB RAM. Assume CPU-only. Inference speed, GPU and RAM remain unverified. Free disk was measured; see
docs/evidence/milestone1/environment.json.

## Nonnegotiable constraints

- Zero spending: existing computer/internet/Codex access only. No paid APIs,
  hosting, rented hardware, subscriptions, credit purchases or card-based trials.
- The GitHub repository is the canonical project. The user later approved a
  local repository copy and isolated test setup entirely inside one folder,
  with a 250 MB ceiling, no global installation, and no intentional writes
  outside that folder. The verified copy is %TEMP%/Knowledge-Delta-.
  Models were not downloaded; later setup still follows explicit download steps.
- Deliverer requests explicit user permission before every push/API publication,
  with concrete changes and a commit justification. GO authorizes preparation;
  it does not waive this gate.
- Brain advises the implementation agent before technical questions are escalated.
  Human approval, human review, preferences and unavailable facts cannot be
  manufactured by an agent.
- Stop after Milestone 1; later milestones need user instruction.
- No repository visibility changes, external outreach or social posting.

## Workflow

Select snapshots A/B; load reviewed questions; run the full same question set on
both; save answers and exact retrieved passages; judge each snapshot against its
own expectation; derive comparison status; inspect evidence; export JSON and
self-contained escaped HTML. Automatic affected-question selection is deferred.

Every document has a stable ID, source reference/revision, explicit applicability
(or visibly unknown applicability), content hash and relevant metadata hash.
Each snapshot has a manifest and reproducible identity. Separate indexes are
rebuilt; this does not validate production incremental ingestion/deletion.

Cases include ID/family, fixed question and requested version, optional
snapshot-specific target context, separate expectations/evidence/rubrics,
category, provenance, split and review status. Current/default questions require
an explicit snapshot default version. Related cases stay in one split.
Gold answers/rubrics stay out of source indexes and model prompts.

Initial fixtures are constructed and labels are drafts. Milestone 3 targets
20 development cases. Later aim for 60 human-reviewed total, with 20 development
and 40 held out; no padding and no held-out tuning. Human review is a real
remaining task, not something model-generated labels can satisfy.

## Correctness and integrity

Support behavior changes, wording-only changes, unrelated changes, other-version
additions, evidence removal, source conflicts and missing evidence.
Old-version facts may remain correct. Changed wording is not automatically a
regression. Deleted evidence does not make facts false; abstention follows the
explicit evidence-only answering policy.

Store independent per-snapshot judgments and derive: pass, expected change,
failure to adopt change, previously correct/now incorrect, incorrect in both,
needs human review, or run error. Citation existence/version compatibility can
be mechanical; semantic support often needs human judgment. No keyword-only
semantic passes.

Keep constructed fixtures, injected faults, genuine source changes, replay
outputs and live inference distinct. Report raw counts, denominators, missing
judgments and run errors. Measure assistant correctness, version/evidence errors,
abstention and latency separately from evaluator precision/recall/review rate
where human labels exist. No invented results or market validation.

## Planned stack and operation

Python isolated environment; Ollama; qwen3:1.7b initial candidate, qwen3:0.6b only
after recorded resource/speed comparison; local all-MiniLM-L6-v2 embeddings;
NumPy search; JSON/JSONL, SQLite only if justified; Streamlit; pytest.
Verify compatibility before installing/pinning; record actual versions.
Foundation runtime uses only the standard library.

One generation at a time, short answers, modest context, thinking disabled where
supported by verified model/API. No hosted fallback. Bind local services to
localhost. Explicit setup/download commands; normal startup/tests must not
download. Offline ordinary use after setup. Missing models/services remain clear
errors; labeled doubles may unblock implementation.

Trace answer, cited chunk IDs, abstention, exact context, snapshot/config IDs,
model/digest, prompt/retrieval versions, timings/errors/retries and available token
counts. Validate structured output, bound retries, preserve malformed responses.
Respect embedding input limits; keep chunk/document/version/snapshot mappings.

Compare semantic retrieval with version-filtered retrieval holding other settings
fixed. Missing/ambiguous applicability stays visible. Cache identity includes
snapshot, question/context, model, prompt, retrieval and pipeline versions.
Repeated fixed-subset variability runs bypass answer caching.

## Milestones and acceptance

1. Foundation: spec/plan/setup guidance/readiness; snapshot/case schemas;
   constructed examples; document diff command; meaningful offline tests.
2. Local answering: chunks/embeddings/indexes, Ollama trace integration,
   ten-question hardware smoke test, two retrieval configurations.
3. MVP: 20 development cases, evaluation/manual review, Streamlit, JSON/HTML,
   live end-to-end inference if available.
4. Evaluation: verified licensed versioned sources (prefer Pydantic v1/v2),
   review/splits, held-out support, controlled experiments, variability/limits.
5. Portfolio: exact Windows instructions, architecture, dataset card, attribution,
   real benchmark evidence, demo script and case study with pending claims.

Full acceptance tests eventually cover identity/isolation, metadata/removals,
version filtering, expected changes/regressions, evidence removal, bad citations,
malformed responses, cache invalidation, no answer-key leakage, missing services
and fixture/live separation. M1 does not claim later-stage checks implemented.

At every milestone explain consequential decisions, evidence, limitations and an
interview concept. PLAN.md records checks actually run and remaining work.
