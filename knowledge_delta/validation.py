"""Small strict schema helpers; no coercion or silent unknown-field loss."""
import json
from hashlib import sha256


class ValidationError(ValueError):
    """An actionable invalid project input."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return sha256(canonical(value)).hexdigest()


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label}: expected a nonempty string")
    return value


def nullable_text(value, label):
    if value is not None:
        text(value, label)
    return value


def fields(value, required, label, optional=()):
    if not isinstance(value, dict):
        raise ValidationError(f"{label}: expected an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise ValidationError(
            f"{label}: missing fields {sorted(missing)}; unknown fields {sorted(unknown)}")
    return value


def choice(value, choices, label):
    if not isinstance(value, str) or value not in choices:
        raise ValidationError(f"{label}: expected one of {sorted(choices)}")
    return value


def sequence(value, label):
    if not isinstance(value, list):
        raise ValidationError(f"{label}: expected a JSON array")
    return value


def schema_version(value, label):
    if type(value) is not int or value != 1:
        raise ValidationError(f"{label}: only integer schema_version 1 is supported")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def _reject_constant(value):
    raise ValidationError(f"nonstandard JSON constant is unsupported: {value}")
