"""Offline boundaries for the optional real-model retrieval command."""
import pytest
from scripts import check_onnx_retrieval as cli


def test_existing_output_is_preserved_before_loading_real_model(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "check", lambda *a: pytest.fail("Must validate output first"))
    target = tmp_path / "runs/existing.json"
    target.parent.mkdir()
    target.write_text("preserve", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli.main(["--output", "runs/existing.json"])
    assert target.read_text(encoding="utf-8") == "preserve"


def test_output_outside_runs_rejected_before_model_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "check", lambda *a: pytest.fail("Must validate output first"))
    with pytest.raises(SystemExit):
        cli.main(["--output", "outside.json"])
    assert not (tmp_path / "outside.json").exists()
