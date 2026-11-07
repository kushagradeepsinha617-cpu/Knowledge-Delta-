"""Explicit optional Playwright setup, or an isolated local fixture recording.

Setup downloads browser tooling only when --setup is supplied. Recording never
downloads anything, calls a model, or submits human-review forms.
"""
import argparse
from datetime import datetime, timezone
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TOOL = ROOT / '.tools/demo-recording'
PACKAGES = TOOL / 'packages'
VERSION = '1.64.1'
CASES = ['request-timeout-change', 'installation-rewording', 'v1-token-despite-v2',
         'export-evidence-removed', 'worker-source-conflict']


def finalize_capture(context, browser, video, saved):
    """Keep the browser connection alive until the finalized video is saved."""
    try:
        context.close()
        if video is not None:
            video.save_as(str(saved))
    finally:
        browser.close()


def environment():
    temp = TOOL / 'tmp'
    temp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
               PLAYWRIGHT_BROWSERS_PATH=str(TOOL / 'browsers'),
               PLAYWRIGHT_SKIP_BROWSER_GC='1', PYTHONDONTWRITEBYTECODE='1',
               PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_CACHE_DIR='1',
               PYTHONPATH=str(PACKAGES))
    return env


def setup():
    """Install only optional recording tools into the project-local target."""
    from scripts.setup_ui import PIP_NAME, PIP_SHA256
    pip = ROOT / '.tools/ui-setup' / PIP_NAME
    if sha256(pip.read_bytes()).hexdigest() != PIP_SHA256:
        raise RuntimeError('Verified project-local pip wheel is missing or changed')
    env = environment()
    bootstrap = ('import runpy,sys;sys.path.insert(0,' + repr(str(pip)) + ');'
                 "sys.argv=['pip','install','--only-binary=:all:','--no-cache-dir',"
                 "'--retries','0','--target'," + repr(str(PACKAGES)) + ","
                 + repr('playwright==' + VERSION) + "];runpy.run_module('pip',run_name='__main__')")
    subprocess.run([sys.executable, '-B', '-c', bootstrap], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, '-B', '-m', 'playwright', 'install',
                    'chromium', '--only-shell'], cwd=ROOT, env=env, check=True)
    print('Recording tools installed locally. Now run this script without --setup.', flush=True)


def prepare_workspace(output):
    workspace = output / 'workspace'
    shutil.copytree(ROOT / 'examples/mvp', workspace / 'examples/mvp')
    return workspace


def verify_state(state):
    evaluation = state['evaluation']
    counts = evaluation['counts']
    if (evaluation['origin'] != 'fixture' or counts['planned_answer_records'] != 80
            or counts['recorded_answer_records'] != 80 or counts['human_answer_reviews'] != 0):
        raise RuntimeError('Unexpected fixture accounting or existing human labels')
    for case_id in CASES:
        row = next(row for row in evaluation['rows'] if row['case_id'] == case_id
                   and row['configuration_name'] == 'basic' and row['repetition'] == 1)
        if row['comparison']['status'] != 'needs_human_review':
            raise RuntimeError('Fixture no longer pending review: ' + case_id)
    return {'origin': 'fixture', 'planned': 80, 'recorded': 80,
            'human_answer_reviews': 0, 'selected_cases_pending_review': CASES}


def record(output, check_only=False):
    from knowledge_delta.web_app import create_server
    workspace = prepare_workspace(output)
    server = create_server(workspace, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    static = ThreadingHTTPServer(('127.0.0.1', 0),
              partial(SimpleHTTPRequestHandler, directory=str(ROOT / 'docs')))
    static_thread = threading.Thread(target=static.serve_forever, daemon=True)
    static_thread.start()
    url = 'http://127.0.0.1:' + str(server.server_address[1])
    docs = 'http://127.0.0.1:' + str(static.server_address[1])
    receipt = {'kind': 'playwright_demo_capture', 'status': 'started',
               'created_at': datetime.now(timezone.utc).isoformat(), 'model_calls': 0,
               'human_reviews_submitted': 0, 'visual_review': 'pending', 'screenshots': []}
    try:
        # This independent check also works offline without Playwright installed.
        with urlopen(url + '/api/state', timeout=20) as response:
            initial = json.load(response)
        request = Request(url + '/api/load', data=b'{}', headers={
            'Content-Type': 'application/json', 'X-KnowledgeDelta-Token': initial['csrf']})
        with urlopen(request, timeout=30) as response:
            receipt['fixture_checks'] = verify_state(json.load(response)['state'])
        if check_only:
            receipt['status'] = 'fixture_preflight_passed_no_browser_or_video'
            return receipt
        sys.path.insert(0, str(PACKAGES))
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError('Playwright cannot be imported in this process. If setup succeeded, '
                               'run recording from your normal PowerShell. Import error: ' + str(exc)) from exc
        receipt['playwright_version'] = importlib.metadata.version('playwright')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, chromium_sandbox=True)
            receipt['browser_version'] = browser.version
            context = browser.new_context(viewport={'width': 1440, 'height': 900},
                      record_video_dir=str(output / 'video'),
                      record_video_size={'width': 1440, 'height': 900},
                      reduced_motion='reduce', service_workers='block')
            video = None
            saved = output / 'knowledge-delta-demo.webm'
            try:
                # The dedicated context can visit only the two owned local servers.
                origins = {url, docs}
                context.route('**/*', lambda route: route.continue_() if
                    (urlsplit(route.request.url).scheme + '://' + urlsplit(route.request.url).netloc)
                    in origins else route.abort())
                page = context.new_page()
                video = page.video
                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(4000)
                page.get_by_role('button', name='Load comparison records', exact=True).click()
                page.locator('#workspace').wait_for(state='visible')
                state = page.evaluate("async () => (await fetch('/api/state')).json()")
                receipt['fixture_checks'] = verify_state(state)
                page.locator('#inputs-panel').evaluate('(node) => node.open = false')
                page.locator('#config-filter').select_option('basic')
                for index, case_id in enumerate(CASES, 1):
                    page.locator('#case-filter').fill(case_id)
                    options = page.locator('#case-select option').evaluate_all(
                        '(nodes) => nodes.map(n => n.value)')
                    selected = next(value for value in options if json.loads(value) == [case_id, 'basic', 1])
                    page.locator('#case-select').select_option(selected)
                    page.locator('#case-title').scroll_into_view_if_needed()
                    page.wait_for_timeout(5000)
                    first = output / f'{index:02d}-{case_id}-answers.png'
                    page.screenshot(path=str(first))
                    page.locator('#case-details details').evaluate_all(
                        "nodes => nodes.forEach(n => { if (n.querySelector('summary')?.textContent === 'Expected behavior and rubric') n.open = true; })")
                    page.locator('#case-details .snapshot-pair').scroll_into_view_if_needed()
                    page.mouse.wheel(0, 300)
                    page.wait_for_timeout(6000)
                    second = output / f'{index:02d}-{case_id}-evidence.png'
                    page.screenshot(path=str(second))
                    receipt['screenshots'].extend([first.name, second.name])
                page.goto(docs + '/portfolio/index.html', wait_until='networkidle')
                page.wait_for_timeout(6000)
                page.locator('#workflow').scroll_into_view_if_needed()
                page.mouse.wheel(0, 420)
                page.wait_for_timeout(6000)
            finally:
                # Finalize the context, then save while the browser connection
                # still exists. Closing the browser first invalidates save_as.
                finalize_capture(context, browser, video, saved)
            receipt.update(status='captured_pending_visual_review', video=saved.name,
                           video_bytes=saved.stat().st_size,
                           video_sha256=sha256(saved.read_bytes()).hexdigest())
    finally:
        server.shutdown(); server.server_close(); thread.join(5)
        static.shutdown(); static.server_close(); static_thread.join(5)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', action='store_true')
    parser.add_argument('--check', action='store_true', help='Offline fixture check, no browser or video')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14) or not Path(sys.prefix).resolve().is_relative_to(ROOT):
        parser.error('Use this repo\'s .venv-ml Python 3.14')
    if args.setup:
        setup()
        return 0
    os.environ.update(environment())
    output = ROOT / 'docs/portfolio/captures' / uuid4().hex[:12]
    output.mkdir(parents=True)
    try:
        receipt = record(output, args.check)
    except Exception as exc:
        receipt = {'status': 'capture_failed', 'error': str(exc), 'video_verified': False}
    (output / 'capture.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), **receipt}, indent=2))
    return 2 if receipt['status'] == 'capture_failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
