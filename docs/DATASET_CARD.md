# Dataset inventory (current)

- examples/constructed: original seven-case Widget foundation fixture.
- examples/mvp: twenty draft constructed Widget development cases.
- examples/pydantic: ten development cases using genuine pinned MIT
  Pydantic excerpts in a constructed corpus-addition experiment. See its README,
  sources.json and source licenses. Ten explicit human case reviews are recorded, with no
  held-out cases. Four actual answer judgments are now recorded separately for
  one assisted diagnostic family. The 128-token comparison, repeat subset
  and separate 256-token comparison now have actual local records and ungraded
  reports; see EXPERIMENT_RESULTS.md. Completion counts are not correctness.
  The older runs retain their original seven-reviewed/three-draft revision.
- examples/pydantic-revision: one approved development case from an actual pinned
  parent/child documentation revision, with an earlier draft diagnostic and a
  separate four-record run made after case approval. The
  source warning is a clarification; released-software applicability is unknown.
  Its case and relation were explicitly reviewed; new-run answer review is pending.
  No software-behavior-change claim is made.

The 60-reviewed-case target is not achieved. No held-out evaluation has occurred.
Keep related families together if expanding the dataset; development observations
must not be moved into held-out data or used to imply independent validation.

The original foundation card below is historical; its seven-case counts and
implementation-status statements do not describe the later application.

## Historical foundation card (preserved)

# Constructed dataset card

Domain: imaginary Widget software. All documentation and cases are constructed
for this repository; none are authoritative software advice.
No third-party documentation excerpts are bundled.

Two snapshots, seven draft development cases, zero human-reviewed cases,
zero held-out cases. Each requested version remains "1" across snapshots.
Cases cover all seven requested categories. Their small size is a foundation
example, not a benchmark or the eventual 20/60-case dataset.

The timeout changes within version 1 are deliberately constructed evidence
changes across source revisions, not a verified real release change.
One source has missing version metadata before a metadata correction.
The version-2 addition coexists with unchanged version-1 status evidence.
Two version-1 sources deliberately contradict each other about worker limits.
Removed export evidence makes the evidence-only expectation abstention, not a
claim that export files stopped existing.

Related cases remain in the development split. The two version-1 status-command
cases share family widget-status-v1, so a later split cannot separate them.
No prompts/thresholds or answering
models exist yet. No live outputs, empirical error rates or market conclusions
can be inferred from these cases.

Next: human review before correctness measurement; later add revision-pinned,
license-verified genuine Pydantic material and reserve independent held-out
families. A review workflow must record actual human review; agent approval
does not count as human dataset review.
