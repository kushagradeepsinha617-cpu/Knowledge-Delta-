"""Raw experiment output contract: no models, services or downloads."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_local_cases as cli

ROOT = Path(__file__).resolve().parents[1]


def prepare(monkeypatch, tmp_path, run_errors=0):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "configure_offline_environment", lambda *a: None)
    monkeypatch.setattr(cli, "LocalMiniLM", lambda *a: SimpleNamespace(token_limit=256))
    monkeypatch.setattr(cli, "OllamaClient", lambda *a: SimpleNamespace())
    result = {"kind": "local_snapshot_experiment", "status": "completed_with_run_errors" if run_errors else "completed_pending_review",
              "run_id": "TEST-ONLY", "origin": "test_double",
              "counts": {"run_errors": run_errors}, "results": [{"answer": "TEST ONLY: café", "error": "injected" if run_errors else None}]}
    monkeypatch.setattr(cli, "run_dataset", lambda *a, **k: result)
    args = [str(ROOT / "examples/pydantic/before/manifest.json"),
            str(ROOT / "examples/pydantic/after/manifest.json"),
            str(ROOT / "examples/pydantic/cases.json"),
            "--embedding-directory", str(tmp_path / "assets")]
    return args, result


def test_explicit_output_is_utf8_and_preserves_all_raw_results(monkeypatch, tmp_path, capsys):
    args, expected = prepare(monkeypatch, tmp_path)
    assert cli.main([*args, "--output", "runs/live-test.json"]) == 0
    body = (tmp_path / "runs/live-test.json").read_bytes()
    assert b"caf\xc3\xa9" in body
    assert json.loads(body) == expected
    assert json.loads(capsys.readouterr().out)["origin"] == "test_double"


def test_run_errors_are_saved_even_when_exit_is_nonzero(monkeypatch, tmp_path):
    args, expected = prepare(monkeypatch, tmp_path, run_errors=2)
    assert cli.main([*args, "--output", "runs/failed-test.json"]) == 2
    assert json.loads((tmp_path / "runs/failed-test.json").read_text(encoding="utf-8")) == expected


def test_existing_or_outside_output_rejected_before_embedding_load(monkeypatch, tmp_path):
    args, _ = prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "LocalMiniLM", lambda *a: pytest.fail("Output must be checked first"))
    target = tmp_path / "runs/keep.json"
    target.parent.mkdir()
    target.write_text("preserve", encoding="utf-8")
    assert cli.main([*args, "--output", "runs/keep.json"]) == 2
    assert cli.main([*args, "--output", "source.json"]) == 2
    assert target.read_text(encoding="utf-8") == "preserve"


def test_post_start_failure_does_not_claim_generation_did_not_happen(monkeypatch, tmp_path, capsys):
    args, _ = prepare(monkeypatch, tmp_path)
    def failure(*a, **k):
        raise RuntimeError("TEST ONLY failure after experiment start")
    monkeypatch.setattr(cli, "run_dataset", failure)
    assert cli.main(args) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["experiment_started"] is True
    assert result["generation_performed"] is None


def test_explicit_onnx_backend_does_not_silently_call_legacy_adapter(monkeypatch, tmp_path):
    args, _ = prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "LocalMiniLM", lambda *a: pytest.fail("Legacy adapter must not be selected"))
    monkeypatch.setattr(cli, "LocalOnnxMiniLM", lambda *a: SimpleNamespace(token_limit=256))
    assert cli.main([*args, "--embedding-backend", "onnxruntime"]) == 0


@pytest.mark.parametrize("cap", [128, 256])
def test_explicit_output_cap_reaches_experiment_without_changing_other_settings(monkeypatch, tmp_path, cap):
    from knowledge_delta.pipeline import RunConfiguration
    args, result = prepare(monkeypatch, tmp_path)
    def capture(*a, **kwargs):
        assert kwargs["configuration"] == RunConfiguration(max_output_tokens=cap)
        assert kwargs["repeats"] == 1
        assert kwargs["token_limit"] == 128
        return result
    monkeypatch.setattr(cli, "run_dataset", capture)
    assert cli.main([*args, "--max-output-tokens", str(cap)]) == 0


def test_default_output_cap_preserves_original_experiment(monkeypatch, tmp_path):
    args, result = prepare(monkeypatch, tmp_path)
    def capture(*a, **kwargs):
        assert kwargs["configuration"].max_output_tokens == 128
        return result
    monkeypatch.setattr(cli, "run_dataset", capture)
    assert cli.main(args) == 0


def test_unsupported_output_cap_rejected_before_model_loading(monkeypatch, tmp_path):
    args, _ = prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "LocalMiniLM", lambda *a: pytest.fail("Invalid CLI cap must stop before loading"))
    with pytest.raises(SystemExit) as exc:
        cli.main([*args, "--max-output-tokens", "512"])
    assert exc.value.code == 2
