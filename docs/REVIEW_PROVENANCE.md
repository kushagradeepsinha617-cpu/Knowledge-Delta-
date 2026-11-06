# Approval and review provenance

## The user-authorized workflow change

On 2026-11-07 the project owner authorized all cases and asked the agents to
continue without further case-approval questions. This is blanket authorization
to use the definitions and expected relations. It is not evidence that a person
read each question, source passage, rubric or generated answer.

Keep these distinct:

| Record | What it establishes | What it does not establish |
| --- | --- | --- |
| Blanket owner approval | Permission to use the exact approved study inputs and proceed | An item-specific human read-through or correct model answers |
| Agent source check | Recorded agent inspection of the question, scope, passages, expectations and rubric | Independent human ground truth or authenticated reviewer identity |
| Item-specific human definition review | An actual human decision on identified case definitions and expectations | Approval of future model outputs |
| Human answer judgment | An actual decision bound to one exact answer, evidence trace and expectation | A judgment of another run or a representative population estimate |
| Mechanical check | A justified schema, citation-membership or version-applicability observation | Semantic support or full answer correctness |

The 60-case study contains 20 development and 40 held-out cases. At this change,
11 definitions have item-specific human reviews and 49 remain drafts in their
case schema. One expected relation has an item-specific human review; 59 do not.
Preserve those original records. The earlier four human answer judgments belong
to one original development run and family. Do not transfer them to fresh runs.

## Separate owner-approval ledger

Use a separate ledger for the amended execution gate. This document specifies
the policy; it does not itself create an approval ledger or make the runner pass.
The ledger and runner must be implemented and verified before execution.

The ledger must record the actual blanket instruction's scope, the recording
time, and a basis identifying blanket owner approval rather than individual
human review. For every one of the 60 cases, bind:

- The bundle path, case ID and semantic family/split.
- The exact dataset hash, case hash and expected-relation hash.
- Both snapshot identifiers.
- The actual agent source-check status and basis, including unresolved caveats.

Do not label an unchecked item as agent-checked merely because the owner approved
the batch. If a source check finds a material ambiguity, resolve it from evidence
or retain the uncertainty explicitly; authorization cannot make a source support
an assertion. Preserve genuine upstream revisions separately from constructed
corpus transformations and disclose unknown release applicability.

The execution gate must reject missing, duplicate, stale or foreign entries and
unresolved material source-check failures. It must bind the complete ledger into
the frozen protocol and recheck it with source and configuration identities.
Changing a case or expectation requires a new binding; the script must not
silently reinterpret an earlier record. A blanket approval does not authorize
changing labels after seeing held-out outcomes to improve results.

## Labels, denominators and claims

Use wording such as **60 owner-approved definitions, including 11 item-specifically
human-reviewed and 49 agent-checked drafts**, only after the ledger and checks
actually support those counts. Report relation review counts separately. Do not
call the dataset "60 human-reviewed cases" or claim independent review.

Keep `case.review` and relation review bases truthful. Do not change 49 drafts to
`human_reviewed`, invent reviewer names/timestamps, or convert an agent assessment
into a human judgment to bypass an existing metric gate. Human-ground-truth
accuracy remains restricted to the cohorts and exact judgments its schema
qualifies. Owner-approved drafts and agent assessments require separate labels;
missing eligible judgments remain unavailable or unresolved.

Report all 240 planned main records and 36 separate development variability
records, including missing records, errors and policy abstentions. Those planned
records are not a promise of 276 model calls or 276 correct answers. In particular,
empty evidence-removal snapshots exercise a policy abstention without generation.

Show review coverage and each metric's numerator/denominator. Mechanical failure
flags are not a semantic accuracy score. Agent analysis may explain suspected
causes but must not supply hidden benchmark ground truth. Failure-flag precision
and recall need separate qualifying reference annotations; leave them unavailable
when those annotations do not exist.

Held out means the case families were withheld from project tuning. It does not
mean unseen source documents, unknown model pretraining, independent authorship,
or blind review. Freeze before held-out inference and preserve failures rather
than tuning and presenting a later run as the original held-out evaluation.

## Completion and public presentation

The owner changed the approval procedure, not the required execution accounting,
reproducible setup/build, or portfolio deliverables. Keep those requirements in
[MILESTONE_5.md](MILESTONE_5.md). Finish the study, reports and demo with the review
provenance visible; do not describe the original 60-item human-review target as
achieved through blanket authorization.
