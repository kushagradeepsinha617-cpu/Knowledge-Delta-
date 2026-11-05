"""Readiness or explicit localhost UI startup; no downloads, models or pandas."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.web_app import ASSETS, create_server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--project-root", type=Path, default=ROOT,
                        help="Project-local alternate fixture copy, for isolated demonstrations")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    if not root.is_relative_to(ROOT.resolve()) or not root.is_dir() or not 0 <= args.port <= 65535:
        parser.error("Choose a project-local folder and a valid port")
    if sys.prefix == sys.base_prefix or not Path(sys.prefix).resolve().is_relative_to(ROOT.resolve()):
        parser.error("Use this repository's isolated Python")
    missing = [name for name in ("index.html", "app.css", "app.js") if not (ASSETS / name).is_file()]
    if not args.serve:
        print(json.dumps({"status": "ready_for_explicit_start" if not missing else "missing_interface_assets",
            "interface": "Python standard library", "missing_assets": missing, "downloads_performed": False,
            "models_started": False, "ui_started": False}, indent=2))
        return 0 if not missing else 2
    if missing:
        parser.error("Interface assets are missing")
    try:
        with create_server(root, args.port) as server:
            print(f"KnowledgeDelta: http://127.0.0.1:{server.server_address[1]}", flush=True)
            print("Local fixture/saved-run review. No model calls or downloads. Ctrl+C stops the server.", flush=True)
            server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        print(json.dumps({"status": "server_not_started", "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
