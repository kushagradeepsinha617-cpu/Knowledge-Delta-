# Constructed MVP development fixtures

All documents, product behavior, commands and cases here are invented for KnowledgeDelta. Widget is fictional; installation commands are sample text, not setup instructions. These are AI-authored draft cases, not human-reviewed labels, live inference results or benchmark evidence. No answers from an assistant are supplied here.

The dataset contains 20 distinct development questions covering all seven change categories. Every case uses a separate fact or decision; there are no paraphrase cases. Both snapshots belong to one constructed software domain. Explicit version-1 questions retain version 1. Two current/default-version questions deliberately resolve through the manifests: version 1 before and version 2 after. The older version documents remain valid in the later snapshot.

Several independent constructed mutations occur in this snapshot pair. A case category identifies the intended test condition for its supporting fact; the pair does not isolate one causal mutation. These fixtures cannot establish which individual change caused an observed assistant failure.

The three removed-evidence cases expect abstention only under the evidence-only answering policy. Their old facts are not thereby proven false. The two conflicts use sources with the same applicable version and no declared precedence. Missing-evidence cases concern facts absent from both snapshots.

`cases.json` and `relations.json` contain answer keys, rubrics and draft expected relations. Keep them outside the retrieval corpus and answering prompt. Only files explicitly listed in a snapshot manifest belong in its document corpus. `relations.json` binds its draft annotations to canonical dataset and case hashes; none of those annotations is human-reviewed.

All cases are development cases. No held-out score, independent review, production correctness or real-source provenance is claimed. Review content and family assignments before reusing or extending the dataset.
