"""Compare independently loaded snapshots by stable document identity."""
from .validation import ValidationError


def compare(before, after):
    if before.domain != after.domain:
        raise ValidationError("snapshots must belong to the same software domain")
    old = {d.document_id: d for d in before.documents}
    new = {d.document_id: d for d in after.documents}
    changes = []
    for identity in sorted(old.keys() | new.keys()):
        left, right = old.get(identity), new.get(identity)
        if left is None:
            kind, content_changed, metadata_changed = "added", False, False
        elif right is None:
            kind, content_changed, metadata_changed = "removed", False, False
        else:
            content_changed = left.content_hash != right.content_hash
            metadata_changed = left.metadata_hash != right.metadata_hash
            if not (content_changed or metadata_changed):
                continue
            kind = "modified"
        changes.append({
            "document_id": identity, "kind": kind,
            "content_changed": content_changed, "metadata_changed": metadata_changed,
            "before": None if left is None else {
                "content_hash": left.content_hash, "metadata_hash": left.metadata_hash},
            "after": None if right is None else {
                "content_hash": right.content_hash, "metadata_hash": right.metadata_hash},
        })
    metadata_changes = {}
    for key in ("default_version", "provenance"):
        left, right = getattr(before, key), getattr(after, key)
        if left != right:
            metadata_changes[key] = {"before": left, "after": right}
    return {"schema_version": 1, "before_snapshot_id": before.snapshot_id,
            "after_snapshot_id": after.snapshot_id, "domain": before.domain,
            "snapshot_metadata_changes": metadata_changes, "document_changes": changes}
