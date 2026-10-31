"""Immutable snapshots. Source URLs are provenance only and never fetched."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath

from .validation import (ValidationError, digest, fields, nullable_text,
                         read_json, schema_version, sequence, text)


@dataclass(frozen=True)
class Document:
    document_id: str
    path: str
    source_reference: str
    source_revision: str | None
    software_versions: tuple[str, ...]
    title: str
    content: str
    content_hash: str
    metadata_hash: str


@dataclass(frozen=True)
class Snapshot:
    name: str
    domain: str
    default_version: str | None
    provenance: str
    documents: tuple[Document, ...]
    snapshot_id: str

    def document(self, document_id):
        for document in self.documents:
            if document.document_id == document_id:
                return document
        raise ValidationError(f"{self.name}: unknown document ID {document_id}")


def document_path(root, value):
    text(value, "document.path")
    if (value.startswith("/") or "\\" in value or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or PurePosixPath(value).suffix.lower() not in (".md", ".txt")):
        raise ValidationError(f"unsafe or unsupported document path: {value}")
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT")
                    for number in "123456789¹²³")
    for part in value.split("/"):
        if (part.endswith((".", " ")) or part.split(".")[0].upper() in reserved
                or any(ord(char) < 32 or char in '<>"|?*' for char in part)):
            raise ValidationError(f"unsafe Windows document path: {value}")
    candidate = root
    for part in value.split("/"):
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValidationError(f"symlink document paths are unsupported: {value}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValidationError(f"document path escapes snapshot root: {value}")
    return resolved


def parse_snapshot(raw, root, read_bytes=None):
    """Validate a manifest, read local UTF-8 files, and compute identity.

    read_bytes is injectable for isolated unit tests. Production uses Path.read_bytes.
    """
    try:
        root = Path(root).resolve()
    except (OSError, RuntimeError) as exc:
        raise ValidationError(f"cannot resolve snapshot root {root}: {exc}") from exc
    fields(raw, ("schema_version", "name", "domain", "default_version",
                 "provenance", "documents"), "snapshot")
    schema_version(raw["schema_version"], "snapshot")
    name = text(raw["name"], "snapshot.name")
    domain = text(raw["domain"], "snapshot.domain")
    default = nullable_text(raw["default_version"], "snapshot.default_version")
    from .validation import choice
    provenance = choice(raw["provenance"], ("constructed", "genuine"), "snapshot.provenance")
    documents = []
    ids, paths = set(), set()
    for item in sequence(raw["documents"], "snapshot.documents"):
        fields(item, ("document_id", "path", "source_reference", "source_revision",
                      "software_versions", "title"), "document")
        identity = text(item["document_id"], "document.document_id")
        relative = text(item["path"], "document.path")
        if identity in ids or relative.casefold() in paths:
            raise ValidationError(f"duplicate document ID or path: {identity}, {relative}")
        ids.add(identity)
        paths.add(relative.casefold())
        reference = text(item["source_reference"], "document.source_reference")
        revision = nullable_text(item["source_revision"], "document.source_revision")
        title = text(item["title"], "document.title")
        versions = [text(v, "software_versions item")
                    for v in sequence(item["software_versions"], "document.software_versions")]
        if len(set(versions)) != len(versions):
            raise ValidationError(f"{identity}: duplicate software versions")
        versions = tuple(sorted(versions))
        try:
            path = document_path(root, relative)
        except (OSError, RuntimeError) as exc:
            raise ValidationError(f"{identity}: cannot resolve document path {relative}: {exc}") from exc
        try:
            content_bytes = read_bytes(path) if read_bytes else path.read_bytes()
            content = content_bytes.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValidationError(f"{identity}: cannot read UTF-8 document {relative}: {exc}") from exc
        metadata = {"source_reference": reference, "source_revision": revision,
                    "software_versions": versions, "title": title}
        documents.append(Document(identity, relative, reference, revision, versions,
                                  title, content, sha256(content_bytes).hexdigest(),
                                  digest(metadata)))
    documents.sort(key=lambda document: document.document_id)
    identity_data = {
        "schema_version": 1, "domain": domain, "default_version": default,
        "provenance": provenance,
        "documents": [{"document_id": d.document_id, "content_hash": d.content_hash,
                       "metadata_hash": d.metadata_hash} for d in documents],
    }
    return Snapshot(name, domain, default, provenance, tuple(documents), digest(identity_data))


def load_snapshot(manifest):
    manifest = Path(manifest)
    return parse_snapshot(read_json(manifest), manifest.parent)
