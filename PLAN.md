# Current milestone: 5 ? Final evaluation and portfolio packaging

See `docs/MILESTONE_5.md` for scope and completion criteria.

- [x] Freeze inputs, run 60 cases across both snapshots/configurations, and retain raw evidence.
- [x] Run the fixed three-case variability subset and preserve errors and provenance.
- [x] Assess all main answers with hash-bound provisional AI assistance; keep human judgments separate.
- [x] Reproduce the JSON/HTML report offline from frozen source and raw archives.
- [x] Verify core wheel build, fresh isolated pip install, installed CLI/assets and fixture HTTP workflow.
- [x] Prepare README, architecture, dataset card, results, screenshots, demo script and case study.
- [x] Build the static portfolio package and 60–90 second demo script.
- [ ] Finish the final artifact audit and GitHub push.

The actual video is deferred at the user's direction and is not claimed by the
package. Browser automation and headless Chrome/Edge capture were unavailable
in this session; the three previously recorded actual UI screenshots remain.

Frozen protocol `a1f613c45be401fdf95a99ee9b47ef36261f7c7baa933eece8a4aaad1e1f23c4`
binds 324 source/configuration/fixture files. The frozen source passed 583
offline tests, zero failures/errors/skips (`25f2ca58950a4edcb05e740f1443b209`).
Execution run `3340520f537043c297e64eedce36daee` retained **240/240**
main records: four run errors, 24 deterministic policy abstentions, 216 chat
attempts and 212 completed model responses. The fixed variability subset
retained **36/36** records with zero errors; five of twelve cells had more
than one distinct answer object. Semantic differences were not adjudicated.

All 240 main records have hash-bound provisional AI-assisted proposals: 125 pass
(24 policy and 101 generated), 95 fail, 16 need human review, four run errors.
The new study has **zero human answer judgments**. Owner blanket approval covers
all 60 definitions; only 11 case definitions and one expected relation have
item-level human review. Forty-nine draft labels remain drafts. No human
accuracy or independent evaluator precision/recall is claimed.

The exact final JSON/HTML report reproduced offline from archived frozen source
and raw runs. See `docs/evidence/milestone5-study/` and
`docs/evidence/milestone5-analysis/final-study-report.json`. Main bundles 1?7
and review packets are published through `a18accb`; variability/final artifacts
await the final push.

A post-run validation-only fix requires both frozen model digests for answered
live rows; recorded answers were not changed. Current source passed **589**
offline tests, zero failures/errors/skips (`cc302a702b224bc1abb93b56956aaff2`).
The core package built, installed and served the fixture workflow again in
receipt `0085d125bf1b4f64b2b04b2b17300708`. Fresh full-ML resolution,
other platforms and OS peak memory remain unverified.

Next: complete portfolio packaging and final scope audit, then push and verify
GitHub. Keep AI proposals distinct from human judgments.

## Earlier checkpoints (preserved)

# UI refinement checkpoint

- User selected an overall UI improvement before portfolio packaging.
- Added a restrained teal/ink visual theme, local delta mark, workflow links,
  clearer comparison table, summary cards and distinct before/after panels.
- Fixture setup hides file paths in advanced options; choosing an existing run
  opens those options automatically. Readiness is displayed as labeled rows.
  Browser validation reveals collapsed required fields before focusing them.
  Fixture notices, draft labels and full run accounting remain visible.
- Verified startup and actual fixture loading in Microsoft Edge at localhost:
  20 drafts, 80/80 answer records, 40 comparison rows, 71 pending judgments and
  2 fixture run errors displayed. No model inference or review submission.
- Browser automation host was unavailable; native Edge inspection confirmed
  the initial and loaded layouts. A full viewport/browser accessibility matrix
  remains unverified. Existing CSS includes narrow-screen/reduced-motion rules.
- Final offline suite: 568 tests passed, zero failures/errors/skips, run
  `46d7dba3725a40a093a15ca501e60265`; real CLI checks also passed.
  Browser script syntax checked with Node. Final evidence:
  `docs/evidence/ui-refresh-final/`; initial check retained in `ui-refresh/`.
- Next: publish this UI checkpoint; continue UI refinements from user feedback.

## Earlier checkpoints (preserved)

# Pre-portfolio code audit checkpoint

- User requested a code audit and fixes before Milestone 5; packaging has not
  started. Broad source/test review covered snapshots/cases, chunking/retrieval,
  local inference, experiments, evaluation/review persistence, reports/UI and
  setup/download helpers. Brain independently reviewed evaluation/review/export.
- Six confirmed issues fixed: contradictory recorded configurations; simulated
  generation inside live traces; exports into `.venv-ml`; redirect bodies outside
  download accounting; incomplete cached Ollama receipts; incomplete cached
  Python receipts. Regression cases exercise the faults without network/models.
- Full offline suite: **568 executed, zero failures/errors/skips**, run
  `9c9c70b5d60a45f9ab3634e156b3aec4`, Windows/Python 3.15.2 with verified source
  dependencies. All 213 tested source/configuration/fixture files unchanged
  during execution. Real foundation CLI checks also passed.
- Read-only compatibility probe reproduced original 128/256-token outcomes,
  four published human-review counts/metrics, and four unresolved genuine-case
  answers. Cached Python (2208 files) and Ollama (75 files) passed stricter
  checks without native execution. No new model calls/downloads or journal edits.
- See `docs/CODE_AUDIT.md` and `docs/evidence/pre-portfolio-code-audit/` for
  reproducible commands, raw evidence, fixes and remaining verification limits.
- Next: publish/hash-reconcile this audit under standing push authorization;
  report completion. Milestone 5 remains a separate next step.

## Earlier checkpoints (preserved)

# Milestone 4 closure checkpoint

- Required implementation and exploratory evaluation artifacts are verified;
  goal closure follows remote publication/hash reconciliation.
- Eleven actual case-definition approvals:ten main plus one genuine revision.
  Four main-run answer judgments and expected relation are recorded exactly as
  approved; one observed basic regression and filtered recovery, with causality
  and post-hoc selection limits disclosed.
- Main256-token run40/40structured,0errors; baseline128had22/40structured.
  Cap controls matched exact prompts/evidence/model across all40rows.
  Citation-version flags2/20basic versus0/20filtered; no semantic generalization.
- Genuine source clarification:approved case/relation, new4-record live run with
 0errors; actual answer judgments remain explicitly ungraded unless the optional
  review card is answered. Old draft diagnostic and frozen labels are preserved.
- Fixed-subset repeats36records:6structured/30runerrors at128tokens. Additional
  identical-request observation shows No/Yes variability; document addition is
  not established as sole cause of the observed regression. No answer caching.
- Latest519offline tests passed with0failures/errors/skips;212tested source
  files unchanged. Test-only60case capacity validates20/40split plumbing and
 240records/HTMLJSON without claiming a reviewed60-case benchmark.
- Public human-label files reproduce counts/metrics without private SQLite/model.
  Independent-reference labels absent:testerprecision/recall stay unavailable.
- All reports/raw records archived losslessly; models/environments/keys excluded.
  Resource scan about5.42GB within12GB; setupledger3.41GB within5GB,CPUdependency
 348MBwithin1GB. No new model downloads or security changes during evaluation.
- Broader60-reviewed-case target and held-out evaluation remain unfinished and
  disclosed. Milestone 5portfolio packaging awaits user instruction.

## Earlier checkpoints (preserved)

# Current state — operational experiments verified; human answer review pending

- All 10main Pydantic case definitions explicitly human-reviewed. Latest3approvals
  recorded2026-11-06; old runs retain frozen7-reviewed/3-draft dataset metadata.
- Original128-token main40records:22structured/18errors; repeat36:6structured/30errors.
  Separate256-token main40:40structured/0errors,841.381s; cap-only controls checked
  against all 40baseline prompts, exact passages, requests and model identity.
- Mechanical incompatible-citation flags:basic2/20, filtered0/20. No semantic
  improvement or independent evaluator precision/recall claimed.
- Genuine pinned parent/child warning addition:1draft case,4live records,0errors,
 78.120s. Unknown release applicability visible; no software behavior change claim.
- Latest source/dataset verification:518tests passed,0failures/errors/skips,
  run3c629f3f9b324c909205beb2ad4b247b; exact211source files captured. A prior web
  timeout remains preserved; isolated test and subsequent full suites passed
  without changing the test. Failure root cause is unverified.
- Raw runs and self-contained HTML/JSON exports packaged losslessly and byte-checked;
  models, environments, keys excluded from publication.
- Actual-answer review card queued for dict-pairs across both snapshots/configs,
  selected after inspection as an assisted diagnostic subset, not representative.
  No answer/relation judgments saved before explicit human approval.
- Remaining M4gate: actual human answer judgments and honest reviewed findings.
  Genuine-case expectations still draft. No held-out evaluation;60reviews is an
  unfinished target, never a fabricated dataset/review count.

## Earlier checkpoints (preserved)

# Current next step — separate 256-token experiment running

- User resumed work after pause; no restart/replacement of completed runs.
- Original main run retained40/40records,22structured answers,18run errors,
  60chatattempts,1117.842s. All38rejected attempts hit128tokens with length stop.
- Fixed3-case/3-repeat study retained36/36records,6structured answers,30errors,
  753.579s. All60rejected attempts hit128tokens. No answer caching.
- Main report flags1citation-version incompatibility,21unresolved results and
  18errors. Zerohuman answerjudgments; nosemantic accuracy/regressionclaim.
- Exported real HTML/JSON reports, packaged complete raw evidence losslessly;
  archives byte-verified against originals. Models/environments/keys excluded.
- Added explicit --max-output-tokens128/256, default128 unchanged.498offline
  tests passed, zero failures/errors/skips, run8cbe3a4939074220b3d89668fc5e2c4e.
- New256-token protocol frozen before its full40-record run. Only outputcap
  intentionally changes; must verify prompt/evidence identity against baseline.
- Next: retain new results, export and compare completion with full denominators;
  human answers/case reviews, genuine-revision study and held-out dataset remain.

## Earlier checkpoints (preserved)

# Current next step — frozen Pydantic live comparison running

- Normal-terminal Ollama discovery matched expected digest; ten live CPU smoke
  requests completed with ten structured answers, zero run errors, same model
  and settings, thinking disabled, no caching. Full command122.453s, pipeline
  median11.009s. Ollama reports zero VRAM; OS peakRAM and correctness unmeasured.
- Brain independently audited raw smoke traces and confirmed these limited claims.
  No fallback model or security/ACL change. Earlier access cause remains unknown.
- Frozen existing Pydantic development protocol before inference. Main40-record
  comparison is running: ten cases x two snapshots x basic/version-filtered.
  Seven human-reviewed case definitions, three drafts; zero answer judgments.
- Predeclared variability subset remains serialization/optional/union, three
  repetitions across both snapshots/configurations (36 planned records).
- Actual smoke/discovery/raw model metadata and initial wrong-input error are
  preserved separately. Ordinary tested source unchanged:494offline tests.
- Next: retain full main results/errors, run fixed variability subset serially,
  export ungraded reports, and request actual human review. Held-out dataset,
  genuine-revision experiment and portfolio packaging are unfinished.

## Earlier checkpoints (preserved)

# Current next step — normal-terminal native model discovery

- User Qwen download succeeded: all config/layer hashes and raw manifest passed;
  shared ledger now reserves 3,411,696,918 bytes of approved 5 GB.
- Agent-started native Ollama reports 0.40.14 but empty inventory and manifest
  Access is denied. No inference attempted. Owned server stopped; subsequent
  exclusive IPv4 localhost port bind succeeded.
- Root and Brain confirmed correct V2 regular-file layout, exact manifest hash,
  Python readability and user FullControl ACL. Native path-traversal/sandbox
  access is plausible but unproven. No security/ACL changes are authorized or
  required for the next diagnostic.
- Next: user starts existing verified launcher in normal PowerShell, same cache;
  inspect tags/digest, then run ten-question CPU smoke if discovery succeeds.
  See docs/QWEN_DISCOVERY_STATUS.md. No repeat download needed.
- Source unchanged since 494-test checkpoint; this update preserves actual
  setup/discovery evidence and documentation only.

## Earlier checkpoints (preserved)

# Current next step — explicit pinned Qwen download

- Ollama runtime preparation succeeded; archive and executable hashes verified.
  Temporary localhost server reported 0.40.14 and an empty model list. Root
  stopped its owned server and positively acquired an exclusive IPv4 bind on
  127.0.0.1:11434 afterward. No answering inference has run.
- Prepared explicit qwen3:1.7b cache importer: exact raw manifest SHA256, full
  blob checks, persistent global transfer ledger, V2 named manifest last,
  exclusive localhost port guard and no automatic server/pull. Redirect bodies
  are closed without consumption. Brain found and reviewed that fix.
- Full verification: 494 tests passed, zero failures/errors/skips, run
  cdc74fdc5b0a411eb7779d413942f01a, plus real CLI checks. An earlier full run
  exposed Windows staging filename length failures; shortened unique staging
  names corrected them. Earlier failed evidence is retained separately.
- Actual setup evidence and earlier HTTP 504 remain preserved. Global artifact
  ledger reserved 2,052,402,609 bytes before Qwen; model payload 1,359,293,444
  bytes fits remaining allowance. No download started by this implementation.
- Next: docs/QWEN_CACHE_SETUP.md command in normal user PowerShell (shell public
  networking remains restricted), then native discovery/digest check and ten-query
  CPU smoke. Cache success alone is not inference success. Human answer review,
  controlled results and remaining dataset work are pending.

## Earlier checkpoints (preserved)

# Current next step — local answering runtime

- Actual pinned MiniLM ONNX assets downloaded and verified: 91,115,253 bytes.
  Live CPU smoke passed 4x384 finite unit embeddings, duplicate/batch checks,
  Unicode offsets and 256-token boundary/overlength rejection. torch absent.
  Model load 1.4823 s; encoding/checks 1.0130 s on this fixed constructed smoke.
  These are observations, not a general latency benchmark or Torch comparison.
- Independently ran real NumPy retrieval over separate Pydantic snapshot indexes:
  26 before chunks / 86 after chunks; 40 queries passed snapshot/version contracts,
  24.1069 s total. No answering model or correctness measurement. Exact traces
  and asset/configuration identity are preserved in evidence.
- Prepared pinned Ollama 0.40.14 portable runtime setup: bounded directory
  preflight, full archive SHA256, single-copy contained extraction, shared global
  transfer accounting, version-only native check and progress. Default offline;
  explicit --prepare required. No server/model pull or policy change.
- 462 offline tests passed, zero failures/errors/skips, run
  9b72b54650124a6bbfd90c2bfc6bbbd5. Actual Ollama/native engine and Qwen answers
  remain unverified. Next command: docs/OLLAMA_RUNTIME_SETUP.md.
- User prefers Brain consultation only for genuine decisions/blockers/reviews.
  Brain verified current Ollama cache stores raw manifests/blobs and warned of
  V2 layout. Root subsequently inspected official manifest/paths.go: V2 preferred,
  public-host canonicalization to ollama.com, legacy fallback and blob naming.
  Future direct importer must reverify hashes and write named manifest last.
- Dataset remains seven reviewed development cases / three drafts in Pydantic;
  no held-out/human answer judgments or controlled answer results are invented.

## Earlier checkpoints (preserved)

# Current next step — real ONNX embedding model smoke

- User resumed implementation and asked to consult Brain only for genuine needs.
- Actual ONNX Runtime 1.31.1/NumPy2.5.4/tokenizers0.23.3 compatibility passed under
  .venv-ml; CPU provider present, torch absent. Original blocked PyTorch evidence
  remains historical and unchanged. No model weights are present yet.
- Implemented pinned direct ONNX MiniLM adapter, explicit ~91.1 MB downloader,
  and a separate real-model smoke. Tokenizer never truncates, input limit256
  includes specials, exact graph inputs/output/provider are checked, and masked
  mean pooling/L2 normalization plus backend versions/hashes are recorded.
- Brain identified active-runtime provenance and ORT-specific error handling gaps,
  then a cumulative-report-key typo. All corrected with focused regressions.
  452 tests executed/passed, zero failures/errors/skips, run
  c78a00adec534bf29c71c9050837b327. Actual .venv-ml runtime gate passed without
  network/download. Embedding inference is still unverified until the explicit
  download/smoke command succeeds. See docs/ONNX_EMBEDDINGS.md.
- Three answering/run CLIs accept explicit --embedding-backend onnxruntime;
  no silent fallback. Ollama/Qwen setup and ten-query hardware test remain pending.
- Pydantic review remains seven genuinely reviewed cases and three drafts. No
  human live-answer judgments or controlled live benchmark results exist.

## Earlier checkpoints (preserved)



## Approved separate ONNX compatibility test (2026-11-05)

The user approved testing ONNX Runtime CPU for the same upstream MiniLM model.
This is a separate backend candidate, with no blocked PyTorch DLL reuse or
security change. NumPy 2.5.4 and tokenizers 0.23.3 actually imported under
.venv-ml with torch absent from sys.modules. ONNX imports/providers and model
execution remain unverified. scripts/setup_onnx_runtime.py defaults to an offline
plan; explicit --test performs bounded dependency inspection, missing-package
installation and import/CPU-provider checks. It downloads no model weights and
shares the existing resource ledger. See docs/ONNX_COMPATIBILITY_TEST.md.
Preparation verification: 426 tests passed, zero failures/errors/skips, run
ce78b874f27144528c57a79c8c524f0b. An initial synthetic reader fixture error
was corrected; the earlier failed evidence is retained. Actual ONNX Runtime
installation/imports and model execution remain pending.

A direct ONNX embedding adapter and actual model validation would follow only
after a successful compatibility result; no silent model/backend substitution
or retrospective PyTorch improvement claim is permitted.

# Current state — Milestone 4 authorized and in progress

- On 2026-11-05 the user authorized real local model/embedding runs, genuine
  documentation, human-reviewed cases, controlled experiments and measured results.
- The user separately approved 12,000,000,000 bytes total project storage and
  5,000,000,000 bytes additional artifact payload including retries, with at most
  1,000,000,000 bytes for CPU embedding dependencies. These supersede the UI-only
  resource limits for this explicit setup; no global installs or security changes.
- First source batch: ten development cases using pinned MIT Pydantic
  documentation. A=v2 excerpts; B=same excerpts plus v1 models. Snapshot assembly
  is constructed, source material genuine. Seven explicit human case reviews, three drafts; zero human answer reviews or live results.
- Implemented offline source/excerpt/case verification and explicit bounded model
  metadata preflight. Full dependency closure/space planning and native execution
  remain pending. See docs/MILESTONE_4.md, docs/EVALUATION.md and
  docs/MILESTONE_4_RESOURCE_PROPOSAL.md.
- User reported loading and inspecting scripted replay in the new local web UI.
  This is a manual workflow observation, not an automated visual/layout audit or
  dataset correctness review.
- Verified checkpoint: 389 offline tests passed, zero failures/errors/skips, run
  edaa1763bbb84c20b6f79524a448245f. Actual CLI verified the source bundle and
  exported 40 clearly simulated Pydantic records: all await semantic review,
  no live generation. The larger-source fixture prompt overflow was reproduced
  and fixed with traceable fixture-only quote windows; live retrieval is unchanged.
- The agent shell's five bounded metadata requests failed with WinError 10013.
  No assets were downloaded. The normal-terminal metadata command is the next
  external execution step; its report must be inspected before installation.
- The normal-terminal model metadata report arrived: all five sources responded.
  Exact Qwen layers total 1,359,293,444 bytes; pinned MiniLM assets total
  91,578,415 bytes. CPU candidate selection rejected the official
  download-r2.pytorch.org CDN; the inspector host check was corrected and a
  positive CDN/interpreter-tag regression plus negative host/ABI checks added.
  Existing user-terminal report is preserved; no assets were installed.
- Corrected normal-terminal model metadata inspection succeeded for all five
  sources. CPU candidate: torch 2.15.0+cpu, cp315 Windows AMD64. Exact wheel
  size, complete dependency closure and expanded archive footprint remain pending.
- Implemented explicit embedding dependency preflight: metadata/range reads only,
  compatible CPU root, full transitive constraints, declared archive expansion and
  persistent transfer reservations shared by future model setup. Default is offline.
  400 tests passed, zero failures/errors/skips, run 1e2a0fe730654099bb475167d8fa55f6.
  An initial test fixture used an invalid hyphenated wheel filename; corrected it
  to escaped wheel syntax. Earlier failed evidence is preserved. No packages or
  model weights were downloaded/installed to implement or test the preflight.
- CPU package setup is prepared behind successful dependency inspection, with
  a read-only default, full wheel/METADATA/edge verification, preserved existing
  versions, shared CPU/global retry budgets, bounded local subprocesses and
  explicit native-import failures. No installer execution is claimed.
- Brain found cumulative CPU metadata reads could exceed the CPU suballowance;
  a shared guard now applies before both metadata and install body reads.
  Brain's further review stopped at a workspace credit limit; no full independent
  installer clearance is claimed.
- run_local_cases now saves raw UTF-8 JSON with --output, retaining error records
  on nonzero exit and refusing existing/outside targets before inference. A
  post-start exception no longer falsely asserts no generation occurred.
- 411 tests passed, zero failures/errors/skips, run
  64b21ff0c72348c5bf77ecd6222446e0. Genuine case review count: seven; three
  pending. No live model answers, human answer judgments or scores yet.
- The normal-terminal CPU dependency check reached 26 metadata requests, then
  stopped on SymPy's historical invalid release label 0.5.13-hg. No packages or
  model weights were installed/downloaded. 13,208,336 metadata bytes were received;
  cumulative model-setup transfer reservations are 14,391,199 bytes. The original
  error report is preserved. A repeated default command refused to overwrite it.
- The bounded resolver now skips invalid historical release labels, retaining
  strict compatible-wheel, metadata hash and dependency checks. Its regression
  reproduces the observed legacy label alongside a valid modern candidate.
- The corrected normal-terminal dependency run then stopped on PyYAML: its
  official files index has cp314 Windows wheels but no cp315 wheel. No packages
  or weights were installed/downloaded; cumulative reservations are 29,147,369 B.
- Prepared a separate repository-local Python 3.14.10 ML environment. The official
  core AMD64 ZIP is pinned by the Python release manifest SHA256; metadata and
  expansion precede download, files are checked before native execution, venv and
  child state stay local, and native policy errors stop execution. No global
  registration/PATH/security change. Existing 3.15 UI/test environment is retained.
- scripts/setup_ml_python.py defaults to offline planning. Explicit --setup would
  provision .tools/python-3.14 and .venv-ml, then inspect model/CPU dependencies
  under that actual interpreter. It installs no ML packages and no model weights.
  Runtime zip/ranges count against CPU/global budgets; candidate metadata has
  a conservative global reservation. Actual 3.14/native operation remains pending.
- Verification: 419 tests executed and passed, zero failures/errors/skips, run
  dc3a03b979054a688979597a5bde8563. Tests use inert synthetic runtime ZIPs and
  do not establish actual Python 3.14/native operation.
- Actual local Python 3.14.10 setup succeeded: 32,987,388-byte official archive,
  118,369,853 declared expanded bytes, exact hash/receipt checked. The isolated
  .venv-ml interpreter and repository-local base prefix were probed successfully.
- Actual 3.14 dependency inspection resolved 42 wheels: 223,215,045 compressed
  and 794,380,947 declared expanded bytes; conservative dependency plan fits
  the approved storage/transfer limits. Package imports remain a separate gate.
- First CPU install stopped at mdurl on DNS resolution. The user resumed and
  reached setuptools; our validator counted nested vendored dist-info metadata
  as duplicate top-level metadata. Fixed to select the single top-level wheel
  METADATA, keeping full SHA/name/version/dependency checks. Regression also
  retains rejection of multiple top-level metadata roots. Failed-transfer reports
  now record latest persistent reservations even when download/validation fails.
- 422 tests passed, zero failures/errors/skips, run
  db9a1dfb948942b9beb0328d97cf1289. Real read-only resumption plan passed under
  .venv-ml: 31 packages already match, 11 pending, 152,040,561 bytes reserved
  for remaining payload; conservative planning 2,414,633,175 bytes. No native
  ML import, model weight download or inference success is claimed.
- The user resumed installation: all 42 dependency versions are now installed
  (31 existing matches, 11 installed this attempt). The final import check failed
  before readiness: Windows Application Control rejected torch_python.dll,
  WinError 4551. Event 3077 names VerifiedAndReputableDesktop, policy GUID
  0283ac0f-fff1-49ae-ada1-8a933130cad6, and the exact DLL flat SHA256.
  Authenticode reports NotSigned. DLL bytes/size match its installed RECORD;
  the installer recorded matching full wheel SHA256. No tampering or malware
  conclusion is inferred from those observations.
- Stopped the blocked PyTorch execution path. No reinstall loop, native import
  retry, alternate DLL/loader, policy change or model download was performed.
  Preserve logs/reports in docs/evidence/milestone4-torch-policy-block.
- Actual project logical footprint observed: 1,469,571,044 B; global transfer
  reservations 328,879,784 B, CPU dependency reservations 317,696,941 B, within
  the approved limits. No model weights or live inference.
- Live Milestone 4 acceptance is blocked pending a legitimate publisher/Microsoft
  review or policy-compatible path. No external contact/upload is authorized or
  performed. Stop repeating the installer; keep Windows protection enabled.
- Continue independent source/review work where possible and freeze genuinely
  human-reviewed cases, install only validated assets and execute controlled runs.

## Historical Milestone 3 checkpoint (preserved)

# Standard-library UI checkpoint

- The user explicitly approved option 1 on 2026-11-05: replace Streamlit as the
  default UI with Python standard-library HTTP plus HTML/CSS/JavaScript. Keep
  Smart App Control On. No blocked native file or protection setting was modified.
- New entry point: scripts/run_web.py --serve, bound to 127.0.0.1:8501. Existing
  controller/metrics/review/export behavior is reused. Loading records makes no
  model requests. Legacy Streamlit and its installation evidence are retained.
- Focused real HTTP checks passed, including fixture/load/import/review/export,
  stale-revision rejection and a subprocess with third-party imports disabled.
  The verified full suite executed 373 tests with zero failures/errors/skips,
  run 797bcc303da64a88bdb4534e430bf23b. Evidence:
  docs/evidence/milestone3-local-web-verified. Earlier observations are preserved:
  milestone3-local-web passed on the initial source; milestone3-local-web-final
  exposed a Windows TCP reset on rejection with an unread body. Consuming bounded
  request bodies before rejecting actions fixed that response path.
- Browser automation host access was unavailable. Native browser verification
  was stopped after detected user activity changed the active tab. No new-app
  screenshot or successful visual interaction is claimed. User visual review is
  the next acceptance step; see docs/LOCAL_WEB_UI.md.
- The 750 MB folder ceiling and 150 MB artifact allowance remain in force. The
  new UI requires no additional package or model download. This historical checkpoint
  preceded the user's subsequent Milestone 4 authorization.

## Earlier UI setup observations (preserved)

- The user's approved setup installed all 34 locked packages. The final import
  check failed on an unsigned pandas native module, with Code Integrity event
  3077 naming VerifiedAndReputableDesktop. No security settings were changed.
- Independent NumPy/PyArrow imports succeeded. The actual NumPy integration suite
  executed 15 tests, all passing, with labeled tokenizer/vector doubles. This is
  not live model integration. Evidence: docs/evidence/milestone3-ui-installation.
- Download reservations are 86,786,569 bytes of 150 MB; later folder inventory is
  371,959,665 logical bytes of the 750 MB allowance. No installation peak is claimed.
- Next: confirm the Windows Security protection state and identify a legitimate
  policy/publisher resolution. Do not redownload or rerun the blocked native import
  merely to repeat the same failure. Streamlit rendering and live inference remain
  unverified. See docs/MILESTONE_3_UI_INSTALLATION_STATUS.md.

- The user's normal-terminal inspector completed successfully. The saved report's
  source hash, selected wheel tags, active dependency constraints and totals were
  independently checked offline. It resolved 34 candidate wheels: 86,786,535 bytes
  compressed and 280,478,795 bytes of declared expanded files. No installation.
- These packages alone exceed the former 250 MB total-folder ceiling. The user
  approved 750 MB total storage and at most 150 MB future UI artifact
  transfer; the conservative plan using the later larger folder inventory is
  694,104,324 bytes. Actual installer peak is unverified. Neither requested limit
  is an open-ended allowance. Models remain excluded.
- The bounded setup helper and its 17 focused offline tests are implemented.
  The full suite executed 358 tests with zero failures/errors/skips, run
  712d4f2b0aab427ba5a2453a3cd09c70. Actual default-plan execution returned ready
  with 34 pending packages and made no network requests or installation changes.
  Evidence: docs/evidence/milestone3-ui-setup-helper. Real setup/imports remain
  unverified until the normal-terminal installation command runs.
- Next action: use the user's working normal-terminal connection for explicit UI setup.
  Preserve the approved wheel lock, resource ledger and original inspector output.

- User authorized fixture-based Milestone 3. On 2026-11-04 the user retired
  Deliverer, briefly required milestone push approval, then explicitly granted
  all push permissions again. The primary agent handles tested repository
  checkpoints directly until that instruction changes.
  Keep all intentional files project-local,
  preserve remote work, spend zero, avoid global/model installs, and stay below
  the newly approved 750 MB UI-only ceiling. Non-model UI dependencies may be set up within that ceiling
  after full compatibility/footprint checks; none have been installed.
- Published saved-run/metrics checkpoint: 0dfa9ac1b6b71f5c5b7aaabe23a5c02db0f497bb,
  with 294 passing tests and all 127 remote source hashes reconciled. Prior proof
  and sample artifacts remain historical records.
- Current unit exposes optional independent reference-label JSON and abstention
  judgments through the controller, CLI and UI source, preserving them in escaped
  exports. Reference inputs are project-local lists capped at 16 MiB, require exact
  result bindings and default to no labels. Fixture metrics remain ineligible/null.
  The actual offline run executed 313 tests with zero failures/errors/skips,
  run 8d929a4f44d04dbd822b7a85115f1347, source ID
  90d3cd8df8d4ffe705faf951e8f73709eec78619ba2bbe65dc401578b5db6fc0.
  Evidence: docs/evidence/milestone3-measurement-inputs. Brain independently
  verified all 129 source hashes and the 313-test evidence and found no blocking
  issue. Actual empty-reference CLI inspection/export retained 80 fixture records,
  zero human reviews and null scores; synthetic labels exist only in tests.
  The user approved the tested checkpoint and then granted all push permissions
  on 2026-11-04. Published commit bf3a8a1187d175477595fd64659418d3b849437d
  contains its 16 files plus two metadata-only UI proposal files. All 129 tested
  source files match the published Git objects; all 53 prior evidence/sample
  files are unchanged. No package/model installation or storage expansion was
  authorized by the push instruction.
- The broader workflow audit identified and fixed a substantive gap: the review
  controller now imports saved raw experiment JSON as well as replaying fixtures.
  Manifest/dataset/origin checks preserve original answers/evidence; no gold-answer
  regeneration or new inference occurs during import. CLI/UI controls identify
  the selected configuration and repetition.
- Separate assistant and testing-tool metrics retain honest denominators, errors,
  missing judgments and provenance. Assistant accuracy needs eligible reviewed
  live results. Failure-flag precision/recall needs independently attested
  reference labels; identity/execution claims are not authenticated.
- Historical published source ID:
  55635b9d92192d36dcd4768c3e04085129237447399654898c690d717bee16c8.
  Run 026df346a922443abf76d9bc9181c8a4 executed 294 tests with zero failures,
  errors or skips. Brain independently checked all 127 source hashes and the
  final CLI preservation/provenance proof, clearing this bounded checkpoint.
- Evidence: docs/evidence/milestone3-run-import-final. Actual saved-run CLI
  imported/exported 80 fixture records and 40 comparisons with input bytes
  unchanged, zero human reviews, no inference and null assistant accuracy.
  Earlier docs/evidence/milestone3-run-import remains intermediate history.
- Current twenty constructed development cases remain drafts. TEST-ONLY temporary
  database reviews are not real human validation. Historical simulated samples
  demonstrate seven comparison statuses, not measured assistant performance.
- Published historical fixture checkpoint 2c9e9d5 recorded 250 tests and 115
  reconciled remote source hashes. Historical interface checkpoint 4c270e0 recorded
  266 tests and 124 remote source hashes. Their evidence/sample reports remain
  preserved; the older local 257-test controller run is also historical.
- Real Streamlit remains unavailable: historical readiness returned missing package/
  exit 2 without state changes, real AppTest returned unavailable/exit 1 with zero
  UI checks verified, package/HEAD probes failed network access, and base/user-site
  inventory found no usable installation. Controller tests do not verify rendering,
  browser interaction, actual launcher containment or live model integration.
- The user reported HTTP 200 from the requested normal-terminal PyPI HEAD check.
  Agent-side PyPI requests still fail with WinError 10051. This identifies a manual
  inspection route, not a successful installation or a budget change. The bounded
  setup inspector now passed 341 offline tests with zero failures/errors/skips,
  run f65c4026fd3b47d188990fc008e0823e. Evidence is in
  docs/evidence/milestone3-ui-preflight-final. The earlier 340-test observation
  is retained as intermediate evidence before the output-preservation fix.
  The script is ready for an explicit normal-terminal run. It reads metadata and
  bounded archive ranges, installs nothing, and refuses to overwrite existing
  files. Actual dependency/expanded-size resolution remains unverified until run.
- Last folder measurement: 78,348,353 logical bytes including ignored artifacts,
  below 250 MB. No package/model downloads or global installation occurred.
- Earlier metadata-only preparation is preserved in
  docs/MILESTONE_3_UI_DOWNLOAD_PROPOSAL.md. The successful user-run inspection and
  new explicit budget proposal above supersede its unresolved-closure status.
  Actual UI/live acceptance still needs missing dependencies/runtime/assets.
  Milestone 3 is incomplete. Do not advance to Milestone 4 or add speculative
  placeholder features. See docs/MILESTONE_3.md and docs/MILESTONE_3_INTERFACE.md.

## Milestone 2 checkpoint - offline work complete; live acceptance blocked

- User authorized Milestone 2 work and waived per-push approval until further notice.
  This does not authorize additional downloads or installations.
- Local chunking, question/prompt/response contracts, embedding/index adapters,
  bounded localhost Ollama client, and single-question orchestration are implemented.
- Added explicit scripts/answer_question.py and process-local offline/cache
  configuration; the command requires separately installed assets and dependencies.
  Missing-assets exit code 2 is tested; successful live execution is unverified.
- Added full-dataset scripts/run_local_cases.py orchestration for both snapshots
  and retrieval configurations, repeated runs without answer caching, and retained
  error denominators. Draft cases and double outputs are not benchmark results.
- Published smoke unit: ten-question smoke harness, explicit CLI, constructed
  hardware-only inputs and residency observations; offline checkpoint reviewed.
  New evidence is separate in docs/evidence/milestone2-smoke-contracts: 195 executed
  tests, zero failures/errors/skips, plus real CLI checks. Brain approved the
  limited checkpoint with all 55 tested source hashes independently matching.
  Run f26de47c60b1430783205d64ef8c0e9c; source ID
  78c2e05518dfdfcefd1436bb823dfee45c03e7eaf07e8b2a5dcf5ab3720efd80.
  No live measurements are claimed; CPU observation differs from requested control.
- Published readiness unit: explicit real-NumPy integration checks and contained
  Windows runtime planning/start controls. Final source run executed 206 ordinary
  tests with zero failures/errors/skips, plus real foundation CLI checks. Actual
  read-only runtime plan returned missing_runtime/exit 2 without state changes or
  native execution. The separate NumPy attempt was unavailable (exit 1, zero verified
  numeric checks). All three observations use the same frozen source identity.
  Brain approved the limited readiness checkpoint: all 59 source hashes match,
  and ordinary checks, runtime-plan and unavailable integration evidence agree.
  Native runtime execution remains unverified; tests use explicit process doubles.
- Current evidence run: f196d7458a5f46d894857666e69224ca; source ID:
  6d56aeec4f6fb6e242aada783465786d01e8ea2205fbd325f4f1da18b0dde188.
- Offline verification uses explicitly labeled tokenizer/index/transport doubles.
  Published pipeline checkpoint executed 183 tests with zero failures/errors/
  skips, plus real foundation CLI checks, on Windows/Python 3.15.2 with verified
  source-import test dependencies. Brain approved this limited offline checkpoint
  and independently verified all 49 source hashes and the final regression fixes.
  Real NumPy, sentence-transformers, Ollama inference, and hardware performance
  remain unverified.
- Evidence run: 2e4af53709f549b38fa16cae66932cc3; source ID:
  293ce31f394b3f5205cd31b8ef190fde6ee58b0c6eb32dea0784d0463b2c7aa0.
- Fixed repeated-offset chunk progression and forged chunk metadata; regressions
  protect snapshot/evidence identity without claiming semantic correctness.
- User deferred the 12 GB / 4 GB resource proposal; the existing 250 MB folder
  ceiling holds. Continue independent implementation without asking again now.
  No new ML/model downloads were performed for the contract checks.
- Pipeline 74ca2f6 and smoke e9ff0c0 are published; all 49/55 corresponding remote
  source hashes were reconciled. Their evidence is preserved historical data.
- Readiness checkpoint ddc9862540157c45a51da303701b578d8ba95924 is published;
  all 59 remote source hashes match its recorded manifest. Its scoped observations
  remain 206 passing ordinary tests, missing runtime/exit 2, and unavailable
  NumPy/exit 1 with zero verified numeric integration checks.
- Independent Milestone 2 implementation, preflight and scaffolding are complete.
  Remaining real acceptance is blocked by missing ML dependencies/runtime/assets
  and the user's deferred expanded-resource authorization. No renewed request now.
- Next: only when resources are later authorized, verify real numeric/embedding
  imports and live inference, measure ten CPU queries, and check native write
  containment. Milestone 3 fixture work is separately authorized above; it does
  not complete or replace these live Milestone 2 acceptance checks.
- Existing folder footprint is approximately 14.6 MB under the 250 MB ceiling;
  zero project spending and no new model/runtime assets.
- Milestone 2 is not complete. See docs/MILESTONE_2_PROGRESS.md.

## Historical records - superseded status and authorization

The entries below preserve earlier observations. Their current/next instructions,
per-push approval statements, and "Milestone 2 unstarted" status describe past
stages. Current authorization and work status are stated above.

# Earlier Milestone 2 readiness - download approval pending

- User authorized Milestone 2 work and revoked per-push approval until further notice.
- Existing Python 3.15.2 is an installation candidate; published CPU/native
  wheels were checked, but the full ML resolution/imports remain unverified.
- Prepared docs/MILESTONE_2_DOWNLOAD_PROPOSAL.md and machine-readable metadata.
- Request: 12 GB folder ceiling and 4 GB initial-download ceiling; estimated
  initial transfer 3.2–3.6 GB, including a 500 MB CPU-wheel allowance.
- Only metadata was retrieved. No large downloads, global installations,
  model inference or embedding run occurred. The current 250 MB limit holds.
- Shell networking remains restricted. A reviewed repo-local command may need
  to be run in the user's normal terminal if the restriction remains.
- Next: obtain resource approval, preflight complete assets/hashes/expanded ZIP
  totals, then implement and verify the defined Milestone 2 pipeline.
- Keep ordinary tests/startup offline and all caches/profile/state inside the folder.

## Previous audit history

# Current audit status

The complete Milestone 1 audit found verification/input gaps missed by the
original suite. The user approved publication of the reviewed audit fixes.

- Latest run: 92 executed tests, zero failures/errors/skips, real CLI checks.
- Actual inherited collect-only/plugin/optimization settings were ignored.
- All 34 tested source hashes independently checked by Brain.
- Source ID: a489c9c88098203b30366d4fe9aebfa0a9222277a8d1c5f483329c366503afa6.
- New evidence: docs/evidence/milestone1-audit; original 52-test evidence retained.
- Corrected stale-success, environment overrides, concurrent writers, JUnit
  validation, reserved/special paths, JSON errors, redirects/response limits,
  evidence placement and dependency hash checking.
- Scope and setup limits remain explicit in docs/MILESTONE_1_AUDIT.md.
- Next: publish the approved update, reconcile published source hashes, and hand off the audit.
- Milestone 2 remains unstarted.

## Earlier Milestone 1 history

# Plan and current state

## Milestone 1 — verified source-run configuration

Completed:
- Strict immutable snapshot and case schemas; exact content/metadata hashes.
- Deterministic additions, removals, edits and manifest metadata changes.
- Readiness command with disk information, explicit unknown hardware, and
  opt-in localhost model inventory.
- Two constructed snapshots and seven draft development cases.
- Source-only isolated test environment using existing Python 3.15.2.
- Three review fixes: actionable resolution errors, invalid Unicode rejection,
  and same-domain dataset validation, with regression tests.
- Reproducible offline runner and real subprocess CLI checks.
- Exact dependency releases, source provenance, source hashes, raw output,
  JUnit results, environment observations and Windows instructions.

Checks actually run:
- Original remote state inspected at 3026066735e6a6ed8379a5361ba1fbc98fc786a8;
  initial foundation delivered as 884e48301f10ba3cb447aa84635f318ae6c923bc.
- Local source copy reconciled byte-for-byte against all 38 original Git blobs.
- Actual isolated CPython 3.15.2 execution: **52 pytest tests passed**.
  Saved JUnit: 52 tests, zero failures, errors or skips.
- Real compare command matched expected-diff.json exactly.
- Real validate-cases reported seven drafts and zero human reviews.
- Default doctor ran without service calls/downloads; invalid CLI input returned
  a JSON error and exit code 2.
- Tested project source hashes captured before/after execution; unchanged.
- Five official dependency source trees and their generated version metadata
  verified against recorded hashes before use. The unchanged packaging copy
  has separately recorded origin/version and SHA256 hashes.
- Git 2.56.0.windows.3 and an Intel x64 processor identifier observed;
  environment reports 12 logical processors.
- Disk free space observed. RAM/GPU queries denied; reported 16 GB RAM remains
  user-supplied. Local Ollama endpoint refused connection; no inference run.
- Folder footprint approximately 13 MB at measurement, below approved 250 MB.
- Brain reviewed the complete core/test/helper source and actual evidence.

Execution limits:
- Standard PyPI downloads were blocked by the shell network sandbox.
- Tests used genuine upstream pytest and dependencies as explicitly staged
  source imports. No pip installation or project wheel build was verified.
- Only Python 3.15.2 was tested, not every version in the declared Python range.
- No model, embedding, latency, evaluator, UI or HTML-report claims are made.
- No human dataset reviews occurred.

Authorization and delivery:
- User approved a single-folder local source/test setup with a 250 MB ceiling,
  no global installation and no intentional writes outside that folder.
- Home-directory creation was denied. The permitted copy is in
  %TEMP%/Knowledge-Delta-; all agent-created setup assets are inside it.
- Initial setup/copy failures and source-dependency import failures were
  corrected before the successful recorded run.
- No GitHub Actions or paid service was enabled.
- User explicitly approved the verification update for publication.
  Future pushes continue to require separate approval.

Next:
1. Publish the user-approved verification update.
2. Verify the published source hashes match the executed source manifest.
3. Report the final Milestone 1 evidence and exact run command.
4. Wait for user instruction before Milestone 2.

## Deferred milestones

M2: inference/embeddings and measured hardware smoke test.
M3: evaluation/manual review, UI, JSON/HTML reports, 20 development cases.
M4: genuine licensed sources, held-out dataset and controlled evaluation.
M5: portfolio packaging. None of these milestones is claimed complete.
