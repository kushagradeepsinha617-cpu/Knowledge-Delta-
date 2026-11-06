# Actual human case reviews

2026-11-05 04:47 UTC: project user explicitly selected “Reviewed and approve this
one case” for pydantic-serialization after being shown the fixed requested
version, question, both expected answers, deprecation/removal rubric and pinned
source link. The other nine cases were not approved. No assistant outputs or
relations received human judgments. Draft relation hashes were rebound to this
new dataset revision before any live run; no prior live result was rewritten.

2026-11-05: project user separately selected “Reviewed and approve this case”
for pydantic-optional, pydantic-union and pydantic-number-string. Each review
request displayed the fixed version/question, both expectations, source claim,
rubric and pinned source link. Total: four reviewed cases, six drafts. No actual
assistant answer or expected-relation annotation received a human judgment.
Draft relation hashes were rebound before live measurement; old fixture reports
retain their original dataset hashes and review counts.

2026-11-05: project user separately approved pydantic-orm, pydantic-equality
and pydantic-dict-pairs after each question, both expectations, source claim,
rubric and pinned source link were presented. Total: seven reviewed cases,
three drafts. No actual assistant answer or relation annotation was graded.

2026-11-06: user separately approved pydantic-validator-error, pydantic-regex
and pydantic-settings after each question, both expectations, rubric and pinned
source were presented. Total: ten human-reviewed case definitions, zero drafts.
No actual answer or relation annotation was reviewed by these approvals.
Earlier live runs retain their original7-reviewed/3-draft dataset identity.
Frozen cases and relations are preserved in the output-cap evidence directory;
old raw runs are not rewritten. Current draft relation hashes were rebound only
for the newly reviewed dataset revision.
