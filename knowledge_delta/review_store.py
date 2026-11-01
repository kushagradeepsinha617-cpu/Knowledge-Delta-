"""Small append-only SQLite review journal with optimistic concurrency control."""
from datetime import datetime, timezone
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from .validation import ValidationError, canonical, choice, text


class ReviewConflict(ValidationError):
    """The displayed review changed before this edit was saved."""


class ReviewStore:
    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.path = (self.root / "runs/manual_reviews.sqlite3").resolve()
        if not self.root.is_dir() or not self.path.is_relative_to(self.root):
            raise ValidationError("Review database must remain inside the project folder")

    def _connect(self):
        if not self.path.resolve().is_relative_to(self.root):
            raise ValidationError("Review database path changed outside the project")
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.execute("PRAGMA temp_store=MEMORY")
        return connection

    def latest(self, kind, run_id):
        choice(kind, ("answer", "relation"), "review kind")
        text(run_id, "run_id")
        if not self.path.exists():
            return {}
        with closing(self._connect()) as db:
            rows = db.execute("SELECT e.id,e.subject,e.payload FROM events e JOIN (SELECT subject,MAX(id) id FROM events WHERE kind=? AND run_id=? GROUP BY subject) last ON last.id=e.id ORDER BY e.subject", (kind, run_id)).fetchall()
        return {subject: {"revision": revision, "payload": json.loads(payload)} for revision, subject, payload in rows}

    def append(self, kind, run_id, subject, payload, *, expected_revision=0):
        choice(kind, ("answer", "relation"), "review kind")
        text(run_id, "run_id")
        text(subject, "review subject")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValidationError("Expected review revision must be a nonnegative integer")
        if not isinstance(payload, dict) or payload.get("basis") != "human_review":
            raise ValidationError("Persisted manual reviews require an explicit human-review action")
        text(payload.get("reviewer"), "reviewer")
        text(payload.get("reviewed_at"), "reviewed_at")
        encoded = canonical(payload).decode("utf-8")
        if not self.path.resolve().is_relative_to(self.root):
            raise ValidationError("Review database path changed outside the project")
        if not self.path.exists() and expected_revision != 0:
            raise ReviewConflict("No stored review exists for the displayed revision. Reload before saving.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,run_id TEXT NOT NULL,subject TEXT NOT NULL,payload TEXT NOT NULL,recorded_at TEXT NOT NULL)")
            latest = db.execute("SELECT MAX(id) FROM events WHERE kind=? AND run_id=? AND subject=?", (kind, run_id, subject)).fetchone()[0] or 0
            if latest != expected_revision:
                raise ReviewConflict("This review changed in another session. Reload before saving.")
            cursor = db.execute("INSERT INTO events(kind,run_id,subject,payload,recorded_at) VALUES(?,?,?,?,?)",
                                (kind, run_id, subject, encoded, datetime.now(timezone.utc).isoformat()))
            revision = cursor.lastrowid
            db.execute("COMMIT")
            return revision
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def history(self, run_id):
        text(run_id, "run_id")
        if not self.path.exists():
            return []
        with closing(self._connect()) as db:
            rows = db.execute("SELECT id,kind,subject,payload,recorded_at FROM events WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [{"revision": revision, "kind": kind, "subject": subject, "payload": json.loads(payload),
                 "recorded_at": recorded_at} for revision, kind, subject, payload, recorded_at in rows]
