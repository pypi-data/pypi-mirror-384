from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from .client import PolarionClient
from .error import raise_from_response

# Low-level API from the generated client (present in current OpenAPI)
from polarion_rest_client.openapi.api.documents.post_documents import (
    sync_detailed as _post_documents,
)
from polarion_rest_client.openapi.api.documents.get_document import (
    sync_detailed as _get_document,
)
from polarion_rest_client.openapi.api.documents.patch_document import (
    sync_detailed as _patch_document,
)

# Models / helpers from the generated client
from polarion_rest_client.openapi.models.sparse_fields import SparseFields
from polarion_rest_client.openapi.models.documents_list_post_request import (
    DocumentsListPostRequest,
)
from polarion_rest_client.openapi.models.documents_single_patch_request import (
    DocumentsSinglePatchRequest,
)
from polarion_rest_client.openapi.types import UNSET, Unset

# ---------------------------------------------------------------------------
# TODO: implement when Polarion 25.12 is available
# The list/iter/find_by_title helpers below depend on a list endpoint:
#   GET /projects/{projectId}/spaces/{spaceId}/documents
# When upgrading to 25.12, uncomment the imports and the methods further down.
# ---------------------------------------------------------------------------
# from .paging import (
#     paged,
#     extract_items,
#     resolve_page_params,
#     list_items,
# )
# from polarion_rest_client.openapi.api.documents.get_documents import (
#     sync_detailed as _get_documents,
# )
# ---------------------------------------------------------------------------


def _to_dict(resp) -> Dict[str, Any]:
    """Normalize a generated Response to a plain dict payload."""
    if resp is None or getattr(resp, "parsed", None) is None:
        return {}
    try:
        return resp.parsed.to_dict()
    except Exception:
        return resp.parsed


class Document:
    """
    High-level Document operations built strictly on the current generated client API.

    Available (current spec):
      • create (POST /projects/{projectId}/spaces/{spaceId}/documents)
      • get    (GET  /projects/{projectId}/spaces/{spaceId}/documents/{documentName})
      • update (PATCH /projects/{projectId}/spaces/{spaceId}/documents/{documentName})

    Not yet available in current spec (planned for 25.12):
      • list/iter/find_by_title (see commented stubs below)
    """

    def __init__(self, pc: PolarionClient):
        self._c = pc.gen  # AuthenticatedClient

        # -------------------------------------------------------------------
        # TODO: implement when Polarion 25.12 is available
        # Enable paging param resolution when list endpoint exists.
        # self._page_param, self._size_param = resolve_page_params(_get_documents)
        # -------------------------------------------------------------------

    # ---------------------------- CREATE ----------------------------
    def create(
        self,
        project_id: str,
        space_id: str,
        *,
        module_name: str,  # documentName to create
        title: Optional[str] = None,
        doc_type: Optional[str] = None,  # e.g. 'req_specification'
        status: Optional[str] = None,    # e.g. 'draft'
        home_page_content: Optional[str] = None,
        home_page_content_type: str = "text/plain",
        auto_suspect: Optional[bool] = None,
        uses_outline_numbering: Optional[bool] = None,
        outline_numbering_prefix: Optional[str] = None,
        rendering_layouts: Optional[List[Mapping[str, Any]]] = None,
        structure_link_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /projects/{projectId}/spaces/{spaceId}/documents
        Required: module_name (documentName). Other attributes are optional.
        """
        attrs: Dict[str, Any] = {"moduleName": module_name}
        if title is not None:
            attrs["title"] = title
        if doc_type is not None:
            attrs["type"] = doc_type
        if status is not None:
            attrs["status"] = status
        if home_page_content is not None:
            attrs["homePageContent"] = {"type": home_page_content_type, "value": home_page_content}
        if auto_suspect is not None:
            attrs["autoSuspect"] = bool(auto_suspect)
        if uses_outline_numbering is not None:
            attrs["usesOutlineNumbering"] = bool(uses_outline_numbering)
        if outline_numbering_prefix is not None:
            attrs["outlineNumbering"] = {"prefix": outline_numbering_prefix}
        if rendering_layouts:
            attrs["renderingLayouts"] = list(rendering_layouts)
        if structure_link_role is not None:
            attrs["structureLinkRole"] = structure_link_role

        body = DocumentsListPostRequest.from_dict({"data": [{"type": "documents", "attributes": attrs}]})
        resp = _post_documents(client=self._c, project_id=project_id, space_id=space_id, body=body)
        if resp.status_code in (200, 201) and resp.parsed:
            doc = _to_dict(resp)
            data = (doc.get("data") or [])
            return data[0] if isinstance(data, list) and data else doc
        raise_from_response(resp)

    # ------------------------------ GET ------------------------------
    def get(
        self,
        project_id: str,
        space_id: str,
        document_name: str,
        *,
        fields_documents: Optional[List[str]] = None,
        include: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /projects/{projectId}/spaces/{spaceId}/documents/{documentName}"""
        fields: Unset | SparseFields = UNSET
        if fields_documents:
            fields = SparseFields.from_dict({"documents": list(fields_documents)})

        resp = _get_document(
            client=self._c,
            project_id=project_id,
            space_id=space_id,
            document_name=document_name,
            fields=fields,
            include=include if include is not None else UNSET,
            revision=revision if revision is not None else UNSET,
        )
        if resp.status_code == 200 and resp.parsed:
            return _to_dict(resp)
        raise_from_response(resp)

    # ----------------------------- UPDATE -----------------------------
    def update(
        self,
        project_id: str,
        space_id: str,
        document_name: str,
        *,
        title: Optional[str] = None,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        home_page_content: Optional[str] = None,
        home_page_content_type: str = "text/plain",
        auto_suspect: Optional[bool] = None,
        uses_outline_numbering: Optional[bool] = None,
        outline_numbering_prefix: Optional[str] = None,
        rendering_layouts: Optional[List[Mapping[str, Any]]] = None,
        workflow_action: Optional[str] = None,  # maps to query param 'workflowAction'
    ) -> Dict[str, Any]:
        """
        PATCH /projects/{projectId}/spaces/{spaceId}/documents/{documentName}
        Sends only provided fields.
        """
        attrs: Dict[str, Any] = {}
        if title is not None:
            attrs["title"] = title
        if doc_type is not None:
            attrs["type"] = doc_type
        if status is not None:
            attrs["status"] = status
        if home_page_content is not None:
            attrs["homePageContent"] = {"type": home_page_content_type, "value": home_page_content}
        if auto_suspect is not None:
            attrs["autoSuspect"] = bool(auto_suspect)
        if uses_outline_numbering is not None:
            attrs["usesOutlineNumbering"] = bool(uses_outline_numbering)
        if outline_numbering_prefix is not None:
            attrs["outlineNumbering"] = {"prefix": outline_numbering_prefix}
        if rendering_layouts:
            attrs["renderingLayouts"] = list(rendering_layouts)

        data: Dict[str, Any] = {
            "type": "documents",
            "id": f"{project_id}/{space_id}/{document_name}",
        }
        if attrs:
            data["attributes"] = attrs

        body = DocumentsSinglePatchRequest.from_dict({"data": data})
        resp = _patch_document(
            client=self._c,
            project_id=project_id,
            space_id=space_id,
            document_name=document_name,
            body=body,
            workflow_action=workflow_action if workflow_action is not None else UNSET,
        )
        if resp.status_code in (200, 204):
            return _to_dict(resp)
        raise_from_response(resp)

    # -------------------------------------------------------------------
    # TODO: implement when Polarion 25.12 is available
    #       Once GET /projects/{projectId}/spaces/{spaceId}/documents exists:
    #
    # def list(self, project_id: str, space_id: str, *, page_number: int = 1,
    #          page_size: int = 100, query: Optional[str] = None,
    #          sort: Optional[str] = None, revision: Optional[str] = None,
    #          chunk_size: int = 200) -> List[Dict[str, Any]]:
    #     return list_items(
    #         _get_documents,
    #         page_param=self._page_param,
    #         size_param=self._size_param,
    #         page_number=page_number,
    #         page_size=page_size,     # -1 ⇒ handled client-side
    #         chunk_size=chunk_size,
    #         on_error=raise_from_response,
    #         client=self._c,
    #         project_id=project_id,
    #         space_id=space_id,
    #         query=query,
    #         sort=sort,
    #         revision=revision,
    #     )
    #
    # def iter(self, project_id: str, space_id: str, *, page_size: int = 100,
    #          query: Optional[str] = None, sort: Optional[str] = None,
    #          revision: Optional[str] = None, start_page: int = 1):
    #     resolved_page = self._page_param
    #     resolved_size = self._size_param
    #     def _one_page(**kw):
    #         call_kwargs = {
    #             "client": self._c,
    #             "project_id": project_id,
    #             "space_id": space_id,
    #             resolved_size: kw.get("page_size"),
    #             "query": query,
    #             "sort": sort,
    #             "revision": revision,
    #         }
    #         if resolved_page is not None:
    #             call_kwargs[resolved_page] = kw.get("page_index")
    #         return _get_documents(**call_kwargs)
    #     for page_obj in paged(
    #         _one_page,
    #         page_param=("page_index" if resolved_page is not None else None),
    #         size_param="page_size",
    #         start=start_page,
    #         page_size=page_size,
    #     ):
    #         for item in extract_items(page_obj):
    #             yield item
    #
    # def find_by_title(self, project_id: str, space_id: str, title: str, *,
    #                   limit: int = 1, page_size: int = 100, start_page: int = 1,
    #                   query_via_server: bool = True, strict_match: bool = False):
    #     q = f'title:"{title}"'
    #     if query_via_server and page_size == -1:
    #         items = self.list(project_id, space_id, page_number=start_page, page_size=-1, query=q)
    #         if strict_match:
    #             t = title.lower()
    #             items = [it for it in items if str((it.get("attributes") or {}).get("title", "")).lower() == t]
    #         return items[:limit] if limit > 0 else items
    #     if query_via_server:
    #         out = []
    #         t = title.lower()
    #         for it in self.iter(project_id, space_id, page_size=page_size, start_page=start_page, query=q):
    #             if strict_match:
    #                 attrs = (it.get("attributes") or {})
    #                 if str(attrs.get("title", "")).lower() != t:
    #                     continue
    #             out.append(it)
    #             if 0 < limit <= len(out):
    #                 break
    #         return out
    #     out = []
    #     t = title.lower()
    #     for it in self.iter(project_id, space_id, page_size=page_size, start_page=start_page):
    #         attrs = (it.get("attributes") or {})
    #         if str(attrs.get("title", "")).lower() == t:
    #             out.append(it)
    #             if 0 < limit <= len(out):
    #                 break
    #     return out
    # -------------------------------------------------------------------
