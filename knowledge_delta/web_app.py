"""Local browser interface using only the standard library and existing workflow."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import secrets
import sqlite3
import threading
from urllib.parse import urlsplit

from .review_store import ReviewConflict
from .review_workflow import ReviewSession
from .validation import ValidationError, digest, _unique_object, _reject_constant
from .workflow import export_report

ASSETS = Path(__file__).with_name("web_assets")
MAX_BODY = 2 * 1024 * 1024
MAX_RESPONSE = 32 * 1024 * 1024
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
REPORT_CSP = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
DEFAULT_INPUTS = {"before": "examples/mvp/before/manifest.json", "after": "examples/mvp/after/manifest.json",
    "dataset": "examples/mvp/cases.json", "relations": "examples/mvp/relations.json",
    "run_path": None, "reference_labels": None, "simulate_judgments": False}


def load_inputs(value):
    if not isinstance(value, dict) or set(value) - set(DEFAULT_INPUTS):
        raise ValidationError("Unknown input fields")
    result = dict(DEFAULT_INPUTS, **value)
    for name in DEFAULT_INPUTS:
        if name == "simulate_judgments":
            if type(result[name]) is not bool:
                raise ValidationError("Simulated judgment selection must be boolean")
        elif result[name] is None and name in ("run_path", "reference_labels"):
            continue
        elif not isinstance(result[name], str) or not result[name].strip() or len(result[name]) > 4096:
            raise ValidationError("Choose a nonempty project-local input path")
    return result


class Application:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.csrf = secrets.token_urlsafe(32)
        self.inputs = None
        self.exports = {}
        self.lock = threading.RLock()

    def session(self):
        if self.inputs is None:
            raise ValidationError("Load snapshot and case inputs first")
        # Reload trusted files for every action; stale forms must not grade edited inputs.
        return ReviewSession(self.root, **self.inputs)

    def state(self, session=None):
        with self.lock:
            state = {"csrf": self.csrf, "loaded": self.inputs is not None,
                "readiness": {"interface": "Python standard library", "python": platform.python_version(),
                    "model_inference": "Not requested; local model acceptance remains unverified",
                    "downloads": "None on startup"}, "defaults": DEFAULT_INPUTS}
            if self.inputs is None:
                return state
            session = session or self.session()
            evaluation = session.evaluate()
            latest = session.store.latest("answer", session.run["run_id"])
            for row in evaluation["rows"]:
                for detail in row["snapshots"].values():
                    detail["review_form"] = None
                    if detail["judgment"]["outcome"] == "run_error":
                        continue
                    bound = detail["judgment"]["binding"]
                    subject = digest(bound["result_key"])
                    detail["review_form"] = {"subject": subject, "binding_hash": digest(bound),
                        "revision": latest[subject]["revision"] if subject in latest else 0}
            relation_forms = {case_id: {key: value for key, value in session.relation_info(case_id).items()
                if key in ("subject", "binding_hash", "revision")} for case_id in session.cases}
            state.update(evaluation=evaluation, notice=session.notice, inputs=self.inputs,
                relation_forms=relation_forms, snapshots=[{"slot": slot, "name": snapshot.name,
                    "default_version": snapshot.default_version, "documents": len(snapshot.documents),
                    "snapshot_id": snapshot.snapshot_id} for slot, snapshot in session.snapshots.items()])
            return state

    def action(self, route, body):
        if not isinstance(body, dict):
            raise ValidationError("Expected a JSON object")
        with self.lock:
            extra = {}
            session = None
            if route == "/api/load":
                selected = load_inputs(body)
                # Validate before replacing a previously usable selection.
                session = ReviewSession(self.root, **selected)
                session.evaluate()
                self.inputs = selected
                self.exports = {}
            elif route == "/api/review-answer":
                allowed = {"case_id", "configuration", "slot", "repetition", "outcome", "reviewer", "rationale",
                    "failure_kind", "abstention_judgment", "expected_binding_hash", "expected_revision"}
                if set(body) - allowed:
                    raise ValidationError("Unknown answer-review fields")
                session = self.session()
                session.save_answer(**body)
            elif route == "/api/review-relation":
                if set(body) - {"case_id", "relation", "reviewer", "rationale", "expected_binding_hash", "expected_revision"}:
                    raise ValidationError("Unknown expected-change fields")
                session = self.session()
                session.save_relation(**body)
            elif route == "/api/export":
                if set(body) != {"directory"} or not isinstance(body["directory"], str):
                    raise ValidationError("Choose an export directory inside the project")
                session = self.session()
                evaluation = session.evaluate()
                self.exports = export_report(self.root, body["directory"], evaluation)
                extra["files"] = self.exports
            else:
                raise ValidationError("Unknown interface action")
            return {"ok": True, "state": self.state(session), **extra}


def create_server(root, port=8501):
    app = Application(root)

    class Handler(BaseHTTPRequestHandler):
        server_version = "KnowledgeDelta/1"

        def log_message(self, *args):
            pass

        def valid_host(self):
            allowed = {f"127.0.0.1:{self.server.server_address[1]}", f"localhost:{self.server.server_address[1]}"}
            return self.headers.get("Host") in allowed

        def send_data(self, code, content, mime, *, report=False):
            if len(content) > MAX_RESPONSE:
                return self.send_json(413, {"error": "Selected run exceeds the local interface response limit"})
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", REPORT_CSP if report else CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, code, value):
            data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
            self.send_data(code, data, "application/json; charset=utf-8")

        def do_GET(self):
            if not self.valid_host():
                return self.send_json(403, {"error": "Use this interface's localhost URL"})
            route = urlsplit(self.path).path
            try:
                if route == "/api/state":
                    return self.send_json(200, app.state())
                static = {"/": ("index.html", "text/html; charset=utf-8"),
                    "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
                    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8")}
                if route in static:
                    name, mime = static[route]
                    return self.send_data(200, (ASSETS / name).read_bytes(), mime)
                if route in ("/download/report.json", "/download/report.html"):
                    name = route.rsplit("/", 1)[1]
                    with app.lock:
                        target = Path(app.exports[name]) if name in app.exports else None
                        if target is None:
                            return self.send_json(404, {"error": "Export a report first"})
                        if target.is_symlink() or not target.resolve().is_relative_to(app.root):
                            raise ValidationError("Saved export no longer belongs to this project")
                        if target.stat().st_size > MAX_RESPONSE:
                            raise ValidationError("Saved export exceeds the local interface size limit")
                        content = target.read_bytes()
                    mime = "text/html; charset=utf-8" if name.endswith("html") else "application/json; charset=utf-8"
                    return self.send_data(200, content, mime, report=True)
                self.send_json(404, {"error": "Not found"})
            except (ValidationError, OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
                self.send_json(400, {"error": str(exc)})

        def do_POST(self):
            # Consume a bounded, non-streaming body before rejecting an action.
            # Closing with unread bytes can reset Windows TCP before the browser
            # receives the useful 403/415 response. Parsing still follows CSRF checks.
            try:
                if self.headers.get("Transfer-Encoding") is not None:
                    raise ValidationError("Streaming action bodies are unsupported")
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 <= length <= MAX_BODY:
                    return self.send_json(413, {"error": "Action is missing a length or exceeds 2 MiB"})
                self.connection.settimeout(10)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValidationError("Incomplete action body")
            except (ValidationError, OSError, ValueError) as exc:
                return self.send_json(400, {"error": str(exc)})
            if not self.valid_host():
                return self.send_json(403, {"error": "Invalid localhost host"})
            origin = self.headers.get("Origin")
            token = self.headers.get("X-KnowledgeDelta-Token", "")
            if (origin is not None and origin != "http://" + self.headers["Host"]
                    or self.headers.get("Sec-Fetch-Site") == "cross-site"
                    or not token.isascii() or not hmac.compare_digest(token, app.csrf)):
                return self.send_json(403, {"error": "Reload this local page before performing an action"})
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                return self.send_json(415, {"error": "Interface actions require JSON"})
            try:
                body = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
                self.send_json(200, app.action(urlsplit(self.path).path, body))
            except ReviewConflict as exc:
                self.send_json(409, {"error": str(exc)})
            except (ValidationError, OSError, ValueError, TypeError, KeyError, RecursionError, sqlite3.Error) as exc:
                self.send_json(400, {"error": str(exc)})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.app = app
    return server
