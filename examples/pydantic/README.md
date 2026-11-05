# Pydantic development review batch

Status: ten development cases: seven explicitly human-reviewed, three AI drafts;
no model runs. See REVIEW_LOG.md for the exact limited review scope.
This is a constructed corpus experiment using genuine, MIT-licensed upstream
documentation, not an observed production regression or a historical upstream
document-update event. No benchmark correctness is established.

Snapshot A contains selected Pydantic 2.10.6 migration-guide excerpts. Snapshot B
contains the identical excerpts plus the Pydantic 1.10.21 models guide. All ten
questions explicitly request 2.10.6 in both snapshots. The expected substantive
answers should remain correct after adding another version's documentation.
Both defaults are explicitly 2.10.6, a historical target, not today's latest release.

The guide compares versions within the same file. A v2 version label describes
the guide's primary applicability; it does not mean every sentence describes v2.
Version filtering cannot remove historical clauses inside an otherwise applicable
document. Relative links in excerpts are retained as upstream text, not fetched.

## Sources and reproduction

See sources.json for immutable commits, upstream paths, Git blob identities and
SHA256 hashes. Original files and their respective MIT notices are in sources/.
Keep both notices when redistributing this bundle. Attribution: Pydantic authors;
v1 copyright Samuel Colvin, v2 Pydantic Services Inc. and contributors, as recorded
verbatim in the included licenses. No third-party endorsement is implied.

Run inside the repository using its isolated Python:

```powershell
& .\.venv\Scripts\python.exe -B scripts/prepare_pydantic.py
```

The command checks sources, exact excerpts, manifests, case definitions and
supporting quotes offline. --write explicitly creates missing generated artifacts;
it refuses to overwrite changed files or case definitions. It preserves actual
human case-review fields. It never downloads packages, runs models or assigns
human-review status. recipe.json is the reproducible extraction/case proposal.

## Human review still required

For each case, read the exact excerpt, requested version, answer and rubric in
cases.json. Check both expectations, source applicability, deprecation distinctions
and whether the rubric admits correct equivalent answers. Correct mistakes before
approval; record the real reviewer and review scope in that case's review fields.
A blanket statement of trust does not count as a case review. Dataset review is
separate from reviewing an assistant's actual answer after a run.

Only before/manifest.json and after/manifest.json define retrieval inputs. Never
index recipe.json, cases.json, review records or this README as source documents.
All families remain development-only. No held-out cases or independent labels
have been invented. This batch tests one category; genuine revision changes,
evidence-removal/conflict experiments and the final reviewed held-out dataset
remain separate work.
