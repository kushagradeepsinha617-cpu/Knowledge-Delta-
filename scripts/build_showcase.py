"""Build the static GitHub Pages export without dependencies or network access."""
import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
from urllib.parse import unquote, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/kushagradeepsinha617-cpu/Knowledge-Delta-'
FILES = {
    **{f'docs/screenshots/{name}.png': f'assets/{name}.png' for name in
       ('fixture-workspace', 'fixture-comparisons', 'fixture-evidence')},
    **{f'docs/evidence/milestone5-analysis/final-study-report.{suffix}':
       f'reports/final-study-report.{suffix}' for suffix in ('html', 'json')},
    **{f'docs/evidence/milestone5-study/{name}.json': f'reports/{name}.json'
       for name in ('final-artifact-manifest', 'offline-reproduction-receipt')},
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in ('href', 'src'))


def build(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / '.tools').resolve()) or output.exists():
        raise ValueError('Choose a new export directory inside this repository\'s .tools folder')
    html = (ROOT / 'docs/portfolio/index.html').read_text(encoding='utf-8')
    replacements = {'../../README.md': REPO + '#readme'}
    for name in ('ARCHITECTURE', 'DATASET_CARD', 'EXPERIMENT_RESULTS', 'CASE_STUDY', 'DEMO_SCRIPT'):
        replacements[f'../{name}.md'] = REPO + f'/blob/main/docs/{name}.md'
    for source, destination in FILES.items():
        replacements['../' + source.removeprefix('docs/')] = destination
    for source, destination in replacements.items():
        html = html.replace('"' + source + '"', '"' + destination + '"')
    output.mkdir(parents=True)
    (output / 'index.html').write_text(html, encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    for source, destination in FILES.items():
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    parser = Links()
    parser.feed(html)
    local_links = 0
    for url in parser.urls:
        parts = urlsplit(url)
        if parts.scheme or url.startswith('#'):
            if parts.scheme and parts.scheme != 'https':
                raise ValueError('Unexpected non-HTTPS external URL: ' + url)
            continue
        target = (output / unquote(parts.path)).resolve()
        if not target.is_relative_to(output) or not target.is_file():
            raise ValueError('Broken or escaping public link: ' + url)
        local_links += 1
    files = {path.relative_to(output).as_posix(): sha256(path.read_bytes()).hexdigest()
             for path in sorted(output.rglob('*')) if path.is_file()}
    manifest = {'kind': 'static_showcase_export', 'files': files,
                'verified_local_links': local_links, 'model_service_deployed': False,
                'source_repository': REPO}
    (output / 'deployment-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'status': 'static_export_verified', 'output': str(output),
            'files': len(files) + 1, 'local_links': local_links}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.tools/pages') / uuid4().hex[:8])
    args = parser.parse_args()
    print(json.dumps(build(ROOT / args.output), indent=2))


if __name__ == '__main__':
    main()
