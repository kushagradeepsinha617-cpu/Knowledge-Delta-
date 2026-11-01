"""Portable JSON and self-contained escaped HTML. No external assets or executable source content."""
from html import escape
import json

from .validation import ValidationError

LABELS = {"pass": "Pass", "expected_answer_change": "Expected answer change",
          "failure_to_adopt_expected_change": "Failed to adopt expected change",
          "previously_correct_now_incorrect": "Previously correct, now incorrect",
          "incorrect_in_both_snapshots": "Incorrect in both snapshots",
          "needs_human_review": "Needs human review", "run_error": "Run error"}


def json_report(evaluation):
    return json.dumps(evaluation, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"


def _pre(value):
    return "<pre>" + escape(str(value) if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)) + "</pre>"


def html_report(evaluation, *, snapshot_changes=None):
    if evaluation.get("kind") != "knowledge_delta_evaluation":
        raise ValidationError("Expected an evaluated run before export")
    fixture = evaluation["origin"] in ("fixture", "test_double") or any(row["comparison"]["simulated"] for row in evaluation["rows"])
    title = "KnowledgeDelta · fixture replay" if fixture else "KnowledgeDelta · evidence report"
    banner = ("SIMULATED FIXTURE — no live inference. Scripted outputs and simulated labels are demonstrations, not benchmark results."
              if fixture else "Imported/live trace report. Correctness depends on recorded reviews and verified source provenance.")
    counts = evaluation["counts"]
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">",
        "<title>" + escape(title) + "</title>",
        "<style>body{font:16px/1.55 system-ui,sans-serif;background:#f5f6f8;color:#17212e;max-width:1160px;margin:auto;padding:30px}header,section,article{background:white;padding:24px;margin:20px 0;border:1px solid #dce1e8;border-radius:10px}h1,h2,h3{line-height:1.25}h1{font-size:30px;margin:4px 0 16px}.notice{padding:15px;background:#fff0ce;border-left:5px solid #b77705}.muted{color:#536173}.stats,.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.stats{grid-template-columns:repeat(4,minmax(0,1fr))}.stat{padding:14px;border:1px solid #dce1e8;border-radius:6px}.stat strong{display:block;font-size:25px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #dce1e8;vertical-align:top}th{background:#edf1f6}a{color:#164a91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f9;padding:12px;font:13px/1.55 ui-monospace,monospace}details{margin:12px 0}summary{cursor:pointer;font-weight:600}.badge{display:inline-block;padding:3px 9px;background:#edf1f6;border-radius:12px;font-size:13px}.error{color:#9f2525}blockquote{margin:10px 0;padding-left:12px;border-left:3px solid #a3b2c8}@media(max-width:720px){body{padding:12px}.pair,.stats{grid-template-columns:1fr}section,article{padding:16px}table{font-size:13px}}</style></head><body>",
        "<header><p class='muted'>LOCAL DOCUMENTATION ANSWER TESTING</p><h1>" + escape(title) + "</h1><p class='notice'>" + escape(banner) + "</p>",
        "<p>Run <code>" + escape(evaluation["run_id"]) + "</code></p><p>" + escape(evaluation["semantic_note"]) + "</p></header>",
        "<section><h2>Run accounting</h2><div class='stats'>"]
    for name, value in (("Cases", counts["cases"]), ("Planned answers", counts["planned_answer_records"]),
                        ("Run errors", counts["answer_outcomes"]["run_error"]), ("Need review", counts["answer_outcomes"]["needs_human_review"])):
        parts.append("<div class='stat'><strong>" + escape(str(value)) + "</strong>" + escape(name) + "</div>")
    parts.extend(["</div><p>Recorded answers: " + escape(str(counts["recorded_answer_records"])) +
        "; missing records retained as errors: " + escape(str(counts["missing_answer_records"])) + ".</p>",
        "<p>Human-reviewed cases: " + escape(str(counts["human_reviewed_cases"])) + "; draft cases: " + escape(str(counts["draft_cases"])) +
        "; human answer reviews: " + escape(str(counts["human_answer_reviews"])) + "; simulated answer judgments: " + escape(str(counts["simulated_answer_judgments"])) + ".</p>",
        "<p>Only the displayed counts are reported here. Simulated labels are excluded from benchmark evidence.</p></section>"])
    if snapshot_changes is not None:
        parts.extend(["<section><h2>Snapshot changes</h2>", _pre(snapshot_changes), "</section>"])
    parts.append("<section><h2>Comparison</h2><p>Select a case to inspect both answers and the evidence.</p><table><thead><tr><th>Case</th><th>Configuration</th><th>Status</th><th>Review status</th></tr></thead><tbody>")
    for index, row in enumerate(evaluation["rows"]):
        status = LABELS[row["comparison"]["status"]]
        parts.append("<tr><td><a href='#case-" + str(index) + "'>" + escape(row["case_id"]) + "</a></td><td>" + escape(row["configuration_name"]) +
            "</td><td>" + escape(status) + (" · simulated" if row["comparison"]["simulated"] else "") + "</td><td>" + escape(row["case"]["review"]["status"]) + " expectations</td></tr>")
    parts.append("</tbody></table></section>")
    for index, row in enumerate(evaluation["rows"]):
        case = row["case"]
        parts.extend(["<article id='case-" + str(index) + "'><h2>" + escape(case["question"]) + "</h2>",
            "<p><span class='badge'>" + escape(LABELS[row["comparison"]["status"]]) + "</span> · " + escape(row["configuration_name"]) +
            " · repetition " + escape(str(row["repetition"])) + "</p>",
            "<p>Requested version: " + escape(str(case["requested_version"] or case["target"])) + "; provenance: " + escape(case["provenance"]) + "; split: " + escape(case["split"]) + ".</p>",
            "<p>Expected relation: " + escape(row["comparison"]["expected_relation"]) + " (" + escape(row["comparison"]["relation_basis"]) + ").</p><div class='pair'>"])
        for slot in ("before", "after"):
            detail = row["snapshots"][slot]
            trace, judgment = detail["trace"], detail["judgment"]
            context_label = ("Scripted evidence — simulated" if trace.get("origin") in ("fixture", "test_double") else
                "Recorded request passages — effective model context unverified" if trace.get("generation_attempted") is True else
                "Retrieved passages — no model request")
            parts.extend(["<div><h3>" + slot.title() + "</h3><p>Judgment: " + escape(judgment["outcome"]) + " · " + escape(judgment["basis"]) + "</p>",
                "<p>Effective version: " + escape(str(trace.get("effective_version", "unknown"))) + "</p><h4>Answer</h4>", _pre(trace.get("answer") or trace.get("error") or "No answer"),
                "<details><summary>Expectation and rubric</summary>", _pre(detail["expectation"]), "</details>",
                "<details open><summary>" + escape(context_label) + "</summary>"])
            for passage in trace.get("retrieved_passages", []):
                parts.extend(["<p><code>" + escape(passage["chunk_id"]) + "</code> · " + escape(passage["document_id"]) + " · versions " + escape(str(passage["software_versions"])) + "</p>", _pre(passage["text"])])
            if not trace.get("retrieved_passages"):
                parts.append("<p>No supplied passages.</p>")
            parts.extend(["</details><details><summary>Checks, review and complete trace</summary>", _pre(judgment), _pre(trace), "</details></div>"])
        parts.append("</div></article>")
    parts.append("<footer><p>KnowledgeDelta · self-contained report · no external assets. Keep genuine changes, constructed fixtures and live measurements separate.</p></footer></body></html>")
    return "".join(parts)
