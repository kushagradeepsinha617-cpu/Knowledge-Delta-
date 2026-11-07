# Milestone 5 — Final evaluation and portfolio packaging

The user consolidated all remaining project work into this milestone on
2026-11-07. The working application and exploratory results remain valid;
unfinished evaluation requirements are carried forward explicitly.

## 5A — Finish and verify the study runner

- Tighten main/variability planned, recorded and actual-row accounting before
  declaring an execution complete. Preserve raw records before rejecting a run.
- Verify model identity before and after generation and at stage boundaries.
- Retain review gates, frozen configuration/source checks, output containment,
  interruption reporting and fixture/live separation.
- Run meaningful regressions and the complete offline suite against final source.

Done when the exact source is verified and the acceptance checks pass, with
failed/interrupted verification history preserved separately.

## 5B — Record case-definition approval and review provenance

- Retain 60 Pydantic case definitions: 20 development and 40 held-out. Most
  snapshot changes are constructed from genuine sources; one source revision
  is an actual upstream documentation change.
- The user subsequently authorized all cases and continuation without further
  case-approval questions. Record that blanket owner approval separately from
  item-specific human review, using the policy in
  [REVIEW_PROVENANCE.md](REVIEW_PROVENANCE.md).
- Source-check both snapshot expectations, applicability, supporting passages,
  rubrics and expected relations. Agent checks remain agent checks; blanket
  authorization does not establish that a person read every case.
- Keep related families in the same split. Preserve the existing 11 approvals
  and their original snapshot pairs; do not rebind old runs to changed datasets.
- Distinguish genuine documentation revisions from constructed corpus changes.

At this policy change, the inventory has 60 prepared definitions, 11 with
item-specific human review and 49 schema drafts; one expected relation has an
item-specific human review and 59 do not. Those counts must not be silently
rewritten. The new held-out cases span 22 semantic families. Existing Widget
fixtures do not count toward this Pydantic study.

The amended execution gate requires a separate, validated owner-approval ledger
covering all 60 exact case definitions and relations, supported by recorded agent
source checks. Bind its identity into the frozen protocol. Until that mechanism
is implemented and verified, the earlier human-review gate still blocks a run.
This amendment permits execution; it does not achieve the original target of 60
item-specifically human-reviewed definitions. Case approval never grades a model
answer, and draft cohorts remain distinct in correctness metrics.

## 5C — Freeze, execute and assess the experiments

- Freeze datasets, source/configuration identities, model digest and experiment
  order before the held-out run. Do not tune on held-out outputs.
- Execute both snapshots and retrieval configurations: 240 planned main answer
  records across 60 cases. Run the fixed development variability subset separately:
  36 planned records. Policy abstentions are not model inference calls.
- Retain raw answers, exact evidence, malformed responses, timings, errors and
  missing records. Record interrupted execution rather than implying completion.
- Assess actual answers to support the final findings, recording whether each
  assessment is human, agent-assisted or mechanical. Existing human answer
  judgments stay bound to their original runs and cannot be copied to new runs.
  Full human coverage remains unachieved unless actual qualifying judgments
  exist. Keep unresolved records visible and never call agent grading or blanket
  owner approval a fully human-graded benchmark.
- Separate assistant measures from testing-tool measures. Independent-reference
  precision/recall remains unavailable without a separate qualifying assessment.
- Export reproducible JSON/HTML reports and actual results with denominators.

Formatting controls change whitespace only. Empty-after removal cases test the
evidence-only abstention policy. Held out means withheld from project tuning,
not unseen during model pretraining or independently authored by another person.

Done when the frozen experiments execute with complete accounting and the reported
findings are supported by recorded judgments and explicit review coverage.

## 5D — Verify reproducibility

- Check fresh local installation and package builds without automatic model
  downloads or global changes; use the existing resource/security constraints.
- Document supported Python/runtime versions and exact Windows setup/run/test
  commands. Preserve the standard-library UI and explicit local inference setup.
- Record compatibility failures and limits without implying cross-platform proof.

Done when a fresh isolated setup and a package build have been exercised for the
documented supported configuration, with actual commands and evidence recorded.
A failed or unverified supported setup/build remains an open item. Other Python
versions, operating systems and optional paths retain their explicit limits.

## 5E — Package the portfolio

- Final README, architecture explanation, dataset card and source attribution.
- Benchmark methodology, actual results, limitations and reproducible evidence.
- Screenshots, a 60–90 second demonstration script/video and a concise case study.
- Claims match the demonstrated results. Novelty, adoption, independent review and
  production readiness are not inferred from a working prototype.

Done when another developer can understand the project, follow its setup, inspect
the evidence and distinguish demonstrated findings from remaining uncertainties.

## Constraints and sequencing

Complete runner checks and the amended, hash-bound owner-approval/source-check
gate before the held-out freeze. Do not infer that gate is implemented merely
because it is described here. Actual answer assessment follows execution.
Packaging may proceed in parallel, but final claims must reflect the evidence
and the approval/review distinctions above.

Zero spending, project-local files, approved storage/download limits, localhost
services and Windows protection remain unchanged. No new model downloads are
authorized by this organizational change. Publishing a repository or posting a
showcase is separate from completing the technical work and deliverables.

## Verified completion evidence

- **5A:** The 324-file frozen source passed 583 offline tests. A post-run
  validation-only digest fix passed 589 tests; original model records were not
  altered. See [verification history](VERIFICATION.md).
- **5B:** The owner-approved ledger binds all 60 exact definitions and expected
  relations. Eleven cases and one relation have item-specific human review;
  the remaining draft labels were not promoted.
- **5C:** The 240/240 main records and 36/36 repeated records completed. Four
  main errors are retained. All main records have hash-bound, provisional
  AI-assisted assessment, while the new study has zero human answer judgments.
  [Final accounting](evidence/milestone5-analysis/final-study-report.json)
  reports 125 proposed pass, 95 fail, 16 unresolved and four errors; 24 of the
  proposed passes are deterministic policy abstentions. No human accuracy or
  independent testing-tool precision/recall is inferred.
- **5D:** The final core wheel, isolated offline pip install, installed CLI,
  packaged assets and fixture HTTP workflow passed in
  [the packaging receipt](evidence/milestone5-packaging/0085d125bf1b4f64b2b04b2b17300708.json).
  The final report also reproduced offline from frozen source/raw archives with
  matching JSON and HTML hashes in the
  [reproduction receipt](evidence/milestone5-study/offline-reproduction-receipt.json).
- **5E:** README, architecture, dataset card, result write-up, actual fixture
  screenshots, 60–90 second demo script, case study and a portable static
  portfolio package are prepared. A video is a separate, explicitly deferred
  capture; no video is claimed. The final published-tree audit is tracked in
  PLAN.md.
