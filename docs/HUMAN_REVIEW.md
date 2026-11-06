# Human review required for Milestone4

The implementation runs locally and the operational experiments are recorded.
No agent can provide the missing human judgments. This page identifies the
remaining decisions without marking any case or answer reviewed automatically.

## Case definitions

All ten Pydantic2.10.6 development case definitions have now been explicitly
reviewed in chat, including validator-error, regex and settings on2026-11-06.
The questions, both expectations, source passages and rubrics are recorded in
`examples/pydantic/cases.json`. Both snapshots retain the requested2.10.6
version; adding v1 material does not change the question's meaning.

The separate case in `examples/pydantic-revision/cases.json` is entirely draft.
Read its README and complete selected GenericModels sections before deciding
whether the proposed earlier evidence-only abstention is justified. The actual
warning addition is verified; released-software applicability is unknown.
Do not convert nominal mainline version metadata into a verified release claim.

## Actual answer review

The main256-token report contains40actual answers:28records from the seven
reviewed cases and12from the three drafts. All40lack resolved human judgments.
Two have automatic citation-version failure flags; these are not independently
reviewed correctness labels. The genuine-revision diagnostic has four more
unreviewed records and a draft case.

For each reviewed answer, inspect the requested context, exact supplied evidence,
answer, citations, expected behavior and rubric. Record pass, fail or unresolved
with a rationale; distinguish unsupported facts, wrong-version answers and
appropriate/unnecessary abstention where justified. Do not approve a result
merely because it contains a keyword or valid JSON.

Use the local web interface's saved-run import/manual review workflow, or inspect
the hash-bound CLI review form. The following command performs inspection only:

```powershell
& .\.venv\Scripts\python.exe -B scripts/review_fixture.py --run runs/pydantic-live-main-256.json --before examples/pydantic/before/manifest.json --after examples/pydantic/after/manifest.json --dataset docs/evidence/milestone4-output-cap-256/cases-at-run.json --relations docs/evidence/milestone4-output-cap-256/relations-at-run.json --case-id pydantic-equality --configuration basic --slot after
```

The frozen cases/relations preserve the labels that existed when the run was
made. New case approvals change dataset identity; do not rewrite old runs or
silently grade them against a different dataset revision. Keep the recorded
review binding and revision when explicitly saving an actual human decision.

## Report reviewed findings

Reviewing all40main answers is preferable. If reviewing a subset, declare the
selection rule, selection timing, scope and denominator; do not present that
subset as representative or held-out. No held-out families were invented or
silently moved out of development.

Failure-flag precision/recall requires separately attested reference annotations.
The same person may supply them under the documented separate procedure, with
exposure to existing flags disclosed. Otherwise leave those metrics unavailable.

After actual judgments exist, regenerate reports and document measured
correctness, abstention, errors, unresolved cases and limitations. The current
60-reviewed-case goal remains a target, not a claim that60reviews happened.
