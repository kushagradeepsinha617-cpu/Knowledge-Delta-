# Engineering decisions

## 001: Small stdlib core first

Foundation has no runtime dependencies. Python 3.11+ is the proposed floor,
not a verified host installation. pytest is a test extra; inference/UI packages
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
was labeled separately. The isolated source run passed 52 tests and real CLI checks.
Normal pip installation/build and other Python versions remain unverified.

Test dependencies and the environment stay ignored under .tools/.venv.
The source manifest binds evidence to executed code/configuration/fixtures.
This setup is a verification workaround, not a new application dependency system.
