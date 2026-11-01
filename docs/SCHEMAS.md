# Version 1 input contracts

All objects reject unknown/missing fields. JSON duplicate keys and nonstandard
NaN/Infinity are invalid. No type coercion. Nonempty strings cannot be whitespace.
Schema version must be integer 1, not a boolean. Decoder resource-limit errors
are reported as validation errors; limits depend on the Python interpreter.

## Snapshot manifest

Required: schema_version, name (display only), domain, default_version (string or
null), provenance (constructed/genuine), documents array.

Every document requires document_id, relative path (.md/.txt), source_reference,
source_revision (string/null), software_versions (unique strings; [] = unknown),
and title. Production documents must be regular UTF-8 files; reserved Windows
device aliases (including spaces before extensions) and symlink paths are rejected.
Source references are recorded, never fetched by the loader.
Document IDs and case-insensitive paths must be unique within each snapshot.

Canonical JSON: sorted object keys, separators comma/colon without whitespace,
UTF-8, non-ASCII preserved, no NaN. software_versions sorted as a set-like field.
content_hash = SHA256(exact file bytes), with UTF-8 required.
metadata_hash = SHA256(canonical {source_reference, source_revision,
software_versions, title}).
snapshot_id = SHA256(canonical {schema_version:1, domain, default_version,
provenance, documents:[{document_id,content_hash,metadata_hash}, ...]}).
Records sort by document_id. Display name and path are excluded.

Computed hashes are exposed by comparison outputs. Input manifests do not carry
self-reported hashes, avoiding circular IDs and stale hand-maintained hashes.
Documents may be empty or have unknown scope; downstream policy must surface this.

## Dataset

Required: schema_version, snapshot_ids {before, after}, cases (nonempty).
Bindings must equal the loaded snapshots' computed IDs. Each case:
- case_id, family_id, question
- target: explicit_version, snapshot_default, or unspecified
- requested_version: required nonempty string only for explicit_version, otherwise null
- expectations: exactly before and after
- category: behavior_change, wording_only, unrelated_change, other_version_added,
  evidence_removed, conflicting_sources, missing_evidence
- provenance: constructed/genuine; split: development/held_out
- review: {status: draft/human_reviewed, reviewer: string/null, scope: string/null}

Human-reviewed entries require reviewer and scope; this records supplied labels,
not verified identity or independent review. Families cannot cross splits.
Each expectation requires behavior (answer/abstain/conflict), answer (string/null),
rubric (nonempty), target_context (string/null), evidence array.
answer behavior needs an answer; abstain must have null answer.
answer/conflict needs support. Every evidence item is {document_id, quote};
the exact nonempty quote must exist in the corresponding snapshot.
For explicit/default targets, cited source applicability must explicitly contain
the target version. Unknown applicability is not silently assumed to match.
snapshot_default requires a default_version in both snapshots, even if abstaining.
The rubric determines semantic adequacy; schema checks do not prove a conflict.

The constructed sample contains draft rubrics only, seven cases and no human
reviews. Case categories describe intended test purpose, not observed failures.
