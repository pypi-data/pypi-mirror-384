from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Union

from .client import PolarionClient
from .error import raise_from_response
from .paging import list_items, extract_items, paged, resolve_page_params

# Generated client bits
from polarion_rest_client.openapi.types import UNSET, Unset

# Low-level endpoints (available today)
from polarion_rest_client.openapi.api.document_parts.get_document_parts import (
    sync_detailed as _get_document_parts,
)
from polarion_rest_client.openapi.api.document_parts.get_document_part import (
    sync_detailed as _get_document_part,
)

# TODO : implement when Polarion 25.12 is available
# The OpenAPI in your environment currently exposes GET only for Document Parts.
# If POST/PATCH/DELETE for parts appear in a newer server (e.g., 25.12),
# add the corresponding imports and high-level wrappers here, mirroring WorkItem.


def _to_dict(resp) -> Dict[str, Any]:
    """Normalize a generated Response to a plain dict payload."""
    if resp is None or getattr(resp, "parsed", None) is None:
        return {}
    try:
        return resp.parsed.to_dict()
    except Exception:
        return resp.parsed  # already a dict


class _DeepFields:
    """
    Small helper that encodes deep-object fields exactly as:
      {'fields[<resource>]': '<value or comma-joined list>'}

    The generated client calls `.to_dict()` on whatever object is passed as `fields`,
    so this works as a drop-in replacement for `SparseFields` while producing
    the correct deep-object query key that some servers require.
    """

    def __init__(self, resource: str, value: Union[str, List[str]]):
        self.resource = resource
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        v = self.value
        if isinstance(v, list):
            # Most servers accept comma-joined string for sparse field lists
            v = ",".join(v)
        return {f"fields[{self.resource}]": v}


def _build_fields_param_for_parts(
    fields_parts: Optional[Union[str, List[str]]],
) -> Union[Unset, _DeepFields]:
    """
    Turn `fields_parts` into a deep-object fields parameter for 'document_parts'.

    - None/empty → UNSET (omit the query param entirely)
    - str or list → fields[document_parts]=<value> (list joined by comma)
    """
    if not fields_parts:
        return UNSET
    return _DeepFields(
        "document_parts",
        fields_parts if isinstance(fields_parts, str) else list(fields_parts),
    )


class DocumentPart:
    """
    High-level wrapper for Document Parts (read/list only as per current OpenAPI).

    Endpoints used (GET only):
      - /projects/{projectId}/spaces/{spaceId}/documents/{documentName}/parts         (list)
      - /projects/{projectId}/spaces/{spaceId}/documents/{documentName}/parts/{id}   (get)
    """

    def __init__(self, pc: PolarionClient):
        self._c = pc.gen
        # Resolve the exact paging param names on your generated function.
        # This avoids any assumptions (could be "page_number"/"page_size" or "pagenumber"/"pagesize" etc.)
        self._page_param, self._size_param = resolve_page_params(_get_document_parts)

    # ---------------------------- LIST (items) ----------------------------
    def list(
        self,
        project_id: str,
        space_id: str,
        document_name: str,
        *,
        page_number: int = 1,
        page_size: int = 100,
        # Accept either "@all" as a string or a list of attribute names
        fields_parts: Optional[Union[str, List[str]]] = None,
        include: Optional[str] = None,
        revision: Optional[str] = None,
        # When page_size == -1 we fetch-all client-side with this per-request chunk
        chunk_size: int = 200,
        # Optional local filtering helpers (no server-side querying exists for parts)
        title_contains: Optional[str] = None,
        max_pages: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Return document parts as a list of JSON:API resource objects.

        Notes:
          * If page_size == -1: fetch ALL pages client-side; we never send “-1” to the server.
          * fields_parts: if provided, encoded as deep-object fields[document_parts]=...
            (e.g., "@all" or ["id","title","content"]).
          * There is no query parameter for parts in the current API, so we optionally
            filter locally by `title_contains` after retrieval.
        """
        fields = _build_fields_param_for_parts(fields_parts)

        items = list_items(
            _get_document_parts,
            page_param=self._page_param,
            size_param=self._size_param,
            page_number=page_number,
            page_size=page_size,   # -1 => handled client-side
            chunk_size=chunk_size,
            max_pages=max_pages,
            on_error=raise_from_response,
            client=self._c,
            project_id=project_id,
            space_id=space_id,
            document_name=document_name,
            fields=fields,
            include=include if include is not None else UNSET,
            revision=revision if revision is not None else UNSET,
        )

        if title_contains:
            t = title_contains.lower()
            items = [
                it for it in items
                if str((it.get("attributes") or {}).get("title", "")).lower().find(t) >= 0
            ]
        return items

    # ------------------------------ GET ------------------------------
    def get(
        self,
        project_id: str,
        space_id: str,
        document_name: str,
        part_id: str,
        *,
        fields_parts: Optional[Union[str, List[str]]] = None,
        include: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a single Document Part by ID.

        Pass `fields_parts="@all"` to ensure the server returns the full content
        (e.g., HTML in `attributes.content` / `contentHtml`), which is necessary
        for features like table extraction.
        """
        fields = _build_fields_param_for_parts(fields_parts)

        resp = _get_document_part(
            client=self._c,
            project_id=project_id,
            space_id=space_id,
            document_name=document_name,
            part_id=part_id,
            fields=fields,
            include=include if include is not None else UNSET,
            revision=revision if revision is not None else UNSET,
        )
        if resp.status_code == 200 and resp.parsed:
            return _to_dict(resp)
        raise_from_response(resp)

    # ------------------------------ ITER ------------------------------
    def iter(
        self,
        project_id: str,
        space_id: str,
        document_name: str,
        *,
        page_size: int = 100,
        start_page: int = 1,
        fields_parts: Optional[Union[str, List[str]]] = None,
        include: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate all parts for a given document.
        """
        fields = _build_fields_param_for_parts(fields_parts)

        resolved_page_param = self._page_param
        resolved_size_param = self._size_param

        def _one_page(**kw):
            call_kwargs: Dict[str, Any] = {
                "client": self._c,
                "project_id": project_id,
                "space_id": space_id,
                "document_name": document_name,
                resolved_size_param: kw.get("page_size"),
                "fields": fields,
                "include": include if include is not None else UNSET,
                "revision": revision if revision is not None else UNSET,
            }
            if resolved_page_param is not None:
                call_kwargs[resolved_page_param] = kw.get("page_index")
            return _get_document_parts(**call_kwargs)

        for page_obj in paged(
            _one_page,
            page_param=("page_index" if resolved_page_param is not None else None),
            size_param="page_size",
            start=start_page,
            page_size=page_size,
        ):
            for item in extract_items(page_obj):
                yield item
