"""Inspect explicit model setup metadata; never install or download model bodies.

Default operation is offline. --online-metadata permits five bounded primary
metadata requests. A successful report is not an installer lock or approval.
"""
import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from knowledge_delta.embeddings import MODEL_REVISION, REQUIRED
from knowledge_delta.validation import read_json, ValidationError

URLS = {
    "ollama": "https://api.github.com/repos/ollama/ollama/releases/tags/v0.40.14",
    "qwen": "https://registry.ollama.ai/v2/library/qwen3/manifests/1.7b",
    "minilm": "https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2/tree/" + MODEL_REVISION + "?recursive=true",
    "cpu_torch": "https://download.pytorch.org/whl/cpu/torch/",
    "sentence_transformers": "https://pypi.org/pypi/sentence-transformers/json",
}
MAX_RESPONSE = 2_000_000
APPROVED_STORAGE = 12_000_000_000
APPROVED_TRANSFER = 5_000_000_000
CPU_DEPENDENCY_CAP = 1_000_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValidationError("Metadata redirect refused; inspect the primary URL")


def fetch_metadata(url):
    if url not in URLS.values():
        raise ValidationError("URL outside the explicit metadata request set")
    request = Request(url, headers={"User-Agent": "KnowledgeDelta-model-preflight/1",
                                   "Accept-Encoding": "identity"})
    with build_opener(NoRedirect).open(request, timeout=15) as response:
        if response.status != 200 or response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValidationError("Unexpected metadata response")
        length = response.headers.get("Content-Length")
        if length is not None and (not length.isdigit() or int(length) > MAX_RESPONSE):
            raise ValidationError("Oversized metadata response")
        data = response.read(MAX_RESPONSE + 1)
    if len(data) > MAX_RESPONSE:
        raise ValidationError("Metadata body exceeds bound")
    return data


def qwen_manifest(data):
    raw = json.loads(data)
    if raw.get("schemaVersion") != 2 or not isinstance(raw.get("layers"), list) or not raw["layers"]:
        raise ValidationError("Invalid Qwen registry manifest")
    parts = [raw["config"], *raw["layers"]]
    for part in parts:
        if (not re.fullmatch("sha256:[a-f0-9]{64}", part.get("digest", ""))
                or type(part.get("size")) is not int or part["size"] < 1):
            raise ValidationError("Invalid model-layer digest/size")
    return {"manifest_sha256": sha256(data).hexdigest(),
            "artifact_payload_bytes": sum(part["size"] for part in parts),
            "config": raw["config"], "layers": raw["layers"],
            "note": "Exact response hash recorded; tag is mutable. Reverify before pull."}


def minilm_assets(data):
    tree = json.loads(data)
    files = {item["path"]: item for item in tree if item.get("type") == "file"}
    required = [*REQUIRED, "README.md"]
    missing = [name for name in required if name not in files]
    if missing:
        raise ValidationError("Pinned MiniLM assets missing: " + ", ".join(missing))
    selected = []
    for name in required:
        item = files[name]
        if type(item.get("size")) is not int or item["size"] < 1:
            raise ValidationError("Invalid pinned asset size")
        selected.append({"path": name, "bytes": item["size"],
                         "git_blob_oid": item.get("oid"),
                         "lfs": item.get("lfs"),
                         "revision": MODEL_REVISION})
    return {"files": selected, "artifact_payload_bytes": sum(item["bytes"] for item in selected),
            "license_check": "Model card/license attribution must be inspected before distribution"}


class WheelLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(urljoin(URLS["cpu_torch"], href))


def cpu_candidate(data):
    from scripts.inspect_ui_setup import packaging_api
    _, Version, canonical, parse_wheel, tags, _ = packaging_api()
    tags = set(tags)
    parser = WheelLinks()
    parser.feed(data.decode("utf-8"))
    choices = []
    for url in parser.links:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in ("download.pytorch.org", "download-r2.pytorch.org"):
            continue
        filename = unquote(parsed.path.rsplit("/", 1)[-1])
        if not filename.endswith(".whl"):
            continue
        try:
            name, version, _, wheel_tags = parse_wheel(filename)
        except ValueError:
            continue
        if (canonical(name) == "torch" and version.local == "cpu"
                and not version.is_prerelease and tags.intersection(wheel_tags)
                and re.fullmatch("sha256=[a-f0-9]{64}", parsed.fragment)):
            choices.append((version, filename, url))
    if not choices:
        raise ValidationError("No compatible hashed CPU Torch wheel for this interpreter")
    version, filename, url = max(choices)
    return {"version": str(version), "filename": filename, "url": url,
            "sha256": urlsplit(url).fragment.removeprefix("sha256="),
            "dependency_closure_verified": False, "compressed_bytes": None,
            "expanded_bytes": None, "installed": False}


def inspect(fetch=fetch_metadata):
    record = {"schema_version": 1, "kind": "model_setup_metadata",
              "python": sys.version, "requests": [], "metadata_payload_bytes": 0,
              "artifact_downloads_performed": False, "models_installed": False,
              "native_execution_performed": False, "dependency_closure_verified": False,
              "installer_authorized_by_report": False,
              "limits": {"total_project_bytes": APPROVED_STORAGE,
                         "additional_artifact_bytes": APPROVED_TRANSFER,
                         "cpu_dependency_bytes": CPU_DEPENDENCY_CAP},
              "pending": ["Complete CPU dependency lock and expanded/temporary space plan",
                          "Native policy acceptance and runtime containment",
                          "Actual offline embedding and inference checks"]}
    for key, url in URLS.items():
        try:
            data = fetch(url)
            if not isinstance(data, bytes) or len(data) > MAX_RESPONSE:
                raise ValidationError("Metadata body exceeds bound")
            record["requests"].append({"key": key, "url": url, "bytes": len(data),
                                       "sha256": sha256(data).hexdigest(), "status": "received"})
            record["metadata_payload_bytes"] += len(data)
            if key == "qwen":
                record[key] = qwen_manifest(data)
            elif key == "minilm":
                record[key] = minilm_assets(data)
            elif key == "cpu_torch":
                record[key] = cpu_candidate(data)
            elif key == "ollama":
                release = json.loads(data)
                assets = [item for item in release["assets"] if item["name"] == "ollama-windows-amd64.zip"]
                if release["tag_name"] != "v0.40.14" or len(assets) != 1:
                    raise ValidationError("Unexpected Ollama release identity")
                item = assets[0]
                record[key] = {field: item.get(field) for field in
                               ("name", "size", "digest", "browser_download_url")}
            else:
                raw = json.loads(data)
                record[key] = {"candidate_version": raw["info"]["version"],
                               "requires_python": raw["info"].get("requires_python"),
                               "dependency_closure_verified": False}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            record["requests"].append({"key": key, "url": url, "status": "error",
                                       "error_type": type(exc).__name__, "error": str(exc)})
    record["status"] = ("metadata_inspected_setup_still_pending"
                        if not any(item["status"] == "error" for item in record["requests"])
                        else "metadata_partial_or_unavailable")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online-metadata", action="store_true")
    parser.add_argument("--output", default="runs/model-setup-inspection.json")
    args = parser.parse_args(argv)
    if not args.online_metadata:
        print(json.dumps({"status": "offline_plan", "metadata_urls": URLS,
                          "network_requests": 0, "models_installed": False,
                          "next": "Explicit --online-metadata reads bounded metadata only"}, indent=2))
        return 0
    output = (ROOT / args.output).resolve()
    if (not output.is_relative_to((ROOT / "runs").resolve())
            or not output.is_relative_to(ROOT) or output.suffix != ".json" or output.exists()):
        parser.error("Choose a new project-local runs/*.json report")
    record = inspect()
    record["inspector_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "output": str(output),
                      "requests": record["requests"], "models_installed": False}, indent=2))
    return 0 if record["status"] == "metadata_inspected_setup_still_pending" else 2


if __name__ == "__main__":
    raise SystemExit(main())
