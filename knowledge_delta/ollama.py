"""Bounded localhost-only Ollama client; never pulls models or falls back to cloud."""
import json
from http.client import HTTPException
import math
import threading
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from .doctor import NoRedirects
from .responses import parse_answer
from .validation import ValidationError, digest, text

ALLOWED_MODELS = ("qwen3:1.7b", "qwen3:0.6b")
MAX_RESPONSE_BYTES = 1024 * 1024
_GENERATION_LOCK = threading.Lock()


class LocalServiceError(RuntimeError):
    def __init__(self, message, raw_body=None):
        super().__init__(message)
        self.raw_body = raw_body


def _read_body(response):
    try:
        return response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, HTTPException) as exc:
        partial = getattr(exc, "partial", b"")
        partial = partial[:MAX_RESPONSE_BYTES] if isinstance(partial, bytes) else b""
        raise LocalServiceError(f"Local API response body read failed: {exc}",
                                partial.decode("utf-8", errors="replace") or None) from exc


def _object(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("nonfinite JSON constant")
    try:
        result = json.loads(body, object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(result, dict):
            raise ValueError("expected object")
        pending = [result]
        while pending:
            value = pending.pop()
            if isinstance(value, str):
                value.encode("utf-8")
            elif isinstance(value, dict):
                pending.extend(value.keys())
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, float) and not math.isfinite(value):
                raise ValueError("nonfinite JSON number")
        if "error" in result:
            raise ValueError(str(result["error"]))
        return result
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise LocalServiceError(f"Invalid local API response (finite JSON and UTF-8 strings required): {exc}", body) from exc


class LocalHTTP:
    mode = "local_http"

    def __init__(self, port=11434, timeout=120):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValidationError("localhost port must be an integer in 1..65535")
        if (type(timeout) not in (int, float) or not math.isfinite(timeout)
                or not 0 < timeout <= 300):
            raise ValidationError("local request timeout must be in (0, 300] seconds")
        self.base_url = f"http://127.0.0.1:{port}"
        self.timeout = timeout
        self._opener = build_opener(ProxyHandler({}), NoRedirects())

    def request(self, path, payload=None):
        if path not in ("/api/tags", "/api/show", "/api/version", "/api/chat", "/api/ps"):
            raise ValidationError("unsupported local endpoint; downloads are setup-only")
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        request = Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                body = _read_body(response)
        except HTTPError as exc:
            body = _read_body(exc)
            raise LocalServiceError(f"Local API HTTP {exc.code}", body.decode("utf-8", errors="replace")) from exc
        except (OSError, HTTPException) as exc:
            raise LocalServiceError(f"Local Ollama unavailable: {exc}. Start the explicitly configured local service; no download attempted.") from exc
        if len(body) > MAX_RESPONSE_BYTES:
            raise LocalServiceError("Local API response exceeds 1 MiB limit", body.decode("utf-8", errors="replace"))
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LocalServiceError("Local API response is not UTF-8", body.decode("utf-8", errors="replace")) from exc


class OllamaClient:
    def __init__(self, model="qwen3:1.7b", transport=None):
        if model not in ALLOWED_MODELS:
            raise ValidationError("Use an explicitly configured local Qwen candidate; cloud/custom tags are not allowed")
        self.model = model
        self.transport = transport if transport is not None else LocalHTTP()
        if self.transport.mode not in ("local_http", "test_double"):
            raise ValidationError("transport must declare local_http or test_double provenance")

    def _inventory(self):
        inventory = _object(self.transport.request("/api/tags"))
        models = inventory.get("models")
        if not isinstance(models, list) or any(not isinstance(item, dict) for item in models):
            raise LocalServiceError("Invalid local model inventory")
        matches = [item for item in models if item.get("name") == self.model or item.get("model") == self.model]
        if len(matches) != 1:
            raise LocalServiceError("Selected local model is missing or ambiguous; explicitly install it during approved setup")
        if matches[0].get("remote_host") or matches[0].get("remote_model"):
            raise LocalServiceError("Model inventory identifies a remote alias; hosted inference is forbidden")
        value = matches[0].get("digest")
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise LocalServiceError("Invalid local model digest")
        if value is not None:
            text(value, "local model digest")
        return value

    def observe_residency(self):
        """Read-only server observation, not an OS memory measurement."""
        try:
            body = self.transport.request("/api/ps")
            payload = _object(body)
            models = payload.get("models")
            if not isinstance(models, list) or any(not isinstance(item, dict) for item in models):
                raise LocalServiceError("Invalid running-model inventory", body)
            matches = [item for item in models if item.get("name") == self.model or item.get("model") == self.model]
            if len(matches) > 1:
                raise LocalServiceError("Ambiguous running-model inventory", body)
            selected = matches[0] if matches else None
            for item in models:
                if item.get("digest") is not None:
                    text(item["digest"], "resident model digest")
                for field in ("context_length", "size_vram", "size"):
                    value = item.get(field)
                    if value is not None and (type(value) is not int or value < 0):
                        raise ValidationError(f"Invalid resident model statistic: {field}")
            return {"status": "observed", "resident": selected is not None, "model": selected, "models": models,
                    "raw_body": body, "origin": "live" if self.transport.mode == "local_http" else "test_double"}
        except (LocalServiceError, ValidationError) as exc:
            return {"status": "unavailable", "resident": None, "model": None, "models": [], "error": str(exc),
                    "raw_body": getattr(exc, "raw_body", None),
                    "origin": "live" if self.transport.mode == "local_http" else "test_double"}

    def answer(self, prompt, chunks, max_attempts=2):
        if type(max_attempts) is not int or not 1 <= max_attempts <= 2:
            raise ValidationError("generation attempts must be 1 or 2")
        started = time.perf_counter()
        result = {"origin": "live" if self.transport.mode == "local_http" else "test_double",
                  "model": self.model, "model_digest": None, "server_version": None,
                  "status": "run_error", "answer": None, "attempts": [], "error": None,
                  "generation_performed": False, "generation_attempted": False, "thinking_control": "unverified",
                  "effective_model_context_verified": False,
                  "model_provenance_verified": False, "answer_cache_used": False}
        # Serializes generations across clients in this process. The managed server
        # must also be configured with OLLAMA_NUM_PARALLEL=1.
        with _GENERATION_LOCK:
            try:
                before = self._inventory()
                result["model_digest"] = before
                version = _object(self.transport.request("/api/version")).get("version")
                if not isinstance(version, str) or not version.strip():
                    raise LocalServiceError("Invalid local server version")
                text(version, "local server version")
                result["server_version"] = version
                show = _object(self.transport.request("/api/show", {"model": self.model}))
                result["model_details"] = show
                if show.get("remote_model") or show.get("remote_host"):
                    raise LocalServiceError("Model metadata identifies a remote model; hosted inference is forbidden")
                values = show.get("thinking", {}).get("values", []) if isinstance(show.get("thinking", {}), dict) else []
                disable = any(value is False for value in values) if isinstance(values, list) else False
                if not disable:
                    raise LocalServiceError("Installed model/API does not advertise think=false; verify support before running the CPU experiment")
                result["thinking_control"] = "requested_false"
                request = {"model": self.model, "messages": prompt["messages"], "format": prompt["format"],
                           "stream": False, "think": False, "keep_alive": "5m",
                           "options": {"temperature": 0, "num_ctx": prompt["context_window"],
                                       "num_predict": prompt["max_output_tokens"], "num_gpu": 0}}
                result["request"] = request
                result["configuration_id"] = digest({"client": "ollama-local-v1", "model": self.model,
                    "digest": before, "server_version": version, "options": request["options"],
                    "think": False, "response_format": "answer-citations-abstained-v1"})
                result["generation_request_id"] = digest(request)
                for number in range(1, max_attempts + 1):
                    attempt = {"number": number, "raw_body": None, "error": None}
                    result["attempts"].append(attempt)
                    attempt_started = time.perf_counter()
                    try:
                        result["generation_attempted"] = True
                        attempt["raw_body"] = self.transport.request("/api/chat", request)
                        response = _object(attempt["raw_body"])
                        attempt["response"] = response
                        if response.get("model") != self.model or response.get("done") is not True:
                            raise ValidationError("Generation model mismatch or incomplete response")
                        result["generation_performed"] = True
                        if response.get("done_reason") != "stop":
                            raise ValidationError("Generation did not stop normally; possible output truncation")
                        message = response.get("message")
                        if not isinstance(message, dict) or message.get("role") != "assistant":
                            raise ValidationError("Missing assistant response message")
                        if message.get("thinking"):
                            raise ValidationError("Model returned thinking despite think=false")
                        for field in ("prompt_eval_count", "eval_count", "total_duration", "load_duration",
                                      "prompt_eval_duration", "eval_duration"):
                            value = response.get(field)
                            if value is not None and (type(value) is not int or value < 0):
                                raise ValidationError(f"Invalid generation statistic: {field}")
                        parsed = parse_answer(message.get("content"), chunks)
                        attempt["valid"] = True
                        result["answer"] = {"answer": parsed.answer, "citations": list(parsed.citations),
                                            "abstained": parsed.abstained}
                        result["status"] = "answered_pending_review"
                        break
                    except (ValidationError, LocalServiceError, TypeError) as exc:
                        attempt["error"] = str(exc)
                        if attempt["raw_body"] is None:
                            attempt["raw_body"] = getattr(exc, "raw_body", None)
                        if isinstance(exc, LocalServiceError):
                            break  # No hidden transport retries after timeout/service errors.
                    finally:
                        attempt["elapsed_seconds"] = time.perf_counter() - attempt_started
                after = self._inventory()
                result["model_digest_after"] = after
                if before != after:
                    raise LocalServiceError("Model identity changed during generation")
                if result["answer"] is None:
                    result["error"] = "Generation failed; inspect every preserved attempt"
            except (LocalServiceError, ValidationError) as exc:
                result["status"] = "run_error"
                result["answer"] = None
                result["error"] = str(exc)
                result["preflight_error_body"] = getattr(exc, "raw_body", None)
        result["elapsed_seconds"] = time.perf_counter() - started
        return result
