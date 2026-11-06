"""Redirect bodies must not bypass the bounded artifact payload reader."""
from urllib.error import HTTPError
from urllib.request import Request
import pytest
from scripts.setup_ollama_runtime import ReleaseRedirects
from scripts.setup_minilm_onnx import HuggingFaceRedirects


@pytest.mark.parametrize("handler,url", [(ReleaseRedirects, "https://release-assets.githubusercontent.com/file"),
                                        (HuggingFaceRedirects, "https://cdn-lfs.huggingface.co/file")])
@pytest.mark.parametrize("code", [301,302,303,307,308])
def test_redirect_closes_without_consuming_unaccounted_body(handler, url, code):
    class Body:
        closed = False
        def close(self): self.closed = True
        def read(self, *a): pytest.fail("Unaccounted redirect body read")
    body = Body()
    class Parent:
        def open(self, request, **kwargs):
            assert body.closed
            assert request.full_url == url
            return "test response"
    h = handler(); h.parent = Parent()
    req = Request(url); req.timeout = 1
    assert getattr(h, 'http_error_'+str(code))(req, body, code, 'redirect', {'location':url}) == 'test response'


@pytest.mark.parametrize("handler,url", [(ReleaseRedirects, "https://github.com/a"), (HuggingFaceRedirects,"https://huggingface.co/a")])
def test_redirect_loop_limit_retained(handler,url):
    from io import BytesIO
    h=handler();req=Request(url);req.timeout=1;req.redirect_dict={url:h.max_repeats}
    with pytest.raises(HTTPError): h.http_error_302(req,BytesIO(),302,'loop',{'location':url})
