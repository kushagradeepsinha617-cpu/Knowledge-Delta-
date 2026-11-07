"""Video lifecycle regression checks without installing a browser."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.record_demo import finalize_capture


@pytest.mark.parametrize('failure', [None, 'context', 'save'])
def test_video_is_saved_before_browser_disconnect_and_browser_always_closes(failure):
    events = []
    def close_context():
        events.append('context')
        if failure == 'context':
            raise RuntimeError('context')
    def save(path):
        assert path == str(Path('demo.webm'))
        assert events == ['context']
        events.append('save')
        if failure == 'save':
            raise RuntimeError('save')
    context = SimpleNamespace(close=close_context)
    video = SimpleNamespace(save_as=save)
    browser = SimpleNamespace(close=lambda: events.append('browser'))
    if failure:
        with pytest.raises(RuntimeError, match=failure):
            finalize_capture(context, browser, video, Path('demo.webm'))
    else:
        finalize_capture(context, browser, video, Path('demo.webm'))
    assert events == (['context', 'browser'] if failure == 'context' else ['context', 'save', 'browser'])
