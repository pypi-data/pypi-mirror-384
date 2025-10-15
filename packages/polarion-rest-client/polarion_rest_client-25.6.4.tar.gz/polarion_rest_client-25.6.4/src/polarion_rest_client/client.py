"""
High-level client wrapper for the generated Polarion REST client.

Usage:
    from polarion_rest_client import PolarionClient, get_env_vars
    pc = PolarionClient(**get_env_vars())  # or pass kwargs explicitly

    from polarion_rest_client.openapi.api.documents.get_document import sync as get_document
    doc = get_document(client=pc.gen, project_id="...", space_id="...", document_name="...")
"""

from __future__ import annotations
from typing import Optional, Mapping, Dict
import base64
import re
import ssl
import truststore

try:
    from polarion_rest_client.openapi.client import AuthenticatedClient
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "The generated package 'polarion_rest_client.openapi' is not available. "
        "Run 'pdm run regenerate-client' and rebuild."
    ) from exc


DEFAULT_TIMEOUT = 30.0
_REST_BASE_PATTERN = re.compile(r"/polarion/rest(/v\d+)?/?$")


def _merge_headers(h: Optional[Mapping[str, str]]) -> Dict[str, str]:
    return dict(h or {})


def _normalize_base_url(base_url: str, rest_version: str = "v1") -> str:
    """
    If base_url already looks like .../polarion/rest or .../polarion/rest/vN, keep it.
    Otherwise append /polarion/rest/<rest_version>.
    """
    if "/polarion/rest" in base_url:
        return base_url.rstrip("/")
    return base_url.rstrip("/") + f"/polarion/rest/{rest_version}"


class PolarionClient:
    """
    HL wrapper that owns the generated AuthenticatedClient.

    Create with either:
      - token=... (preferred)
      - username=... and password=... (sets Basic Authorization header)

    Access the generated client via `.gen`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        token: Optional[str] = None,
        token_prefix: str = "Bearer",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        headers: Optional[Mapping[str, str]] = None,
        rest_version: str = "v1",
        normalize_rest_base: bool = True,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")

        if normalize_rest_base:
            base_url = _normalize_base_url(base_url, rest_version=rest_version)

        hdrs = _merge_headers(headers)
        flag_or_ssl_context = (
            truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            if verify_ssl is True
            else verify_ssl
        )

        if token:
            self._gen = AuthenticatedClient(
                base_url=base_url,
                token=token,
                prefix=token_prefix,
                timeout=timeout,
                verify_ssl=flag_or_ssl_context,
                headers=hdrs,
            )
        elif username and password:
            basic = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            hdrs = {"Authorization": f"Basic {basic}", **hdrs}
            self._gen = AuthenticatedClient(
                base_url=base_url,
                token=None,
                timeout=timeout,
                verify_ssl=flag_or_ssl_context,
                headers=hdrs,
            )
        else:
            raise ValueError("Provide either token or username+password")

    @property
    def gen(self) -> AuthenticatedClient:
        """The generated client object to pass into generated API calls."""
        return self._gen

    @property
    def base_url(self) -> str:
        """
        Be robust to template differences:
        - some templates expose .base_url
        - others keep it as ._base_url
        - a few expose a getter
        """
        if hasattr(self._gen, "base_url"):
            return self._gen.base_url  # type: ignore[attr-defined]
        if hasattr(self._gen, "_base_url"):
            return self._gen._base_url  # type: ignore[attr-defined]
        if hasattr(self._gen, "get_base_url"):
            return self._gen.get_base_url()  # type: ignore[attr-defined]
        raise AttributeError("Generated client has no base_url/_base_url/get_base_url")

    def httpx(self):
        """Return the underlying httpx.Client used by the generated client."""
        return self._gen.get_httpx_client()

    # Optional debugging helper (kept if you found it useful):
    def raw_request(self, op_get_kwargs, **params):
        """
        Send a raw request using a generated operation's _get_kwargs(**params).
        Example:
            from polarion_rest_client.openapi.api.documents.get_document import _get_kwargs
            resp = pc.raw_request(_get_kwargs, project_id="X", space_id="Y", document_name="Z")
        """
        req = op_get_kwargs(**params)
        return self.httpx().request(**req)
