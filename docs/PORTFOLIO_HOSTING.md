# Public portfolio hosting

The static showcase is prepared for GitHub Pages from the `gh-pages` branch,
using its `/ (root)` folder. The repository is public. No custom domain or
paid service is required. This publishes the project presentation and reports;
the Python application and model remain local.

Build the export from the repository root:

```powershell
& '.\.venv\Scripts\python.exe' -B scripts/build_showcase.py
```

The command creates a new folder under `.tools/pages/`, copies the selected
screenshots and reports, rewrites source-document links to GitHub, and verifies
all local asset links. The export has no backend, model weights, environments,
review journal or browser profile. Its `deployment-manifest.json` records hashes.

For first-time activation, open the repository's Settings → Pages. Choose
**Deploy from a branch**, branch **gh-pages**, folder **/ (root)**, then Save.
The expected public address is
`https://kushagradeepsinha617-cpu.github.io/Knowledge-Delta-/`.
Treat that address as pending until GitHub reports deployment success and the
public page can be fetched.

Future showcase updates need a new export and an update of `gh-pages`.
The normal application source stays on `main`. The GitHub connector can publish
the branch; enabling Pages requires repository settings access through the UI.
