import httpx
import pytest

from polarion_rest_client.error import (
    raise_jsonapi_error,
    raise_from_response,
    JSONAPIError,
    HTTPStatusError,
    Forbidden,
    NotFound,
)


def _resp(status: int, body: bytes) -> httpx.Response:
    req = httpx.Request("GET", "http://example.invalid")
    return httpx.Response(status, content=body, request=req)


def test_jsonapi_errors_are_parsed_and_raised():
    body = b'{"errors":[{"status":"403","title":"Forbidden","detail":"No perms"}]}'
    with pytest.raises(Forbidden) as ei:
        raise_jsonapi_error(_resp(403, body))
    e = ei.value
    assert isinstance(e, JSONAPIError)
    assert e.status == 403
    assert "Forbidden" in str(e)
    assert "No perms" in str(e)


def test_plain_http_error_becomes_httpstatuserror():
    with pytest.raises(HTTPStatusError) as ei:
        raise_jsonapi_error(_resp(404, b"Not Found"))
    e = ei.value
    assert e.status_code == 404
    assert "404" in str(e)


@pytest.mark.parametrize(
    "status,title",
    [
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (409, "Conflict"),
        (500, "Server Error"),
        (503, "Server Error"),
    ],
)
def test_subclass_mapping(status, title):
    body = ('{"errors":[{"status":"%d","title":"%s","detail":"x"}]}' % (status, title)).encode()
    with pytest.raises(JSONAPIError) as ei:
        raise_jsonapi_error(_resp(status, body))
    assert ei.value.title == title


def test_ok_2xx_without_errors_does_not_raise():
    resp = _resp(200, b'{"data":{"ok":true}}')
    raise_jsonapi_error(resp)  # no exception


def test_ok_2xx_with_errors_does_raise():
    resp = _resp(200, b'{"errors":[{"status":"400","title":"Bad Request","detail":"nope"}]}')
    with pytest.raises(JSONAPIError):
        raise_jsonapi_error(resp)


class _FakeResponse:
    """Minimal stand-in for an OpenAPI-generated Response object."""
    def __init__(self, status_code: int, doc=None, content: bytes = b""):
        self.status_code = status_code
        self.parsed = doc
        self.content = content


def test_raise_from_response_generated_openapi_not_found():
    fake = _FakeResponse(
        404,
        {"errors": [{"status": "404", "title": "Not Found", "detail": "missing"}]},
    )
    with pytest.raises(NotFound):
        raise_from_response(fake)


def test_raise_from_response_httpstatus_fallback_on_plain_error():
    fake = _FakeResponse(502)  # no JSON:API body -> HTTPStatusError fallback
    with pytest.raises(HTTPStatusError) as ei:
        raise_from_response(fake)
    assert ei.value.status_code == 502


def test_raise_from_response_2xx_with_errors_raises_jsonapierror():
    fake = _FakeResponse(
        200,
        {"errors": [{"status": "400", "title": "Bad Request", "detail": "nope"}]},
    )
    with pytest.raises(JSONAPIError) as ei:
        raise_from_response(fake)
    assert "Bad Request" in str(ei.value)


def test_raise_from_response_with_httpx_response_delegates_properly():
    req = httpx.Request("GET", "http://example.invalid")
    body = b'{"errors":[{"status":"403","title":"Forbidden","detail":"denied"}]}'
    resp = httpx.Response(403, content=body, request=req)
    with pytest.raises(Forbidden):
        raise_from_response(resp)
