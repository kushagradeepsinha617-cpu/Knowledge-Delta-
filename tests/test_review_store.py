"""Journal tests use invented TEST-ONLY authors; no actual human reviews are claimed."""
import sqlite3

import pytest

from knowledge_delta.review_store import ReviewConflict, ReviewStore
from knowledge_delta.validation import ValidationError


def payload(rationale="Test-only review fixture"):
    return {"basis": "human_review", "reviewer": "TEST-ONLY-REVIEWER", "reviewed_at": "2026-01-01T00:00:00+00:00", "rationale": rationale}


def test_review_read_is_lazy_and_revisions_preserve_history(tmp_path):
    store = ReviewStore(tmp_path)
    assert store.latest("answer", "test-run") == {} and not store.path.exists()
    first = store.append("answer", "test-run", "case-before", payload())
    second = store.append("answer", "test-run", "case-before", payload("Revised test-only rationale"), expected_revision=first)
    assert second > first
    assert store.latest("answer", "test-run")["case-before"]["revision"] == second
    assert [item["revision"] for item in store.history("test-run")] == [first, second]
    assert store.latest("answer", "other-run") == {}


def test_stale_session_cannot_overwrite_another_review(tmp_path):
    first, other = ReviewStore(tmp_path), ReviewStore(tmp_path)
    revision = first.append("answer", "run", "case", payload())
    with pytest.raises(ReviewConflict):
        other.append("answer", "run", "case", payload("Stale tab overwrite"), expected_revision=0)
    assert first.latest("answer", "run")["case"]["revision"] == revision
    assert len(first.history("run")) == 1


def test_fixture_labels_cannot_be_persisted_as_manual_human_reviews(tmp_path):
    store = ReviewStore(tmp_path)
    with pytest.raises(ValidationError, match="explicit human"):
        store.append("answer", "run", "case", {"basis": "fixture"})
    assert not store.path.exists()


def test_sql_subjects_are_parameters_not_executable_statements(tmp_path):
    store = ReviewStore(tmp_path)
    subject = "case'); DROP TABLE events; --"
    store.append("relation", "run", subject, payload())
    assert subject in store.latest("relation", "run")
    assert len(store.history("run")) == 1
