"""Strict structured-answer checks. Valid structure is not semantic correctness."""
from dataclasses import dataclass
import json

from .validation import ValidationError, fields, text


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: tuple[str, ...]
    abstained: bool


def response_schema(chunk_ids):
    items = {"type": "string"}
    if chunk_ids:
        items["enum"] = list(chunk_ids)
    return {
        "type": "object", "additionalProperties": False,
        "required": ["answer", "citations", "abstained"],
        "properties": {
            "answer": {"type": "string", "minLength": 1, "maxLength": 4000},
            "citations": {"type": "array", "items": items, "uniqueItems": True,
                          **({"maxItems": 0} if not chunk_ids else {})},
            "abstained": {"type": "boolean"},
        },
    }


def parse_answer(raw, supplied_chunks):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate answer key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValidationError(f"unsupported JSON constant: {value}")

    try:
        payload = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, RecursionError) as exc:
        raise ValidationError(f"malformed structured answer: {exc}") from exc
    fields(payload, ("answer", "citations", "abstained"), "answer")
    answer = text(payload["answer"], "answer.answer")
    if len(answer) > 4000:
        raise ValidationError("answer exceeds the configured response limit")
    if type(payload["abstained"]) is not bool:
        raise ValidationError("abstained must be a boolean")
    citations = payload["citations"]
    if not isinstance(citations, list) or any(not isinstance(value, str) for value in citations):
        raise ValidationError("citations must be an array of chunk-ID strings")
    if len(set(citations)) != len(citations):
        raise ValidationError("citation IDs must be unique")
    known = {chunk.chunk_id for chunk in supplied_chunks}
    if any(value not in known for value in citations):
        raise ValidationError("citation does not exist in the actual supplied context")
    if not payload["abstained"] and not citations:
        raise ValidationError("evidence-only answers require citations or explicit abstention")
    return Answer(answer, tuple(citations), payload["abstained"])


def citation_compatibility(answer, supplied_chunks, effective_version):
    """Mechanical trace flags only; do not remove wrong-version evidence/results."""
    by_id = {chunk.chunk_id: chunk for chunk in supplied_chunks}
    checks = []
    for identity in answer.citations:
        chunk = by_id[identity]
        status = "not_requested" if effective_version is None else (
            "unknown" if not chunk.software_versions else
            "compatible" if effective_version in chunk.software_versions else "incompatible")
        checks.append({"chunk_id": identity, "version_compatibility": status})
    return tuple(checks)
