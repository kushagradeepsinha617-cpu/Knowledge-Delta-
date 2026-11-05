"""Scripted outputs for UI/evaluator demonstrations. No retrieval or inference occurs."""
from copy import deepcopy
from dataclasses import asdict
from types import SimpleNamespace

from .cases import validate_dataset
from .evaluation import make_review, validate_relations
from .prompts import build_prompt
from .questions import QuestionInput
from .validation import digest

FIXTURE_VERSION = "mvp-scripted-v2"


def replay(dataset, snapshots, relation_bundle, *, simulate_judgments=False):
    validate_dataset(dataset, snapshots["before"], snapshots["after"])
    validate_relations(relation_bundle, dataset)
    run = {"schema_version": 1, "kind": "fixture_replay", "run_id": "fixture-" + digest({
        "dataset": dataset, "scenario": FIXTURE_VERSION})[:24], "origin": "fixture",
        "fixture_version": FIXTURE_VERSION, "dataset_hash": digest(dataset),
        "snapshots": dataset["snapshot_ids"], "snapshot_defaults": {slot: snap.default_version for slot, snap in snapshots.items()},
        "configurations": {"basic": {"version_filter": False}, "version_filtered": {"version_filter": True}},
        "repeats": 1, "results": [], "started_at": None, "elapsed_seconds": None,
        "answer_cache_used": False, "correctness_measured": False,
        "notice": "SIMULATED FIXTURE. Scripted evidence and answers; no retrieval, embeddings, model requests or measured configuration improvement. Draft answer keys are used only to construct this replay."}
    reviews = []
    simulated_relations = deepcopy(relation_bundle)
    if simulate_judgments:
        for annotation in simulated_relations["relations"]:
            annotation["basis"] = "fixture"
            annotation["rationale"] = "Simulated expected relation for a fixture demonstration; original case/annotation remain unreviewed drafts."
    for case in dataset["cases"]:
        for configuration in run["configurations"]:
            for slot, snapshot in snapshots.items():
                expectation = case["expectations"][slot]
                doc_ids = list(dict.fromkeys(item["document_id"] for item in expectation["evidence"]))
                failure_kind, outcome = None, "pass"
                note = "Scripted response from the draft expectation; no assistant was queried."
                answer_text = expectation["answer"] or "Applicable evidence is missing or conflicting; I cannot substantiate a single answer."
                abstained = expectation["behavior"] != "answer"
                if expectation["behavior"] == "conflict":
                    answer_text = "Applicable sources conflict: " + "; ".join(item["quote"] for item in expectation["evidence"]) + " I cannot select a single supported answer."
                if slot == "after" and configuration == "basic" and case["category"] == "other_version_added":
                    name = {"v1-token-despite-v2": "widget.token-v2", "v1-report-despite-v2": "widget.report-v2", "v1-page-limit-despite-v2": "widget.page-v2"}.get(case["case_id"])
                    if name is not None:
                        doc_ids = [name]
                        answer_text, abstained = snapshot.document(name).content, False
                        outcome, failure_kind, note = "fail", "wrong_version", "Injected wrong-version context/answer; this is not an observed retrieval failure."
                if case["case_id"] == "request-timeout-change" and slot == "after":
                    answer_text = case["expectations"]["before"]["answer"]
                    outcome, failure_kind, note = "fail", "retained_previous_behavior", "Injected stale answer despite supplied new evidence."
                if case["case_id"] == "cache-directory-rewording":
                    answer_text = "A deliberately unsupported directory: /invented/cache."
                    outcome, failure_kind, note = "fail", "incorrect_answer", "Injected wrong answer in both snapshots."
                if case["case_id"] == "current-archive-compression" and slot == "before":
                    answer_text = "An invented compression format."
                    outcome, failure_kind, note = "fail", "incorrect_answer", "Injected earlier error followed by a scripted recovery."
                if case["case_id"] == "metrics-unrelated-change" and slot == "after":
                    answer_text = "The documented listener is NOT correct; use the invented port 1."
                    outcome, failure_kind, note = "fail", "unsupported_answer", "Injected semantic error; keyword matching must not pass it."
                passages = []
                for doc_id in doc_ids:
                    document = snapshot.document(doc_id)
                    # Explicit fixture-only selection from the gold supporting quote.
                    # Large genuine documents must not overflow a simulated prompt.
                    # This is never presented as retrieval or live inference.
                    start, end = 0, len(document.content)
                    if len(document.content.encode("utf-8")) > 1000:
                        quotes = [ref["quote"] for ref in expectation["evidence"]
                                  if ref["document_id"] == doc_id]
                        if quotes:
                            anchor = document.content.index(quotes[0])
                            start = max(0, anchor - 100)
                            end = min(len(document.content), anchor + len(quotes[0]) + 100)
                    identity = "fixture-chunk-" + digest({"snapshot": snapshot.snapshot_id,
                        "document": doc_id, "start": start, "end": end,
                        "text": document.content[start:end]})[:24]
                    passages.append({"chunk_id": identity, "snapshot_id": snapshot.snapshot_id,
                        "document_id": doc_id, "software_versions": list(document.software_versions),
                        "source_reference": document.source_reference, "source_revision": document.source_revision,
                        "text": document.content[start:end], "start_char": start, "end_char": end,
                        "context_selection": "fixture_gold_quote_window" if (start, end) != (0, len(document.content)) else "fixture_full_document",
                        "provenance": "constructed", "context_origin": "fixture_scripted"})
                citations = [passage["chunk_id"] for passage in passages]
                if case["case_id"] == "installation-rewording" and slot == "after":
                    citations = ["fixture-invented-citation"]
                    outcome, failure_kind, note = "fail", "invalid_response", "Injected citation absent from the simulated prompt."
                if case["case_id"] == "export-evidence-removed" and slot == "after":
                    answer_text, abstained, citations = case["expectations"]["before"]["answer"], False, ["removed-evidence-citation"]
                    outcome, failure_kind, note = "fail", "unsupported_answer", "Injected unsupported answer after evidence removal; the old fact is not thereby false."
                question = QuestionInput.from_case(case, slot)
                prompt = build_prompt(question, snapshot, tuple(SimpleNamespace(**p) for p in passages))
                trace = {"case_id": case["case_id"], "snapshot_slot": slot, "snapshot_id": snapshot.snapshot_id,
                    "configuration_name": configuration, "configuration_id": "fixture-" + digest(run["configurations"][configuration]),
                    "repetition": 1, "origin": "fixture", "question": asdict(question),
                    "requested_version": question.requested_version, "effective_version": question.effective_version(snapshot),
                    "status": "answered_pending_review", "answer": {"answer": answer_text, "citations": citations, "abstained": abstained},
                    "retrieved_passages": passages, "retrieval_exclusions": [], "retrieval_origin": "fixture_scripted",
                    "prompt": prompt, "prompt_origin": "fixture_simulated", "generation": None,
                    "generation_performed": False, "generation_attempted": False, "answer_origin": "fixture_scripted",
                    "model": None, "model_digest": None, "elapsed_seconds": None,
                    "answer_cache_used": False, "error": None, "fixture_note": note}
                if case["case_id"] == "current-log-level" and slot == "after":
                    trace.update(status="run_error", answer=None, error="Injected fixture run error; no inference request occurred.")
                run["results"].append(trace)
                if simulate_judgments and trace["status"] != "run_error" and case["case_id"] != "configuration-file-rewording":
                    reviews.append(make_review(run, trace, dataset, case, outcome, basis="fixture", rationale=note,
                                               failure_kind=failure_kind, snapshots=snapshots))
    run["counts"] = {"planned": len(dataset["cases"]) * 4, "recorded": len(run["results"]),
                     "run_errors": sum(trace["status"] == "run_error" for trace in run["results"])}
    return {"schema_version": 1, "kind": "knowledge_delta_fixture_bundle", "origin": "fixture",
            "run": run, "reviews": reviews, "relations": simulated_relations,
            "simulated_judgments": simulate_judgments, "dataset_hash": digest(dataset)}
