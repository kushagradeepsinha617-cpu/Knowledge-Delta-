"""Local fixture/review interface. Start through scripts/run_interface.py --serve."""
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_delta.doctor import readiness
from knowledge_delta.evaluation import FAILURE_KINDS, RELATIONS
from knowledge_delta.interface_state import displayed_tokens, tokens_changed
from knowledge_delta.reports import LABELS
from knowledge_delta.review_workflow import ReviewSession
from knowledge_delta.validation import ValidationError
from knowledge_delta.workflow import export_report


def answer_form(st, session, row, slot):
    info = session.answer_info(row["case_id"], row["configuration_name"], slot, row["repetition"])
    key = "answer-display-" + info["subject"]
    if st.button("Reload this review form", key=key + "-refresh"):
        displayed_tokens(st.session_state, key, info, refresh=True)
    tokens = displayed_tokens(st.session_state, key, info)
    changed = tokens_changed(tokens, info)
    if changed:
        st.warning("The evidence or stored review changed. Reload this form and inspect it before saving.")
    st.caption("This reviews the displayed recorded answer. Dataset case labels are reviewed separately.")
    with st.form(key + "-form-" + str(tokens["epoch"])):
        reviewer = st.text_input("Your reviewer name")
        outcome = st.selectbox("Answer judgment", ("needs_human_review", "pass", "fail"))
        failure = st.selectbox("Failure classification (for failed answers)", ("Unclassified", *FAILURE_KINDS))
        rationale = st.text_area("Reason, referring to the expectation and supplied evidence")
        submitted = st.form_submit_button("Save answer review", disabled=changed)
    if submitted:
        try:
            session.save_answer(row["case_id"], row["configuration_name"], slot,
                outcome=outcome, reviewer=reviewer, rationale=rationale,
                failure_kind=None if failure == "Unclassified" else failure,
                expected_binding_hash=tokens["binding_hash"], expected_revision=tokens["revision"], repetition=row["repetition"])
            displayed_tokens(st.session_state, key, session.answer_info(row["case_id"], row["configuration_name"], slot, row["repetition"]), refresh=True)
            st.rerun()
        except (ValidationError, OSError, sqlite3.Error) as exc:
            st.error("The review was not saved.")
            st.text(str(exc))


def relation_form(st, session, row):
    info = session.relation_info(row["case_id"])
    key = "relation-display-" + session.run["run_id"] + "-" + row["case_id"]
    if st.button("Reload expected-change form", key=key + "-refresh"):
        displayed_tokens(st.session_state, key, info, refresh=True)
    tokens = displayed_tokens(st.session_state, key, info)
    changed = tokens_changed(tokens, info)
    if changed:
        st.warning("The case or stored annotation changed. Reload before reviewing its expected change.")
    st.caption("This annotation describes how the two expected behaviors relate. It does not mark the dataset human-reviewed.")
    with st.form(key + "-form-" + str(tokens["epoch"])):
        reviewer = st.text_input("Your reviewer name")
        relation = st.selectbox("Expected relation", RELATIONS, index=2)
        rationale = st.text_area("Why should behavior change, remain, or stay unresolved?")
        submitted = st.form_submit_button("Save expected-change review", disabled=changed)
    if submitted:
        try:
            session.save_relation(row["case_id"], relation=relation, reviewer=reviewer, rationale=rationale,
                expected_binding_hash=tokens["binding_hash"], expected_revision=tokens["revision"])
            displayed_tokens(st.session_state, key, session.relation_info(row["case_id"]), refresh=True)
            st.rerun()
        except (ValidationError, OSError, sqlite3.Error) as exc:
            st.error("The expected-change review was not saved.")
            st.text(str(exc))


def main(project_root=ROOT):
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Streamlit is unavailable. Use scripts/fixture_demo.py for the dependency-free report, or explicitly set up the local UI environment.") from exc
    st.set_page_config(page_title="KnowledgeDelta", layout="wide")
    st.title("KnowledgeDelta")
    st.caption("Inspect how documentation snapshots, expected behavior, answers and evidence fit together.")
    with st.sidebar:
        st.header("Inputs")
        input_mode = st.selectbox("Record source", ("Scripted fixture replay", "Existing run JSON"))
        with st.form("fixture-inputs"):
            before = st.text_input("Before snapshot manifest", "examples/mvp/before/manifest.json")
            after = st.text_input("After snapshot manifest", "examples/mvp/after/manifest.json")
            dataset = st.text_input("Case dataset", "examples/mvp/cases.json")
            relations = st.text_input("Expected-change annotations", "examples/mvp/relations.json")
            run_path = st.text_input("Raw run JSON inside this project") if input_mode == "Existing run JSON" else None
            simulated = st.checkbox("Show simulated correctness judgments", value=False,
                help="Demonstration labels, not human review or benchmark ground truth.") if run_path is None else False
            load = st.form_submit_button("Load records")
        if load:
            st.session_state["loaded-inputs"] = {"before": before, "after": after, "dataset": dataset,
                "relations": relations, "simulate_judgments": simulated, "run_path": run_path}
        with st.expander("Setup status"):
            state = readiness(check_ollama=False)
            st.write({"Python": state["python"], "Streamlit": state["packages"]["streamlit"],
                      "Live inference": "Not requested; models remain unverified"})
            st.caption("This page never installs packages, downloads models or calls Ollama.")
    if "loaded-inputs" not in st.session_state:
        st.info("Load the provided 20-case example to inspect a complete scripted comparison.")
        return
    try:
        with st.status("Loading snapshots and answer records", expanded=False) as status:
            session = ReviewSession(project_root, **st.session_state["loaded-inputs"])
            st.write("Validating the complete dataset and current review bindings.")
            evaluation = session.evaluate()
            status.update(label="Comparison ready", state="complete")
    except (ValidationError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        st.error("The selected inputs or review state could not be loaded.")
        st.text(str(exc))
        return
    st.warning(session.notice)
    if session.allow_fixture:
        st.warning("SIMULATED OUTPUT: fixture/test-double records are excluded from live assistant metrics.")
    counts = evaluation["counts"]
    columns = st.columns(4)
    for column, label, value in zip(columns, ("Draft cases", "Answer records", "Need review", "Run errors"),
        (counts["draft_cases"], counts["recorded_answer_records"], counts["answer_outcomes"]["needs_human_review"], counts["answer_outcomes"]["run_error"])):
        column.metric(label, value)
    st.caption(f"Human answer inspections: {counts['human_answer_reviews']}. Simulated answer judgments: {counts['simulated_answer_judgments']}. Human-reviewed case labels: {counts['human_reviewed_cases']}.")
    if evaluation["stale_reviews"]:
        st.warning(f"{len(evaluation['stale_reviews'])} stored reviews are stale or invalid and do not grade the current results.")
        with st.expander("Stale reviews and preserved history"):
            st.json(evaluation["stale_reviews"])
    with st.expander("Assistant and testing-tool measures"):
        st.caption("Null ratios are unavailable. Fixture outputs and draft labels do not establish assistant accuracy.")
        st.json(evaluation["metrics"])
    with st.expander("Snapshot summaries and document changes"):
        for slot, snapshot in session.snapshots.items():
            st.write({"snapshot": slot, "name": snapshot.name, "default_version": snapshot.default_version,
                      "documents": len(snapshot.documents), "snapshot_id": snapshot.snapshot_id})
        st.json(evaluation["snapshot_changes"])
    st.subheader("Comparison")
    statuses = st.multiselect("Display statuses", list(LABELS), default=list(LABELS), format_func=lambda value: LABELS[value])
    configurations = st.multiselect("Display configurations", list(session.run["configurations"]), default=list(session.run["configurations"]))
    rows = [row for row in evaluation["rows"] if row["comparison"]["status"] in statuses and row["configuration_name"] in configurations]
    st.caption("Filters change the view. Missing planned records remain visible as run errors.")
    table = [{"Case": row["case_id"], "Configuration": row["configuration_name"], "Status": LABELS[row["comparison"]["status"]],
              "Repetition": row["repetition"], "Case labels": row["case"]["review"]["status"], "Simulated output": row["comparison"]["simulated"]} for row in rows]
    st.dataframe(table, width="stretch", hide_index=True)
    if rows:
        choices = {row["case_id"] + " · " + row["configuration_name"] + " · repetition " + str(row["repetition"]): row for row in rows}
        selected = st.selectbox("Inspect case", list(choices))
        row = choices[selected]
        st.subheader("Case details")
        st.text(row["case"]["question"])
        st.caption("Requested target: " + str(row["case"]["requested_version"] or row["case"]["target"]) + " · " + row["case"]["provenance"] + " · " + row["case"]["split"])
        pair = st.columns(2)
        for column, slot in zip(pair, ("before", "after")):
            with column:
                detail = row["snapshots"][slot]
                trace = detail["trace"]
                st.subheader(slot.title())
                st.text("Effective version: " + str(trace.get("effective_version")))
                st.text("Judgment: " + detail["judgment"]["outcome"] + " · " + detail["judgment"]["basis"])
                st.code(trace["answer"]["answer"] if trace.get("answer") else trace.get("error", "No answer"), language=None)
                with st.expander("Expected behavior and rubric"):
                    st.json(detail["expectation"])
                with st.expander("Recorded evidence, citations and checks"):
                    for passage in trace.get("retrieved_passages", []):
                        st.text(passage["chunk_id"] + " · " + passage["document_id"])
                        st.text("Version scope: " + str(passage["software_versions"]))
                        st.code(passage["text"], language=None)
                    st.json(detail["judgment"]["checks"])
                if trace["status"] == "run_error":
                    st.info("This record is a run error. It cannot be reviewed as a correct answer.")
                else:
                    with st.expander("Record your answer review"):
                        answer_form(st, session, row, slot)
        with st.expander("Review the expected change between snapshots"):
            st.json(row["relation"])
            relation_form(st, session, row)
    with st.expander("Export and review history", expanded=True):
        output = st.text_input("Export directory inside this project", "runs/exports/" + session.run["run_id"])
        if st.button("Export HTML and JSON"):
            try:
                st.json(export_report(project_root, output, evaluation))
            except (ValidationError, OSError, ValueError) as exc:
                st.error("Export was not completed; existing different files are preserved.")
                st.text(str(exc))
        st.caption("Review history is append-only in runs/manual_reviews.sqlite3. Dataset case labels remain drafts.")
        st.json(evaluation["review_history"])


if __name__ == "__main__":
    main()
