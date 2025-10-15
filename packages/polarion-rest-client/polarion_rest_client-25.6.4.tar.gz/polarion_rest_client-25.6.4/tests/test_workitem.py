# tests/test_workitem.py
import os
import uuid
import pytest

from polarion_rest_client.workitem import WorkItem
from polarion_rest_client.paging import list_page, extract_items, resolve_page_params
from polarion_rest_client.error import Unauthorized, Forbidden, NotFound, Conflict, raise_from_response

# low-level list endpoint for one-page helper
from polarion_rest_client.openapi.api.work_items.get_work_items import (
    sync_detailed as _get_work_items,
)


@pytest.mark.integration
def test_workitem_crud_paging_and_find(polarion_test_client):
    pc = polarion_test_client
    wi = WorkItem(pc)

    project_id = os.environ.get("POLARION_TEST_PROJECT_ID")
    if not project_id:
        pytest.skip("Set POLARION_TEST_PROJECT_ID to run Work Item integration tests.")
    wi_type = os.environ.get("POLARION_TEST_WI_TYPE", "task")

    title = f"SDK WI {uuid.uuid4().hex[:6]}"
    created_id = None

    try:
        # --- CREATE ---
        created = wi.create(
            project_id,
            wi_type=wi_type,
            title=title,
            description="Created by integration test",
        )
        created_full_id = created.get("id", "")
        assert created_full_id.startswith(f"{project_id}/")
        created_id = created_full_id.split("/", 1)[1]
        assert created_id

        # --- GET ---
        payload = wi.get(project_id, created_id)
        assert (payload.get("data") or {}).get("id") == f"{project_id}/{created_id}"

        # --- UPDATE ---
        updated_title = title + " (updated)"
        wi.update(project_id, created_id, title=updated_title)
        payload2 = wi.get(project_id, created_id)
        attrs = ((payload2.get("data") or {}).get("attributes") or {})
        if "title" in attrs:
            assert attrs["title"] == updated_title

        # --- LIST PAGE (generic pager helper, with resolved paging names) ---
        page_param, size_param = resolve_page_params(_get_work_items)
        page = list_page(
            _get_work_items,
            page_param=page_param,       # exact names from the generated client
            size_param=size_param,
            page_number=1,               # used only if page_param is not None
            page_size=1,
            on_error=raise_from_response,
            client=pc.gen,
            project_id=project_id,
            query=f'title:"{updated_title}"',
        )
        assert isinstance(page, dict) and "data" in page
        assert any(e.get("id", "").endswith(f"/{created_id}") for e in extract_items(page))

        # --- ITER (via shared pager; WorkItem maps to resolved names internally) ---
        items = list(
            wi.iter(
                project_id,
                page_size=1,
                query=f'title:"{updated_title}"',
            )
        )
        assert any(i.get("id", "").endswith(f"/{created_id}") for i in items)

        # --- FIND BY TITLE (server query) ---
        found = wi.find_by_title(project_id, updated_title, limit=1, query_via_server=True)
        assert found and found[0].get("id", "").endswith(f"/{created_id}")
        # Strict match
        found_strict = wi.find_by_title(project_id, updated_title, limit=1, query_via_server=True, strict_match=True)
        assert not found_strict

    except (Unauthorized, Forbidden) as e:
        pytest.skip(f"Insufficient permissions for Work Item CRUD/list/query: {e}")
    finally:
        # --- DELETE (best effort) ---
        if created_id:
            try:
                wi.delete_one(project_id, created_id)
            except (Unauthorized, Forbidden, NotFound, Conflict):
                pass
