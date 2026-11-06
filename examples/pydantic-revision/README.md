# Genuine documentation revision: generic type bounds

This separate, **draft development example** follows an actual upstream parent
and child revision. It is not the constructed added-v1 corpus experiment.
There are zero human case or answer reviews in this example.

- Before: `55dd8daeb6091b9317b92836765f3f1396b3e9ba`.
- After: [commit 6f7691b](https://github.com/pydantic/pydantic/commit/6f7691b5c1e1838aedf88414a41cd6a9a0caf1d6), January 23, 2025.
- Upstream path: `docs/concepts/models.md`; the only changed path in that commit.
- Selected corpus: the complete `Generic models` section in each revision.
- Actual change: a warning says concrete type arguments are not checked against
  a type variable's upper bound during model parametrization.

This is a **documentation clarification**, not evidence that software behavior
changed. Both pinned `pydantic/version.py` files are identical and declare
2.10.5, but this alone does not establish applicability to released 2.10.5.
The manifests therefore leave software_versions empty and defaults null.
The question targets the supplied evidence, with no requested release version.
These unknowns remain visible. This diagnostic does not measure version-filter
improvement: filtering has no effective target version here. It does not test
runtime behavior or establish a released documentation snapshot.

The before expectation proposes evidence-only abstention because the selected
corpus does not explicitly state the added clarification. It remains an AI
draft: a human must review the complete selected section, including discussions
of instance validation, unparametrized generics, upper bounds and serialization.
Those topics must not be conflated with checking a concrete type argument at
parametrization. Absent evidence does not make the underlying fact false.

The after expectation proposes answering the explicit warning. The draft
`should_change` relation concerns evidence-backed answering, not changed
software behavior. No semantic pass follows from schema/source verification.
This is one selected document, not the entire Pydantic documentation corpus.

## Provenance and reproduction

Full original files, immutable revisions, sizes, SHA256 and Git blob identities
are in `sources/` and `sources.json`. The sources' MIT license was checked at
both revisions; the identical notice is included as `sources/LICENSE.txt`.
Attribution: Pydantic Services Inc. and individual contributors. No endorsement
is implied. Preserve this notice when redistributing the excerpts.

Run offline, without downloads or model calls:

```powershell
& .\.venv\Scripts\python.exe -B scripts/verify_pydantic_revision.py
```

The command verifies source pins, exact section extraction, the genuine warning
addition, stable document identity/version scope, dataset/quote validation and
draft relation bindings. Only before/manifest.json and after/manifest.json are
retrieval inputs. Cases, rubrics, this README and source inventories are excluded.
