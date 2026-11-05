"""ONNX candidate tests are offline; synthetic metadata and import records only."""
import json
from types import SimpleNamespace

import pytest

from scripts import setup_onnx_runtime as candidate
from scripts import setup_embeddings as shared


def readiness():
    return {"torch_imported": False, "imports": {name: "TEST ONLY" for name in candidate.MODULES},
            "onnx_providers": ["CPUExecutionProvider"]}


def test_default_compatibility_plan_never_runs_network_or_installs(monkeypatch, capsys):
    monkeypatch.setattr(candidate, "perform", lambda *a: pytest.fail("Explicit --test required"))
    assert candidate.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["network_requests"] == 0
    assert result["model_weights_downloaded"] is False
    assert result["torch_import_requested"] is False
    assert result["import_modules"] == ["onnxruntime", "numpy", "tokenizers"]


def test_known_pytorch_dependency_is_rejected_before_any_wheel_transfer(monkeypatch):
    monkeypatch.setattr(candidate, "resolve_packages", lambda **k: [{"name": "torch"}])
    monkeypatch.setattr(candidate, "archive_sizes", lambda *a, **k: pytest.fail("Blocked graph cannot be inspected/installed"))
    with pytest.raises(shared.SetupError, match="blocked PyTorch stack"):
        candidate.inspect_dependencies(SimpleNamespace(request=lambda *a, **k: b""), 100)


def test_readiness_requires_numpy_tokenizer_cpu_provider_and_no_torch():
    assert candidate.validate_readiness(readiness())["torch_imported"] is False
    for modification in ({"torch_imported": True}, {"torch_imported": None},
                         {"onnx_providers": ["CUDAExecutionProvider"]}, {"imports": {}}):
        value = readiness()
        value.update(modification)
        with pytest.raises(shared.SetupError):
            candidate.validate_readiness(value)


def test_custom_import_probe_does_not_request_pytorch_or_sentence_transformers(monkeypatch, tmp_path):
    work = tmp_path / ".tools/model-setup"
    work.mkdir(parents=True)
    monkeypatch.setattr(shared, "bootstrap_pip", lambda *a: work / "test-only-pip.whl")
    monkeypatch.setattr(shared, "child_environment", lambda *a: {})
    captured = []
    def process(command, *args):
        captured.append(command)
        log = work / "TEST-ONLY-readiness.log"
        value = readiness()
        value["versions"] = {}
        value["imports"] = {name: str(__import__("pathlib").Path(shared.sys.prefix) / name)
                            for name in candidate.MODULES}
        log.write_text("KNOWLEDGEDELTA_CPU_READY=" + json.dumps(value), encoding="utf-8")
        return log
    monkeypatch.setattr(shared, "process", process)
    record = {"steps": []}
    shared.install(tmp_path, [], record, import_modules=candidate.MODULES)
    code = captured[0][-1]
    compile(code, "<synthetic-readiness-probe>", "exec")
    assert "for n in ['onnxruntime', 'numpy', 'tokenizers']" in code
    assert "'sentence_transformers'" not in code
    assert "import torch" not in code
    assert record["readiness"]["torch_imported"] is False
