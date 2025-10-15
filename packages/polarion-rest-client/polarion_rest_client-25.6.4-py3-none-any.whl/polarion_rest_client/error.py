from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import httpx


# =========================
# Exception hierarchy
# =========================

class PolarionError(RuntimeError):
    """Base error for the high-level client."""


class HTTPStatusError(PolarionError):
    """
    Raised for non-2xx HTTP responses that don't include a JSON:API "errors" array.
    """
    def __init__(self, status_code: int, message: str, *, url: Optional[str] = None, payload: Any = None):
        super().__init__(f"{status_code} {message}" + (f" [{url}]" if url else ""))
        self.status_code = status_code
        self.message = message
        self.url = url
        self.payload = payload


class JSONAPIError(PolarionError):
    """
    Raised when the response contains a JSON:API "errors" array. Subclasses map common statuses.
    """
    def __init__(self, status: Union[int, str], title: str, detail: Optional[str] = None, *, payload: Any = None):
        msg = f"{status} {title}" + (f": {detail}" if detail else "")
        super().__init__(msg)
        self.status = int(status) if str(status).isdigit() else status
        self.title = title
        self.detail = detail
        self.payload = payload


class Unauthorized(JSONAPIError):
    """401 Unauthorized"""
    def __init__(self, status: Union[int, str] = 401, title: str = "Unauthorized",
                 detail: Optional[str] = None, *, payload: Any = None):
        super().__init__(status or 401, title, detail, payload=payload)


class Forbidden(JSONAPIError):
    """403 Forbidden"""
    def __init__(self, status: Union[int, str] = 403, title: str = "Forbidden",
                 detail: Optional[str] = None, *, payload: Any = None):
        super().__init__(status or 403, title, detail, payload=payload)


class NotFound(JSONAPIError):
    """404 Not Found"""
    def __init__(self, status: Union[int, str] = 404, title: str = "Not Found",
                 detail: Optional[str] = None, *, payload: Any = None):
        super().__init__(status or 404, title, detail, payload=payload)


class Conflict(JSONAPIError):
    """409 Conflict"""
    def __init__(self, status: Union[int, str] = 409, title: str = "Conflict",
                 detail: Optional[str] = None, *, payload: Any = None):
        super().__init__(status or 409, title, detail, payload=payload)


class ServerError(JSONAPIError):
    """5xx Server Error"""
    def __init__(self, status: Union[int, str] = 500, title: str = "Server Error",
                 detail: Optional[str] = None, *, payload: Any = None):
        normalized = int(status) if str(status).isdigit() else 500
        if isinstance(normalized, int) and normalized < 500:
            normalized = 500
        super().__init__(normalized, title, detail, payload=payload)


# =========================
# Helpers
# =========================

def _extract_jsonapi_errors(doc: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    errs = doc.get("errors")
    return errs if isinstance(errs, list) and errs else None


def _map_status_exc(status: int, title: str, detail: Optional[str], *, payload: Any = None) -> JSONAPIError:
    if status == 401:
        return Unauthorized(status, title, detail, payload=payload)
    if status == 403:
        return Forbidden(status, title, detail, payload=payload)
    if status == 404:
        return NotFound(status, title, detail, payload=payload)
    if status == 409:
        return Conflict(status, title, detail, payload=payload)
    if status >= 500:
        return ServerError(status, title, detail, payload=payload)
    return JSONAPIError(status, title, detail, payload=payload)


def raise_jsonapi_error(resp: httpx.Response) -> None:
    """
    Unified status/error checker:

    1) If status is not 2xx:
         - Try to parse JSON:API errors and raise a typed JSONAPIError subclass.
         - Otherwise, raise HTTPStatusError.
    2) If status is 2xx but payload contains an "errors" array (some servers do this),
         raise a typed JSONAPIError subclass.
    3) Otherwise return (OK).
    """
    status = resp.status_code
    url = str(resp.request.url) if resp.request else None

    # Non-2xx → prefer JSON:API error content if present
    if status < 200 or status >= 300:
        try:
            doc = resp.json()
        except Exception:
            doc = None
        if isinstance(doc, dict):
            errs = _extract_jsonapi_errors(doc)
            if errs:
                e0 = errs[0]
                estatus = int(e0.get("status") or status)
                etitle = str(e0.get("title") or httpx.codes.get_reason_phrase(status) or "Error")
                edetail = e0.get("detail")
                raise _map_status_exc(estatus, etitle, edetail, payload=doc)
        # No JSON:API payload
        reason = httpx.codes.get_reason_phrase(status) or "HTTP Error"
        raise HTTPStatusError(status, reason, url=url, payload=resp.text)

    # 2xx but errors array present → still raise
    try:
        doc = resp.json()
    except Exception:
        return
    if isinstance(doc, dict):
        errs = _extract_jsonapi_errors(doc)
        if errs:
            e0 = errs[0]
            estatus = int(e0.get("status") or status)
            etitle = str(e0.get("title") or "Error")
            edetail = e0.get("detail")
            raise _map_status_exc(estatus, etitle, edetail, payload=doc)


def raise_from_response(resp: Any) -> None:
    """
    Raise a typed error from either:
      - an httpx.Response  -> delegated to raise_jsonapi_error
      - a generated OpenAPI Response (with .status_code, .parsed, .content)

    Behavior:
      * Non-2xx: prefer JSON:API `errors[]` payload and map to a typed exception;
        otherwise raise HTTPStatusError with best-effort payload.
      * 2xx with `errors[]`: still raise a typed JSONAPIError subclass.
      * Otherwise: no-op.
    """
    import json  # local import to keep this function self-contained
    import httpx

    # httpx.Response → reuse the canonical checker
    if isinstance(resp, httpx.Response):
        return raise_jsonapi_error(resp)

    status = int(getattr(resp, "status_code", 0) or 0)

    # Try to normalize a JSON document from generated Response
    doc = None
    parsed = getattr(resp, "parsed", None)
    if parsed is not None:
        try:
            # Most generated models expose .to_dict()
            doc = parsed.to_dict()  # type: ignore[attr-defined]
        except Exception:
            if isinstance(parsed, dict):
                doc = parsed

    if doc is None:
        try:
            raw = getattr(resp, "content", b"") or b""
            if isinstance(raw, (bytes, bytearray)) and raw:
                doc = json.loads(raw.decode("utf-8", "ignore"))
        except Exception:
            doc = None

    # Non-2xx → map JSON:API error if present, else HTTPStatusError
    if status < 200 or status >= 300:
        if isinstance(doc, dict):
            errs = _extract_jsonapi_errors(doc)
            if errs:
                e0 = errs[0]
                estatus = int(e0.get("status") or status)
                etitle = str(e0.get("title") or httpx.codes.get_reason_phrase(status) or "Error")
                edetail = e0.get("detail")
                raise _map_status_exc(estatus, etitle, edetail, payload=doc)
        raise HTTPStatusError(status, httpx.codes.get_reason_phrase(status) or "HTTP Error", payload=doc)

    # 2xx but errors[] present (some servers do this) → still raise
    if isinstance(doc, dict):
        errs = _extract_jsonapi_errors(doc)
        if errs:
            e0 = errs[0]
            estatus = int(e0.get("status") or status)
            etitle = str(e0.get("title") or "Error")
            edetail = e0.get("detail")
            raise _map_status_exc(estatus, etitle, edetail, payload=doc)
    # else OK / no-op
