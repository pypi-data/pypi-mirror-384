from __future__ import annotations

from typing import Any, Dict, Iterator, List, Mapping, Optional

from .client import PolarionClient
from .error import raise_from_response
from .paging import (
    paged,
    extract_items,
    resolve_page_params,
    list_items,  # ← new: use generic fetch (supports page_size = -1)
)

# Low-level API (generated) — client uses `body=` for payloads
from polarion_rest_client.openapi.api.work_items.get_work_items import (
    sync_detailed as _get_work_items,
)
from polarion_rest_client.openapi.api.work_items.get_work_item import (
    sync_detailed as _get_work_item,
)
from polarion_rest_client.openapi.api.work_items.post_work_items import (
    sync_detailed as _post_work_items,
)
from polarion_rest_client.openapi.api.work_items.patch_work_item import (
    sync_detailed as _patch_work_item,
)
from polarion_rest_client.openapi.api.work_items.delete_work_items import (
    sync_detailed as _delete_work_items,
)
from polarion_rest_client.openapi.api.work_items.patch_work_items import (
    sync_detailed as _patch_work_items,
)

# Request models
from polarion_rest_client.openapi.models.workitems_list_post_request import (
    WorkitemsListPostRequest,
)
from polarion_rest_client.openapi.models.workitems_single_patch_request import (
    WorkitemsSinglePatchRequest,
)
from polarion_rest_client.openapi.models.workitems_list_delete_request import (
    WorkitemsListDeleteRequest,
)
from polarion_rest_client.openapi.models.workitems_list_patch_request import (
    WorkitemsListPatchRequest,
)


def _to_dict(resp) -> Dict[str, Any]:
    """Normalize a generated Response to a plain dict payload."""
    if resp is None or getattr(resp, "parsed", None) is None:
        return {}
    try:
        return resp.parsed.to_dict()
    except Exception:
        return resp.parsed


class WorkItem:
    """High-level Work Item operations built strictly on the current generated client API."""

    def __init__(self, pc: PolarionClient):
        self._c = pc.gen  # AuthenticatedClient
        # Resolve paging parameter names from the generated list endpoint (exact names, no guessing)
        self._page_param, self._size_param = resolve_page_params(_get_work_items)

    # ---------------------------- CREATE ----------------------------
    def create(
        self,
        project_id: str,
        *,
        wi_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        description_type: str = "text/plain",
        attributes: Optional[Mapping[str, Any]] = None,
        relationships: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        POST /projects/{projectId}/workitems
        Returns the first created resource reference (JSON:API resource object).
        """
        attrs: Dict[str, Any] = {"type": wi_type}
        if title is not None:
            attrs["title"] = title
        if description is not None:
            attrs["description"] = {"type": description_type, "value": description}
        if attributes:
            attrs.update(attributes)

        item: Dict[str, Any] = {"type": "workitems", "attributes": attrs}
        if relationships:
            item["relationships"] = dict(relationships)

        body = WorkitemsListPostRequest.from_dict({"data": [item]})
        resp = _post_work_items(client=self._c, project_id=project_id, body=body)
        if resp.status_code == 201 and resp.parsed:
            payload = _to_dict(resp)
            created = (payload.get("data") or [])
            return created[0] if created else payload
        raise_from_response(resp)

    # ------------------------------ GET ------------------------------
    def get(
        self,
        project_id: str,
        work_item_id: str,
        *,
        include: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /projects/{projectId}/workitems/{workItemId}"""
        resp = _get_work_item(
            client=self._c,
            project_id=project_id,
            work_item_id=work_item_id,
            include=include,
            revision=revision,
        )
        if resp.status_code == 200 and resp.parsed:
            return _to_dict(resp)
        raise_from_response(resp)

    # ----------------------------- UPDATE -----------------------------
    def update(
        self,
        project_id: str,
        work_item_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        description_type: str = "text/plain",
        attributes: Optional[Mapping[str, Any]] = None,
        relationships: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        PATCH /projects/{projectId}/workitems/{workItemId}
        Sends only provided fields.
        """
        attrs: Dict[str, Any] = {}
        if title is not None:
            attrs["title"] = title
        if description is not None:
            attrs["description"] = {"type": description_type, "value": description}
        if attributes:
            attrs.update(attributes)

        data: Dict[str, Any] = {
            "type": "workitems",
            "id": f"{project_id}/{work_item_id}",
        }
        if attrs:
            data["attributes"] = attrs
        if relationships:
            data["relationships"] = dict(relationships)

        body = WorkitemsSinglePatchRequest.from_dict({"data": data})
        resp = _patch_work_item(
            client=self._c,
            project_id=project_id,
            work_item_id=work_item_id,
            body=body,
        )
        if resp.status_code in (200, 204):
            return _to_dict(resp)
        raise_from_response(resp)

    # ----------------------------- BATCH UPDATE -----------------------------
    def update_many(
        self,
        project_id: str,
        items: List[Mapping[str, Any]],
        *,
        workflow_action: Optional[str] = None,
        change_type_to: Optional[str] = None,
    ) -> None:
        """
        PATCH /projects/{projectId}/workitems  (batch update)

        Each item may contain:
          {
            "id": "<short-id or 'project/workitem'>",   # required
            "attributes": {...},                         # optional
            "relationships": {...}                       # optional
          }

        Notes:
          * Short ids are automatically expanded to '<project>/<workitem>'.
          * Server returns 204 No Content on success.
        """
        if not items:
            return

        payload_items: List[Dict[str, Any]] = []
        for it in items:
            wid = it.get("id") or it.get("work_item_id")
            if not wid:
                raise ValueError("Each item must contain 'id' (short or project-qualified)")
            full_id = wid if "/" in str(wid) else f"{project_id}/{wid}"

            entry: Dict[str, Any] = {"type": "workitems", "id": full_id}
            attrs = it.get("attributes")
            rels = it.get("relationships")
            if attrs:
                entry["attributes"] = dict(attrs)
            if rels:
                entry["relationships"] = dict(rels)
            payload_items.append(entry)

        body = WorkitemsListPatchRequest.from_dict({"data": payload_items})
        resp = _patch_work_items(
            client=self._c,
            project_id=project_id,
            body=body,
            # OpenAPI query params (snake-cased by the generator)
            workflow_action=workflow_action,
            change_type_to=change_type_to,
        )
        if resp.status_code in (200, 204):
            return
        raise_from_response(resp)

    # ----------------------- BATCH UPDATE (same attrs) -----------------------
    def update_many_same_attrs(
        self,
        project_id: str,
        work_item_ids: List[str],
        *,
        attributes: Optional[Mapping[str, Any]] = None,
        relationships: Optional[Mapping[str, Any]] = None,
        workflow_action: Optional[str] = None,
        change_type_to: Optional[str] = None,
    ) -> None:
        """
        Convenience wrapper over update_many() when all items share the same change.

        Example:
            wi.update_many_same_attrs(
                "PRJ",
                ["PRJ-123", "PRJ-124", "PRJ-125"],
                attributes={"title": "New Title"},
            )

        You may also drive workflow transitions in bulk by passing workflow_action
        and/or change_type_to (OpenAPI first-class query params).
        """
        if not work_item_ids:
            return

        items = []
        for wid in work_item_ids:
            full_id = wid if "/" in str(wid) else f"{project_id}/{wid}"
            entry: Dict[str, Any] = {"type": "workitems", "id": full_id}
            if attributes:
                entry["attributes"] = dict(attributes)
            if relationships:
                entry["relationships"] = dict(relationships)
            items.append(entry)

        # Delegate to the canonical batch endpoint
        self.update_many(
            project_id,
            items=items,
            workflow_action=workflow_action,
            change_type_to=change_type_to,
        )

    # ----------------------------- DELETE -----------------------------
    def delete(self, project_id: str, work_item_ids: List[str]) -> None:
        """DELETE /projects/{projectId}/workitems (list delete)"""
        body = WorkitemsListDeleteRequest.from_dict(
            {"data": [{"type": "workitems", "id": f"{project_id}/{wid}"} for wid in work_item_ids]}
        )
        resp = _delete_work_items(client=self._c, project_id=project_id, body=body)
        if resp.status_code in (204,):
            return
        raise_from_response(resp)

    def delete_one(self, project_id: str, work_item_id: str) -> None:
        self.delete(project_id, [work_item_id])

    # ------------------------------ LIST (new, uses paging.list_items) ------------------------------
    def list(
        self,
        project_id: str,
        *,
        page_number: int = 1,
        page_size: int = 100,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        revision: Optional[str] = None,
        chunk_size: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Return work items as *items* (not the full page doc).

        - If page_size == -1: fetches *all pages* client-side (using `chunk_size` per request).
        - Otherwise: returns the items from the requested single page (page_number/page_size).

        This never sends -1 to the server; it’s handled locally in paging.list_items().
        """
        return list_items(
            _get_work_items,
            page_param=self._page_param,
            size_param=self._size_param,
            page_number=page_number,
            page_size=page_size,     # -1 ⇒ fetch-all handled by paging.list_items()
            chunk_size=chunk_size,
            on_error=raise_from_response,
            client=self._c,
            project_id=project_id,
            query=query,
            sort=sort,
            revision=revision,
        )

    # ------------------------------ ITERATE ------------------------------
    def iter(
        self,
        project_id: str,
        *,
        page_size: int = 100,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        revision: Optional[str] = None,
        start_page: int = 1,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate all work items using the shared pager; yields JSON:API resource objects.
        Uses the exact paging parameter names discovered from the generated client.
        """
        resolved_page_param = self._page_param
        resolved_size_param = self._size_param

        def _one_page(**kw):
            # paged(...) provides a generic page index under 'page_index' and size under 'page_size'
            call_kwargs: Dict[str, Any] = {
                "client": self._c,
                "project_id": project_id,
                resolved_size_param: kw.get("page_size"),
                "query": query,
                "sort": sort,
                "revision": revision,
            }
            if resolved_page_param is not None:
                call_kwargs[resolved_page_param] = kw.get("page_index")
            return _get_work_items(**call_kwargs)

        for page_obj in paged(
            _one_page,
            page_param=("page_index" if resolved_page_param is not None else None),
            size_param="page_size",
            start=start_page,
            page_size=page_size,
        ):
            for item in extract_items(page_obj):
                yield item

    # ------------------------ FIND BY TITLE ------------------------
    def find_by_title(
        self,
        project_id: str,
        title: str,
        *,
        limit: int = 1,
        page_size: int = 100,
        start_page: int = 1,
        query_via_server: bool = True,
        strict_match: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Find work items by title.

        Default (query_via_server=True, strict_match=False):
          • uses the server query `title:"<title>"`,
          • returns up to `limit` items without extra local equality filtering
            (some servers omit attributes.title unless fields/include are specified).

        If `page_size == -1`, this will fetch *all* matches in one list using `self.list(..., page_size=-1)`.
        If `strict_match=True`, a case-insensitive local equality check on attributes.title is applied.
        """
        q = f'title:"{title}"'
        results: List[Dict[str, Any]] = []

        if query_via_server and page_size == -1:
            # Fetch-all (one big list), then optionally filter & slice
            items = self.list(
                project_id,
                page_number=start_page,
                page_size=-1,  # sentinel: fetch-all via paging.list_items()
                query=q,
            )
            if strict_match:
                t = title.lower()
                items = [it for it in items if str((it.get("attributes") or {}).get("title", "")).lower() == t]
            return items[:limit] if limit > 0 else items

        if query_via_server:
            # Stream via iter() until we collect `limit`
            t = title.lower()
            for it in self.iter(project_id, page_size=page_size, start_page=start_page, query=q):
                if strict_match:
                    attrs = (it.get("attributes") or {})
                    if str(attrs.get("title", "")).lower() != t:
                        continue
                results.append(it)
                if 0 < limit <= len(results):
                    break
            return results

        # Client-side scan (no server query)
        t = title.lower()
        for it in self.iter(project_id, page_size=page_size, start_page=start_page):
            attrs = (it.get("attributes") or {})
            if str(attrs.get("title", "")).lower() == t:
                results.append(it)
                if 0 < limit <= len(results):
                    break
        return results
