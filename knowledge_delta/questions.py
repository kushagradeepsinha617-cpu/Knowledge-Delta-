"""An answering-input contract deliberately separate from gold answers and rubrics."""
from dataclasses import dataclass

from .snapshots import Snapshot
from .validation import ValidationError, choice, nullable_text, text


@dataclass(frozen=True)
class QuestionInput:
    case_id: str
    question: str
    target: str
    requested_version: str | None
    target_context: str | None = None

    def __post_init__(self):
        text(self.case_id, "case_id")
        text(self.question, "question")
        choice(self.target, ("explicit_version", "snapshot_default", "unspecified"), "target")
        nullable_text(self.requested_version, "requested_version")
        nullable_text(self.target_context, "target_context")
        if (self.target == "explicit_version") != (self.requested_version is not None):
            raise ValidationError("explicit_version requires one fixed version; other targets require null")

    @classmethod
    def from_case(cls, case, slot):
        choice(slot, ("before", "after"), "snapshot slot")
        # Extract ONLY the explicitly declared target context from each slot.
        context = case["expectations"][slot]["target_context"]
        return cls(text(case["case_id"], "case_id"), text(case["question"], "question"),
                   choice(case["target"], ("explicit_version", "snapshot_default", "unspecified"), "target"),
                   nullable_text(case["requested_version"], "requested_version"),
                   nullable_text(context, "target_context"))

    def effective_version(self, snapshot: Snapshot):
        if self.target == "explicit_version":
            return text(self.requested_version, "explicit requested version")
        if self.requested_version is not None:
            raise ValidationError("only explicit_version may specify requested_version")
        if self.target == "snapshot_default":
            if snapshot.default_version is None:
                raise ValidationError("snapshot-default question has no declared default version")
            return snapshot.default_version
        if self.target != "unspecified":
            raise ValidationError("unsupported question target")
        return None


def select_applicable(chunks, effective_version, version_filter):
    """Return eligibility and visible reasons. Basic retrieval keeps incompatible sources."""
    if type(version_filter) is not bool:
        raise ValidationError("version_filter must be a boolean")
    selected, excluded = [], []
    for chunk in chunks:
        if version_filter and effective_version is not None:
            reason = "unknown_version_scope" if not chunk.software_versions else (
                "incompatible_version" if effective_version not in chunk.software_versions else None)
            if reason:
                excluded.append({"chunk_id": chunk.chunk_id, "reason": reason})
                continue
        selected.append(chunk)
    return tuple(selected), tuple(excluded)
