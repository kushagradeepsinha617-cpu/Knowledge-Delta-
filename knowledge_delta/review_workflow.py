"""Review saved experiment records or scripted fixtures; loading never runs inference."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .diff import compare
from .evaluation import (binding, evaluate_run, make_review, result_key, validate_relation,
                         validate_review)
from .fixture_replay import replay
from .metrics import summarize_metrics
from .review_store import ReviewConflict, ReviewStore
from .snapshots import load_snapshot
from .validation import ValidationError, digest, read_json

MAX_RUN_BYTES = 16 * 1024 * 1024


class ReviewSession:
    def __init__(self, project_root, *, before="examples/mvp/before/manifest.json",
                 after="examples/mvp/after/manifest.json", dataset="examples/mvp/cases.json",
                 relations="examples/mvp/relations.json", simulate_judgments=False, run_path=None,
                 reference_labels=None):
        self.root = Path(project_root).resolve()
        def source(value):
            path = Path(value)
            path = (self.root / path).resolve() if not path.is_absolute() else path.resolve()
            if not path.is_relative_to(self.root):
                raise ValidationError("Review inputs must stay inside this project folder")
            return path
        self.snapshots = {"before": load_snapshot(source(before)), "after": load_snapshot(source(after))}
        self.dataset = read_json(source(dataset))
        self.original_relations = read_json(source(relations))
        self.reference_labels = []
        self.reference_labels_path = None
        if reference_labels is not None:
            path = source(reference_labels)
            if not path.is_file() or path.stat().st_size > MAX_RUN_BYTES:
                raise ValidationError("Select a regular independent-reference JSON file within the 16 MiB import limit")
            labels = read_json(path)
            if not isinstance(labels, list):
                raise ValidationError("Independent-reference JSON must be a list of separately attested reference records")
            self.reference_labels = labels
            self.reference_labels_path = str(path.relative_to(self.root))
        self.input_mode = "existing_run" if run_path is not None else "fixture_replay"
        self.input_run_path = None
        if run_path is not None:
            if simulate_judgments:
                raise ValidationError("Saved runs cannot be graded with generated fixture-oracle judgments")
            path = source(run_path)
            if not path.is_file() or path.stat().st_size > MAX_RUN_BYTES:
                raise ValidationError("Select a regular saved-run JSON file within the 16 MiB import limit")
            raw = read_json(path)
            if (not isinstance(raw, dict) or type(raw.get("schema_version")) is not int
                    or raw["schema_version"] != 1 or raw.get("kind") not in ("local_snapshot_experiment", "fixture_replay")):
                raise ValidationError("Import raw experiment JSON from run_local_cases, or a raw fixture run; report JSON is a separate export")
            if raw.get("dataset_hash") != digest(self.dataset):
                raise ValidationError("Saved run must identify the exact selected dataset revision")
            if raw.get("origin") not in ("live", "fixture", "test_double", "unverified", "mixed"):
                raise ValidationError("Saved run must declare its recorded origin")
            self.bundle = {"run": raw, "reviews": [], "relations": deepcopy(self.original_relations)}
            self.input_run_path = str(path.relative_to(self.root))
        else:
            self.bundle = replay(self.dataset, self.snapshots, self.original_relations, simulate_judgments=simulate_judgments)
        self.run = self.bundle["run"]
        raw_results = self.run.get("results")
        self.allow_fixture = self.run.get("origin") in ("fixture", "test_double") or (
            isinstance(raw_results, list) and any(isinstance(trace, dict) and trace.get("origin") in ("fixture", "test_double") for trace in raw_results))
        # Validate the original import before indexing records or exposing review actions.
        initial_evaluation = evaluate_run(self.run, self.dataset, self.bundle["relations"], self.bundle["reviews"],
                                         snapshots=self.snapshots, allow_fixture=self.allow_fixture)
        # Reject stale/duplicate/orphaned reference labels before exposing review
        # actions. Loading never creates labels, journal events or metric truth.
        summarize_metrics(initial_evaluation, self.reference_labels)
        self.notice = (self.run["notice"] if self.input_mode == "fixture_replay" else
            "IMPORTED RUN. Recorded answers and evidence are preserved. No inference was performed during import. Origin/model/runtime provenance is self-reported by the file, not authenticated by this loader.")
        self.cases = {case["case_id"]: case for case in self.dataset["cases"]}
        self.traces = {digest(result_key(self.run, trace)): trace for trace in self.run["results"]}
        self.store = ReviewStore(self.root)

    def answer_info(self, case_id, configuration, slot, repetition=1):
        key = {"run_id": self.run["run_id"], "case_id": case_id, "configuration_name": configuration,
               "snapshot_slot": slot, "repetition": repetition}
        subject = digest(key)
        if subject not in self.traces:
            raise ValidationError("No result matches the selected case/configuration/snapshot/repetition")
        trace = self.traces[subject]
        bound = binding(self.run, trace, self.dataset, self.cases[case_id], snapshots=self.snapshots)
        stored = self.store.latest("answer", self.run["run_id"]).get(subject)
        return {"subject": subject, "binding": bound, "binding_hash": digest(bound),
                "revision": stored["revision"] if stored else 0, "stored_review": stored,
                "trace": trace, "case": self.cases[case_id]}

    def relation_info(self, case_id):
        if case_id not in self.cases:
            raise ValidationError("Unknown expected-change case")
        bound = {"run_id": self.run["run_id"], "dataset_hash": digest(self.dataset),
                 "case_hash": digest(self.cases[case_id])}
        stored = self.store.latest("relation", self.run["run_id"]).get(case_id)
        return {"subject": case_id, "binding_hash": digest(bound), "revision": stored["revision"] if stored else 0,
                "stored_review": stored, "case": self.cases[case_id]}

    def save_answer(self, case_id, configuration, slot, *, outcome, reviewer, rationale,
                    expected_binding_hash, expected_revision, failure_kind=None, abstention_judgment=None, repetition=1):
        info = self.answer_info(case_id, configuration, slot, repetition)
        if info["binding_hash"] != expected_binding_hash:
            raise ReviewConflict("The displayed case/answer/evidence changed. Reload it before reviewing.")
        review = make_review(self.run, info["trace"], self.dataset, info["case"], outcome,
            basis="human_review", reviewer=reviewer, rationale=rationale, failure_kind=failure_kind,
            abstention_judgment=abstention_judgment, snapshots=self.snapshots)
        return self.store.append("answer", self.run["run_id"], info["subject"], review, expected_revision=expected_revision)

    def save_relation(self, case_id, *, relation, reviewer, rationale, expected_binding_hash, expected_revision):
        info = self.relation_info(case_id)
        if info["binding_hash"] != expected_binding_hash:
            raise ReviewConflict("The displayed case/expectations changed. Reload before reviewing the expected change.")
        annotation = {"schema_version": 1, "case_id": case_id, "case_hash": digest(info["case"]),
                      "relation": relation, "basis": "human_review", "reviewer": reviewer,
                      "reviewed_at": datetime.now(timezone.utc).isoformat(), "rationale": rationale}
        validate_relation(annotation, self.dataset, info["case"])
        return self.store.append("relation", self.run["run_id"], case_id, annotation, expected_revision=expected_revision)

    def evaluate(self):
        answers = {digest(item["binding"]["result_key"]): item for item in self.bundle["reviews"]}
        relations = deepcopy(self.bundle["relations"])
        relation_positions = {item["case_id"]: index for index, item in enumerate(relations["relations"])}
        original = {item["case_id"]: item for item in self.original_relations["relations"]}
        stale = []
        for subject, event in self.store.latest("answer", self.run["run_id"]).items():
            try:
                if subject not in self.traces:
                    raise ValidationError("Stored review refers to an unavailable result")
                trace = self.traces[subject]
                validate_review(event["payload"], self.run, trace, self.dataset, self.cases[trace["case_id"]], snapshots=self.snapshots)
                if event["payload"]["basis"] != "human_review":
                    raise ValidationError("Manual journal contains a non-human review basis")
                answers[subject] = event["payload"]
            except (ValidationError, KeyError, TypeError) as exc:
                answers.pop(subject, None)  # Never silently fall back to a simulated pass.
                stale.append({"kind": "answer", "subject": subject, "revision": event["revision"],
                              "reason": str(exc), "payload": event["payload"]})
        for case_id, event in self.store.latest("relation", self.run["run_id"]).items():
            try:
                if case_id not in self.cases:
                    raise ValidationError("Stored expected-change review refers to an unavailable case")
                validate_relation(event["payload"], self.dataset, self.cases[case_id])
                if event["payload"]["basis"] != "human_review":
                    raise ValidationError("Manual journal contains a non-human relation basis")
                if case_id in relation_positions:
                    relations["relations"][relation_positions[case_id]] = event["payload"]
                else:
                    relation_positions[case_id] = len(relations["relations"])
                    relations["relations"].append(event["payload"])
            except (ValidationError, KeyError, TypeError) as exc:
                if case_id in relation_positions:
                    if case_id in original:
                        relations["relations"][relation_positions[case_id]] = deepcopy(original[case_id])
                    else:
                        relations["relations"] = [item for item in relations["relations"] if item["case_id"] != case_id]
                        relation_positions = {item["case_id"]: index for index, item in enumerate(relations["relations"])}
                stale.append({"kind": "relation", "subject": case_id, "revision": event["revision"],
                              "reason": str(exc), "payload": event["payload"]})
        evaluation = evaluate_run(self.run, self.dataset, relations, list(answers.values()),
                                   snapshots=self.snapshots, allow_fixture=self.allow_fixture)
        evaluation.update(raw_run=self.run, review_records=list(answers.values()), relation_annotations=relations,
                          snapshot_changes=compare(self.snapshots["before"], self.snapshots["after"]),
                          fixture_notice=self.notice if self.allow_fixture else None, import_notice=self.notice,
                          input_mode=self.input_mode, input_run_path=self.input_run_path,
                          inference_performed_during_review=False, stale_reviews=stale,
                          review_history=self.store.history(self.run["run_id"]))
        evaluation["reference_labels"] = deepcopy(self.reference_labels)
        evaluation["reference_labels_path"] = self.reference_labels_path
        evaluation["metrics"] = summarize_metrics(evaluation, self.reference_labels)
        return evaluation
