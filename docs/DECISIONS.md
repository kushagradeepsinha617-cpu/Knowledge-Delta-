# Engineering decisions

## 001: Small stdlib core first

Foundation has no runtime dependencies. Python 3.11+ is the proposed floor;
only Python 3.15.2 has been exercised. pytest is a test extra; inference/UI packages
wait until their milestone. No speculative full ML lockfile is presented.

## 002: Identity differs from content

Human-assigned document IDs survive edits and path moves. Exact UTF-8 bytes
determine content hashes; even line-ending changes count as content changes.
Relevant source/version/title metadata has a separate hash. Full definitions:
SCHEMAS.md. .gitattributes requests LF checkout to keep shipped fixture IDs stable.

Snapshot display names and storage paths do not affect snapshot identity.
Default version and provenance do. This is an explicit identity contract;
changing it requires a schema/pipeline revision.

## 003: Independent immutable snapshots

Each manifest lists its Markdown/text files explicitly. Loaded records are frozen
dataclasses containing tuples and strings. A separate snapshot cannot mutate one
already loaded. Future indexes will be separate rebuilds, not claimed connector
incremental-update tests.

Paths reject traversal, unsupported suffixes, symlink components, Windows device
aliases and unsafe path components. This is input hygiene, not a race-proof
filesystem security boundary against an adversarial local process.

## 004: Gold data is separate

Cases live outside snapshot document roots and cannot be ingested as JSON source
documents. Validate dataset snapshot IDs and exact evidence quotes up front.
The expected requested version is stored once per case. Version scopes are exact
labels, not inferred semantic version ranges. Empty version lists mean unknown.

## 005: No semantic grading shortcut

M1 validates gold inputs only. A schema-valid case is not a correct answer or a
human-reviewed case. Rubrics need future human review. No embedding similarity
threshold or keyword occurrence is used to grant correctness.

## 006: Delivery and evidence boundaries

The user approved a single-folder local source/test setup with a 250 MB ceiling;
no global installations or intentional writes outside that folder.
Each GitHub publication needs explicit approval. Read-only inventory does not
establish complete host state. Actual source-run verification is now recorded in VERIFICATION.md.

Interview concept: stable document identity lets us tell a modification from a
delete-plus-add; content-addressed snapshot identity lets us bind a test dataset
to exactly the evidence it was designed to assess.

## 007: Source-run verification under the network sandbox

Existing Python/Git outside PATH were found before downloading another runtime.
PyPI downloads were blocked. Official pytest dependencies were explicitly staged
from recorded source revisions and licenses; generated release-version metadata
was labeled separately. The initial isolated source run passed 52 tests and real CLI checks;
the later adversarial audit is recorded separately in MILESTONE_1_AUDIT.md.
Normal pip installation/build and other Python versions remain unverified.

Test dependencies and the environment stay ignored under .tools/.venv.
The source manifest binds evidence to executed code/configuration/fixtures.
This setup is a verification workaround, not a new application dependency system.

## 008: Verification must prove execution and preserve current failures

The adversarial audit exposed stale-success and inherited pytest override gaps.
The runner now records run IDs and setup/command/timeout errors, validates real
JUnit execution and counts, locks concurrent evidence writers, and writes passed
status only after matching artifacts. Dependency hashes use checked-in test pins.
Windows locking was exercised; POSIX locking remains unverified.

## 009: Keep local inventory and file ingestion bounded

Inventory redirects are rejected, response size is capped at 1 MiB, and model
fields are validated. Production documents must be regular files; Windows
reserved aliases and parser resource errors have explicit handling. These are
foundation safeguards, not a production security certification.


## 2026-11-05: Milestone 4 sources and approved local runtime limits

Use pinned MIT Pydantic docs with separate source-material and snapshot-assembly
provenance. The first ten-case batch adds old-version documentation as a controlled
distractor; it does not demonstrate a naturally observed upstream regression.
One case has actual user review; agent review does not promote the others.

The user approved 12 GB total project storage and 5 GB additional artifact payload
including retries (at most 1 GB CPU embedding dependencies), superseding earlier
UI-only limits for explicit model setup. Require exact compatibility/hash/space
checks before downloads. Keep Smart App Control On. Agent-shell metadata access
failed with WinError 10013; use the normal-terminal preflight and inspect its
report. Do not mistake resource approval for runtime compatibility.
