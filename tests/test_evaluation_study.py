"""Study gates use copied datasets and explicitly TEST-ONLY synthetic approvals."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import pytest

from knowledge_delta.ollama import OllamaClient
from knowledge_delta.validation import ValidationError, digest, read_json
from scripts import evaluation_study as study

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project():
    # Keep copied corpus paths below the Windows path limit, inside the repo.
    parent = ROOT / ".tools/s"
    parent.mkdir(parents=True, exist_ok=True)
    assert parent.resolve().is_relative_to(ROOT.resolve())
    with TemporaryDirectory(dir=parent) as owned:
        target = Path(owned).resolve()
        assert target.is_relative_to(parent.resolve())
        for name in ("examples", "knowledge_delta", "scripts", "tests"):
            shutil.copytree(ROOT / name, target / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("pyproject.toml", "requirements-test.txt", ".gitattributes"):
            shutil.copyfile(ROOT / name, target / name)
        ledger = target / "examples/pydantic-evaluation/user-approval.json"
        if ledger.exists(): ledger.unlink()  # Only the owned synthetic project copy.
        yield target


def synthetic_approvals(project):
    entries, _, _ = study.inventory(project)
    for entry in entries:
        dataset = entry["dataset"]
        for case in dataset["cases"]:
            case["review"] = {"status": "human_reviewed", "reviewer": "TEST-ONLY NOT A HUMAN REVIEW",
                              "scope": "Synthetic gate fixture; excluded from benchmark evidence."}
        relations = entry["relations"]
        relations["dataset_hash"] = digest(dataset)
        cases = {c["case_id"]: c for c in dataset["cases"]}
        for relation in relations["relations"]:
            relation.update(case_hash=digest(cases[relation["case_id"]]), basis="human_review",
                            reviewer="TEST-ONLY NOT A HUMAN REVIEW", reviewed_at="2026-11-07T00:00:00+00:00")
        base = project / entry["path"]
        (base / "cases.json").write_text(json.dumps(dataset), encoding="utf-8")
        (base / "relations.json").write_text(json.dumps(relations), encoding="utf-8")


def test_real_inventory_keeps_all_drafts_and_prior_reviews_visible():
    _, counts, _ = study.inventory(ROOT)
    assert (counts["development"], counts["held_out"], counts["cases"]) == (20, 40, 60)
    assert counts["human_reviewed"] + counts["draft"] == 60


def test_draft_gate_blocks_before_local_service_or_output(project, monkeypatch):
    monkeypatch.setattr(OllamaClient, "_inventory", lambda *a: pytest.fail("Drafts must not query services"))
    with pytest.raises(ValidationError, match="Review gate"):
        study.freeze(project, Path("runs/forbidden.json"))
    assert not (project / "runs/forbidden.json").exists()


def test_owner_authorization_allows_execution_without_inventing_human_reviews(project, monkeypatch):
    from scripts.record_study_authorization import record
    before = study.inventory(project)[1]
    assert record(project)["user_approved"] == 60
    assert study.inventory(project)[1] == before
    monkeypatch.setattr(OllamaClient, "_inventory", lambda *a: "TEST-ONLY-DIGEST")
    study.freeze(project, Path("runs/owner-protocol.json"))
    frozen = study.verify_protocol(project, Path("runs/owner-protocol.json"))
    assert frozen["user_approved_definitions"] == 60
    assert frozen["counts"]["human_reviewed"] == before["human_reviewed"]
    ledger = project / "examples/pydantic-evaluation/user-approval.json"
    value = read_json(ledger)
    value["records"][0]["case_hash"] = "STALE"
    ledger.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValidationError): study.verify_protocol(project, Path("runs/owner-protocol.json"))


def test_freeze_binds_case_reviews_and_pipeline_source(project, monkeypatch):
    synthetic_approvals(project)
    monkeypatch.setattr(OllamaClient, "_inventory", lambda *a: "TEST-ONLY-DIGEST")
    study.freeze(project, Path("runs/protocol.json"))
    before = (project / "runs/protocol.json").read_bytes()
    assert study.verify_protocol(project, Path("runs/protocol.json"))["counts"]["human_reviewed"] == 60
    changed = project / "knowledge_delta/prompts.py"
    changed.write_bytes(changed.read_bytes() + b"\n# TEST-ONLY prompt change\n")
    with pytest.raises(ValidationError, match="Frozen inputs"):
        study.verify_protocol(project, Path("runs/protocol.json"))
    assert (project / "runs/protocol.json").read_bytes() == before


def test_review_packet_hashes_exact_cases_and_escapes_markup(project, monkeypatch):
    entries, counts, families = study.inventory(project)
    changed = deepcopy(entries)
    changed[0]["dataset"]["cases"][0]["question"] = '<script>alert("TEST ONLY")</script>'
    monkeypatch.setattr(study, "inventory", lambda root: (changed, counts, families))
    study.review_packet(project, Path("runs/packet"))
    html = (project / "runs/packet/review.html").read_text(encoding="utf-8")
    assert "<script>" not in html and "&lt;script&gt;" in html
    records = read_json(project / "runs/packet/bindings.json")
    assert len(records) == 60
    assert records[0]["case_hash"] == digest(changed[0]["dataset"]["cases"][0])
    with pytest.raises(ValidationError):
        study.review_packet(project, Path("runs/packet"))


def test_family_leakage_blocks_even_with_valid_individual_bundles(project, monkeypatch):
    monkeypatch.setattr(study, "prepare", lambda root: read_json(project / "examples/pydantic-evaluation/study-plan.json"))
    path = project / "examples/pydantic-evaluation/heldout-other-version-added/cases.json"
    dataset = read_json(path)
    dataset["cases"][0]["family_id"] = "pydantic-serialization"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    relations_path = path.with_name("relations.json")
    relations = read_json(relations_path)
    relations["dataset_hash"] = digest(dataset)
    for relation in relations["relations"]:
        case = next(c for c in dataset["cases"] if c["case_id"] == relation["case_id"])
        relation["case_hash"] = digest(case)
    relations_path.write_text(json.dumps(relations), encoding="utf-8")
    with pytest.raises(ValidationError, match="family crosses"):
        study.inventory(project)


def test_cannot_write_study_outputs_outside_project(project):
    with pytest.raises(ValidationError):
        study.output_path(project, Path("../outside-protocol.json"))


def test_evidence_removal_requires_abstention_without_changing_fact_truth():
    entries, _, _ = study.inventory(ROOT)
    removal = next(e for e in entries if e["path"].endswith("heldout-evidence-removed"))
    assert removal["snapshots"]["after"].documents == ()
    for case in removal["dataset"]["cases"]:
        assert case["expectations"]["before"]["behavior"] == "answer"
        assert case["expectations"]["after"]["behavior"] == "abstain"
        assert case["expectations"]["after"]["answer"] is None


@pytest.mark.parametrize("field,value", [("chunk_tokens", 256), ("variability_repeats", 1),
                                        ("answer_cache_used", True)])
def test_protocol_cannot_misreport_ignored_execution_settings(project, monkeypatch, field, value):
    synthetic_approvals(project)
    monkeypatch.setattr(OllamaClient, "_inventory", lambda *a: "TEST-ONLY-DIGEST")
    study.freeze(project, Path("runs/protocol.json"))
    path = project / "runs/protocol.json"
    protocol = read_json(path)
    protocol[field] = value
    protocol.pop("protocol_id")
    protocol["protocol_id"] = digest(protocol)
    path.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(ValidationError, match="Frozen inputs"):
        study.verify_protocol(project, Path("runs/protocol.json"))


def test_raw_execution_remains_accounted_when_report_export_fails(project, monkeypatch):
    from knowledge_delta import onnx_embeddings, experiments, review_workflow, workflow, local_environment
    synthetic_approvals(project)
    monkeypatch.setattr(OllamaClient, "_inventory", lambda *a: "TEST-ONLY-DIGEST")
    study.freeze(project, Path("runs/protocol.json"))
    monkeypatch.setattr(onnx_embeddings, "LocalOnnxMiniLM", lambda *a: object())
    monkeypatch.setattr(local_environment, "configure_offline_environment", lambda *a: {})
    def synthetic_run(dataset, *args, **kwargs):
        count = len(dataset["cases"]) * 4
        return {"origin": "TEST-ONLY", "results": [{"status": "run_error"} for _ in range(count)],
                "counts": {"planned": count, "recorded": count, "run_errors": count}}
    monkeypatch.setattr(experiments, "run_dataset", synthetic_run)
    class TestSession:
        def __init__(self, *a, **kw): pass
        def evaluate(self): return {"TEST-ONLY": True}
    monkeypatch.setattr(review_workflow, "ReviewSession", TestSession)
    def fail_export(*args): raise OSError("TEST-ONLY export failure")
    monkeypatch.setattr(workflow, "export_report", fail_export)
    with pytest.raises(OSError, match="TEST-ONLY"):
        study.run(project, Path("runs/protocol.json"), Path("runs/study"))
    summary = read_json(project / "runs/study/summary.json")
    assert summary["status"] == "interrupted_or_run_error"
    assert summary["recorded_main_records"] == 40
    assert summary["missing_main_records"] == 200
    assert len(summary["runs"]) == 1 and summary["runs"][0]["raw_sha256"]
    assert (project / summary["runs"][0]["raw"]).is_file()


@pytest.mark.parametrize("fault", ["missing", "false_error_count", "changed_after_digest",
                                   "missing_generation", "missing_start_digest", "missing_after_digest",
                                   "null_start_digest", "null_after_digest"])
def test_completed_control_claim_requires_all_rows_and_both_digests(fault):
    result = {"counts": {"planned": 4, "recorded": 4, "run_errors": 0}, "results": [
        {"status": "answered_pending_review", "generation": {"model_digest": "TEST", "model_digest_after": "TEST"}}
        for _ in range(4)]}
    study.verify_result(result, 4, "TEST")
    if fault == "missing": result["results"].pop()
    elif fault == "false_error_count": result["counts"]["run_errors"] = 1
    elif fault == "missing_generation": result["results"][0].pop("generation")
    elif fault == "missing_start_digest": result["results"][0]["generation"].pop("model_digest")
    elif fault == "missing_after_digest": result["results"][0]["generation"].pop("model_digest_after")
    elif fault == "null_start_digest": result["results"][0]["generation"]["model_digest"] = None
    elif fault == "null_after_digest": result["results"][0]["generation"]["model_digest_after"] = None
    else: result["results"][0]["generation"]["model_digest_after"] = "CHANGED"
    with pytest.raises(ValidationError): study.verify_result(result, 4, "TEST")


def test_policy_abstention_and_incomplete_run_error_do_not_require_model_observations():
    result = {"counts": {"planned": 2, "recorded": 2, "run_errors": 1}, "results": [
        {"status": "answered_pending_review", "answer_origin": "policy_abstention", "generation": None},
        {"status": "run_error", "answer_origin": "live", "generation": {"model_digest": None}},
    ]}
    study.verify_result(result, 2, "TEST")
    result["results"][1]["generation"]["model_digest"] = "OTHER"
    with pytest.raises(ValidationError):
        study.verify_result(result, 2, "TEST")
