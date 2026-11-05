"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const labels = {
    pass: "Pass", expected_answer_change: "Expected answer change",
    failure_to_adopt_expected_change: "Failed to adopt expected change",
    previously_correct_now_incorrect: "Previously correct, now incorrect",
    incorrect_in_both_snapshots: "Incorrect in both snapshots",
    needs_human_review: "Needs human review", run_error: "Run error"
  };
  const failureKinds = ["incorrect_answer", "retained_previous_behavior", "wrong_version", "unsupported_answer",
    "unnecessary_abstention", "invalid_response", "citation_version_mismatch", "other"];
  let state = null;
  let csrf = "";
  let busy = false;
  let selected = "";
  let controlNumber = 0;
  const answerDrafts = new Map();
  const relationDrafts = new Map();

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }

  function replace(id, ...children) { $(id).replaceChildren(...children); }
  function json(value) { return element("pre", JSON.stringify(value === undefined ? null : value, null, 2)); }
  function message(text, kind = "error") {
    const node = $("message");
    node.textContent = text;
    node.className = "message " + kind;
    node.hidden = !text;
  }
  function setBusy(value, text = "") {
    busy = value;
    $("request-status").textContent = text;
    $("request-status").classList.toggle("busy", value);
    for (const node of document.querySelectorAll("button,input,select,textarea")) {
      if (value) {
        node.dataset.busyDisabled = node.disabled ? "true" : "false";
        node.disabled = true;
      } else if (node.dataset.busyDisabled !== undefined) {
        node.disabled = node.dataset.busyDisabled === "true";
        delete node.dataset.busyDisabled;
      }
    }
  }

  async function request(path, body, progress) {
    if (busy) throw new Error("Wait for the current request to finish.");
    setBusy(true, progress);
    try {
      const options = {credentials: "same-origin", cache: "no-store", redirect: "error"};
      if (body !== undefined) {
        options.method = "POST";
        options.headers = {"Content-Type": "application/json", "X-KnowledgeDelta-Token": csrf};
        options.body = JSON.stringify(body);
      }
      const response = await fetch(path, options);
      let data;
      try { data = await response.json(); }
      catch (_) { throw new Error("The local server did not return a valid JSON response."); }
      if (!response.ok) {
        const error = new Error(data.error || "The local request failed.");
        error.status = response.status;
        throw error;
      }
      return data;
    } finally {
      setBusy(false, "");
    }
  }

  function acceptState(next, clearForms = false) {
    if (!next || typeof next.csrf !== "string") throw new Error("The local workspace response is incomplete. Reload the page.");
    state = next;
    csrf = next.csrf;
    if (clearForms) {
      answerDrafts.clear();
      relationDrafts.clear();
      selected = "";
    }
    render();
  }

  function rowKey(row) { return JSON.stringify([row.case_id, row.configuration_name, row.repetition]); }
  function badge(status, simulated) {
    const kind = status === "pass" ? "pass" : status === "expected_answer_change" ? "change" :
      status === "run_error" ? "error" : status === "needs_human_review" ? "review" : "fail";
    return element("span", (labels[status] || status) + (simulated ? " · simulated" : ""), "badge " + kind);
  }
  function populateSelect(node, options, previous) {
    node.replaceChildren();
    for (const [value, text] of options) {
      const option = element("option", text);
      option.value = value;
      node.append(option);
    }
    node.value = options.some(([value]) => value === previous) ? previous : (options[0]?.[0] || "");
  }
  function expandable(title, value, open = false) {
    const node = element("details");
    node.open = open;
    node.append(element("summary", title), json(value));
    return node;
  }

  function render() {
    $("readiness").textContent = JSON.stringify(state.readiness || {}, null, 2);
    const loaded = state.loaded === true && state.evaluation;
    $("empty-state").hidden = !!loaded;
    $("workspace").hidden = !loaded;
    if (!loaded) return;
    const evaluation = state.evaluation;
    const rows = evaluation.rows || [];
    const simulated = evaluation.origin === "fixture" || evaluation.origin === "test_double" ||
      rows.some((row) => row.comparison?.simulated);
    const notice = $("provenance-notice");
    notice.className = "notice" + (simulated ? "" : " recorded");
    notice.textContent = (simulated ? "SIMULATED OUTPUT · " : "RECORDED RESULTS · ") +
      (state.notice || evaluation.import_notice || evaluation.fixture_notice ||
       "Inspect the recorded origin and reviews. Loading records performs no inference.");
    $("run-description").textContent = "Run " + evaluation.run_id + " · origin: " + evaluation.origin;
    const counts = evaluation.counts;
    const outcomes = counts.answer_outcomes || {};
    replace("summary", ...[
      [counts.draft_cases, "Draft cases"],
      [String(counts.recorded_answer_records) + " / " + counts.planned_answer_records, "Recorded / planned answers"],
      [outcomes.needs_human_review, "Need human review"],
      [outcomes.run_error, "Run errors (including missing records)"]
    ].map(([value, label]) => {
      const card = element("div", null, "stat");
      card.append(element("strong", value ?? "—"), element("span", label));
      return card;
    }));
    $("review-counts").textContent = "Human answer inspections: " + counts.human_answer_reviews +
      " · Simulated judgments: " + counts.simulated_answer_judgments + " · Human-reviewed case labels: " + counts.human_reviewed_cases +
      ". Answer reviews do not approve draft case labels.";
    replace("snapshot-summaries", ...(state.snapshots || []).map((snapshot) => {
      const card = element("div", null, "snapshot-summary");
      card.append(element("h3", snapshot.slot === "before" ? "Before" : "After"), element("p", snapshot.name),
        element("p", "Default version: " + (snapshot.default_version ?? "unknown") + " · Documents: " + snapshot.documents),
        element("p", snapshot.snapshot_id, "hash muted"));
      return card;
    }));
    replace("snapshot-changes", expandable("Document additions, edits and removals", evaluation.snapshot_changes));
    replace("metrics", json(evaluation.metrics));
    const stale = evaluation.stale_reviews || [];
    $("stale-panel").hidden = !stale.length;
    replace("stale-reviews", json(stale));
    replace("review-history", json(evaluation.review_history || []));
    populateSelect($("status-filter"), [["", "All statuses"], ...Object.entries(labels)], $("status-filter").value);
    const configurations = [...new Set(rows.map((row) => row.configuration_name))];
    populateSelect($("config-filter"), [["", "All configurations"], ...configurations.map((name) => [name, name])], $("config-filter").value);
    renderComparisons();
    if (!$("export-directory").value) $("export-directory").value = "runs/exports/" + evaluation.run_id;
  }

  function filteredRows() {
    const search = $("case-filter").value.trim().toLocaleLowerCase();
    const status = $("status-filter").value;
    const config = $("config-filter").value;
    return (state.evaluation.rows || []).filter((row) =>
      (!status || row.comparison.status === status) && (!config || row.configuration_name === config) &&
      (!search || (row.case_id + " " + row.case.question).toLocaleLowerCase().includes(search)));
  }

  function renderComparisons() {
    const rows = filteredRows();
    if (!rows.some((row) => rowKey(row) === selected)) selected = rows.length ? rowKey(rows[0]) : "";
    $("table-caption").textContent = "Showing " + rows.length + " of " + state.evaluation.rows.length + " comparisons.";
    const body = $("comparison-body");
    body.replaceChildren();
    for (const row of rows) {
      const key = rowKey(row);
      const tr = element("tr", null, key === selected ? "selected" : "");
      const caseCell = element("td");
      const button = element("button", row.case_id, "case-link");
      button.type = "button";
      if (key === selected) button.setAttribute("aria-current", "true");
      button.addEventListener("click", () => { selected = key; renderComparisons(); });
      caseCell.append(button);
      const statusCell = element("td");
      statusCell.append(badge(row.comparison.status, row.comparison.simulated));
      tr.append(caseCell, element("td", row.configuration_name), element("td", row.repetition), statusCell,
        element("td", row.case.review.status));
      body.append(tr);
    }
    if (!rows.length) {
      const tr = element("tr");
      const td = element("td", "No comparisons match these filters.");
      td.colSpan = 5;
      tr.append(td);
      body.append(tr);
    }
    populateSelect($("case-select"), rows.map((row) => [rowKey(row), row.case_id + " · " + row.configuration_name + " · repetition " + row.repetition]), selected);
    $("case-select").disabled = !rows.length;
    renderCase(rows.find((row) => rowKey(row) === selected));
  }

  function addField(form, labelText, kind, value, update, required = false, options = []) {
    const id = "review-field-" + (++controlNumber);
    const label = element("label", labelText);
    label.htmlFor = id;
    const input = element(kind === "textarea" ? "textarea" : kind === "select" ? "select" : "input");
    input.id = id;
    input.required = required;
    if (kind === "select") {
      for (const [optionValue, optionLabel] of options) {
        const option = element("option", optionLabel);
        option.value = optionValue;
        input.append(option);
      }
    } else if (kind !== "textarea") input.type = "text";
    input.value = value;
    input.addEventListener(kind === "select" ? "change" : "input", () => update(input.value));
    form.append(label, input);
    return input;
  }

  function draftFor(map, key, tokens, defaults) {
    if (!map.has(key)) map.set(key, {tokens: {binding_hash: tokens.binding_hash, revision: tokens.revision},
      values: {...defaults}, saved: false, conflict: false});
    return map.get(key);
  }

  function reviewForm(row, slot, tokens) {
    const isAnswer = slot !== null;
    const map = isAnswer ? answerDrafts : relationDrafts;
    const key = isAnswer ? tokens.subject : state.evaluation.run_id + ":" + row.case_id;
    const defaults = isAnswer ? {reviewer: "", rationale: "", outcome: "needs_human_review", failure_kind: "", abstention_judgment: ""} :
      {reviewer: "", rationale: "", relation: "undetermined"};
    const draft = draftFor(map, key, tokens, defaults);
    const stale = draft.tokens.binding_hash !== tokens.binding_hash || draft.tokens.revision !== tokens.revision;
    const form = element("form", null, "review-form");
    const caption = isAnswer ? "Review the displayed answer and its evidence. This does not approve the dataset’s draft expectations." :
      "Review how the two expected behaviors relate. Answer wording alone does not establish a change.";
    form.append(element("p", caption, "hint"));
    if (draft.saved || draft.conflict || stale) form.append(element("p",
      draft.saved ? "Saved. Reload data to open a fresh review form. Your entered text is retained until then." :
      "This form is outdated. Reload data and inspect the current evidence before saving. Your entered text has been retained.",
      "form-note" + (draft.saved ? " saved" : "")));
    addField(form, "Your reviewer name", "text", draft.values.reviewer, (v) => { draft.values.reviewer = v; }, true);
    if (isAnswer) {
      addField(form, "Answer judgment", "select", draft.values.outcome, (v) => { draft.values.outcome = v; }, false,
        [["needs_human_review", "Needs human review"], ["pass", "Pass"], ["fail", "Fail"]]);
      addField(form, "Failure classification (for failed answers)", "select", draft.values.failure_kind,
        (v) => { draft.values.failure_kind = v; }, false,
        [["", "Unclassified"], ...failureKinds.map((value) => [value, value.replaceAll("_", " ")])]);
      if (row.snapshots[slot].trace.answer?.abstained === true) addField(form, "Abstention assessment", "select",
        draft.values.abstention_judgment, (v) => { draft.values.abstention_judgment = v; }, false,
        [["", "Unassessed"], ["appropriate", "Appropriate (requires Pass)"], ["unnecessary", "Unnecessary (requires Fail)"]]);
    } else addField(form, "Expected relation", "select", draft.values.relation,
      (v) => { draft.values.relation = v; }, false,
      [["undetermined", "Undetermined"], ["should_change", "Should change"], ["should_remain", "Should remain"]]);
    addField(form, "Reason, referring to expectations and source evidence", "textarea", draft.values.rationale,
      (v) => { draft.values.rationale = v; }, true);
    const save = element("button", isAnswer ? "Save answer review" : "Save expected-change review", "primary");
    save.type = "submit";
    save.disabled = draft.saved || draft.conflict || stale;
    form.append(save);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (busy || draft.saved || draft.conflict || stale) return;
      message("");
      const common = {case_id: row.case_id, reviewer: draft.values.reviewer, rationale: draft.values.rationale,
        expected_binding_hash: draft.tokens.binding_hash, expected_revision: draft.tokens.revision};
      const payload = isAnswer ? {...common, configuration: row.configuration_name, slot, repetition: row.repetition,
        outcome: draft.values.outcome, failure_kind: draft.values.failure_kind || null,
        abstention_judgment: draft.values.abstention_judgment || null} : {...common, relation: draft.values.relation};
      try {
        const result = await request(isAnswer ? "/api/review-answer" : "/api/review-relation", payload, "Saving your review…");
        draft.saved = true;
        acceptState(result.state);
        message("Review saved. Case-label review status is unchanged. Reload explicitly when you are ready to clear review forms.", "success");
      } catch (error) {
        if (error.status === 409) draft.conflict = true;
        message(error.message + (error.status === 409 ? " Reload data and review the current record before saving." : ""));
        renderComparisons();
      }
    });
    return form;
  }

  function renderCase(row) {
    const container = $("case-details");
    container.replaceChildren();
    if (!row) {
      container.append(element("h2", "No case selected"), element("p", "Change the filters to inspect a comparison."));
      return;
    }
    const title = element("h2", row.case.question);
    title.id = "case-title";
    const meta = element("div", null, "case-meta");
    for (const value of [row.case_id, row.configuration_name, "Repetition " + row.repetition,
      "Target: " + (row.case.requested_version ?? row.case.target), row.case.provenance, row.case.split]) meta.append(element("span", value));
    container.append(title, meta, badge(row.comparison.status, row.comparison.simulated));
    const pair = element("div", null, "snapshot-pair");
    for (const slot of ["before", "after"]) {
      const detail = row.snapshots[slot];
      const trace = detail.trace;
      const answer = trace.answer && typeof trace.answer === "object" && !Array.isArray(trace.answer) ? trace.answer : null;
      const answerText = typeof answer?.answer === "string" ? answer.answer : trace.answer !== null && trace.answer !== undefined ?
        JSON.stringify(trace.answer, null, 2) : trace.error || "No answer recorded.";
      const passages = Array.isArray(trace.retrieved_passages) ? trace.retrieved_passages : [];
      const column = element("section", null, "snapshot-side");
      column.append(element("h3", slot === "before" ? "Before" : "After"),
        element("p", "Judgment: " + detail.judgment.outcome + " · " + detail.judgment.basis, "hint"),
        element("p", "Effective version: " + (trace.effective_version ?? "unknown"), "hint"), element("h4", "Answer"));
      column.append(element("div", answerText, "answer" + (detail.judgment.outcome === "run_error" ? " error" : "")));
      if (answer) {
        const citations = Array.isArray(answer.citations) ? answer.citations.join(", ") || "none" :
          "invalid citation structure (see raw trace)";
        column.append(element("p", "Citations: " + citations + " · Abstained: " + String(answer.abstained), "hint hash"));
      }
      column.append(expandable("Expected behavior and rubric", detail.expectation));
      const evidence = element("details");
      evidence.open = true;
      const scripted = trace.origin === "fixture" || trace.origin === "test_double";
      evidence.append(element("summary", scripted ? "Scripted evidence — simulated" :
        trace.generation_attempted === true ? "Recorded request passages — model context unverified" : "Retrieved passages — no model request"));
      for (const passage of passages) {
        const item = element("div", null, "evidence-item");
        if (!passage || typeof passage !== "object" || Array.isArray(passage)) {
          item.append(element("p", "Malformed recorded passage; inspect the complete raw trace."), json(passage));
          evidence.append(item);
          continue;
        }
        item.append(element("p", passage.chunk_id + " · " + passage.document_id, "hash"),
          element("p", "Version scope: " + JSON.stringify(passage.software_versions)), element("pre", passage.text));
        evidence.append(item);
      }
      if (!passages.length) evidence.append(element("p", trace.retrieved_passages != null && !Array.isArray(trace.retrieved_passages) ?
        "Recorded passage data is malformed; inspect the complete raw trace." : "No passages recorded.", "hint"));
      column.append(evidence, expandable("Checks and recorded review", detail.judgment), expandable("Complete raw trace", trace));
      if (detail.review_form && detail.judgment.outcome !== "run_error") {
        const editor = element("details");
        editor.append(element("summary", "Record your answer review"), reviewForm(row, slot, detail.review_form));
        column.append(editor);
      } else column.append(element("p", "This record cannot be reviewed as a correct answer. Run errors and missing records remain in accounting.", "hint"));
      pair.append(column);
    }
    container.append(pair);
    const relation = element("div", null, "relation-review");
    const editor = expandable("Expected change between snapshots", row.relation);
    const tokens = state.relation_forms?.[row.case_id];
    if (tokens) editor.append(reviewForm(row, null, tokens));
    relation.append(editor);
    container.append(relation);
  }

  function sourceMode() {
    const existing = $("source-mode").value === "existing";
    $("run-path-field").hidden = !existing;
    $("run-path").required = existing;
    $("simulation-field").hidden = existing;
    $("simulation-hint").hidden = existing;
    if (existing) $("simulate").checked = false;
  }

  $("source-mode").addEventListener("change", sourceMode);
  $("load-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    message("");
    const existing = $("source-mode").value === "existing";
    const payload = {before: $("before").value.trim(), after: $("after").value.trim(), dataset: $("dataset").value.trim(),
      relations: $("relations").value.trim(), run_path: existing ? $("run-path").value.trim() : null,
      reference_labels: $("reference-labels").value.trim() || null, simulate_judgments: !existing && $("simulate").checked};
    try {
      const result = await request("/api/load", payload, "Loading and validating the complete comparison…");
      $("export-directory").value = "";
      replace("export-result");
      acceptState(result.state, true);
      $("inputs-panel").open = false;
      message("Records loaded. No inference was requested.", "success");
    } catch (error) { message(error.message); }
  });
  $("reload").addEventListener("click", async () => {
    try {
      const next = await request("/api/state", undefined, "Reloading current records and review revisions…");
      acceptState(next, true);
      message("Current records loaded. Review forms have been cleared.", "success");
    } catch (error) { message(error.message); }
  });
  for (const id of ["status-filter", "config-filter"]) $(id).addEventListener("change", renderComparisons);
  $("case-filter").addEventListener("input", renderComparisons);
  $("case-select").addEventListener("change", () => { selected = $("case-select").value; renderComparisons(); });
  $("export-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await request("/api/export", {directory: $("export-directory").value.trim()}, "Saving HTML and JSON reports inside the project…");
      if (result.state) acceptState(result.state);
      const links = element("div", null, "export-links");
      for (const [name, label] of [["report.html", "Open HTML report"], ["report.json", "Open JSON results"]]) {
        const link = element("a", label);
        link.href = "/download/" + name;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        links.append(link);
      }
      replace("export-result", element("p", "Reports saved inside this project. Links open the last successful export."), json(result.files), links);
      message("Report export completed.", "success");
    } catch (error) { message(error.message); }
  });

  sourceMode();
  request("/api/state", undefined, "Connecting to the local workspace…")
    .then((next) => acceptState(next))
    .catch((error) => message(error.message + " Confirm that the local server is running, then reload this page."));
})();
