import os
import time
import uuid
import pytest

from polarion_rest_client.project import Project
from polarion_rest_client.error import JSONAPIError


@pytest.mark.integration
def test_project_flow_full_or_get_only(polarion_test_client):
    """
    Behavior:
      - If POLARION_TEMPLATE_ID is set -> run FULL CRUD flow (create, get, patch, delete/unmark).
      - Else -> run GET-only against POLARION_TEST_PROJECT_ID (must be set).
    """
    pc = polarion_test_client
    api = Project(pc)

    template_id = os.getenv("POLARION_TEMPLATE_ID")

    # -------- GET-only path (no template id provided) ----------
    if not template_id:
        existing_proj_id = os.getenv("POLARION_TEST_PROJECT_ID")
        if not existing_proj_id:
            pytest.skip(
                "Set POLARION_TEMPLATE_ID for full CRUD, or set POLARION_TEST_PROJECT_ID "
                "to run GET-only."
            )

        # GET-only assertion — no sparse-field params (some servers reject fields[projects])
        doc = api.get(existing_proj_id)
        assert (doc.get("data") or {}).get("id") == existing_proj_id
        # Optional sanity:
        assert (doc.get("data") or {}).get("type") == "projects"
        return  # GET-only done

    # -------- FULL CRUD path (template id provided) ------------
    # Create (async)
    nonce = uuid.uuid4().hex[:8]
    proj_id = f"rest-{int(time.time())}-{nonce}"
    job = api.create(
        proj_id,
        tracker_prefix=f"T{nonce[:2]}P",
        template_id=template_id,
        wait=True,
        poll_timeout_s=300,
    )
    assert isinstance(job, str) and job

    # List / Get (leave as-is; server may support fields here during full CRUD)
    lst = api.list(page_size=10, fields_projects=["id", "name", "trackerPrefix"])
    assert isinstance(lst, dict) and "data" in lst

    doc = api.get(proj_id, fields_projects=["id", "name", "trackerPrefix", "description"])
    assert (doc.get("data") or {}).get("id") == proj_id

    # Patch
    api.patch(
        proj_id,
        name="HL Client Test",
        description="updated by test",
        color="#336699",
        active=True,
    )
    doc2 = api.get(proj_id, fields_projects=["id", "name", "description", "color", "active"])
    attrs = ((doc2.get("data") or {}).get("attributes") or {})
    assert attrs.get("name") == "HL Client Test"
    assert (attrs.get("description") or {}).get("value") == "updated by test"
    assert attrs.get("color") == "#336699"
    assert attrs.get("active") is True

    # Delete (async) or Unmark fallback
    try:
        del_job = api.delete(proj_id, wait=True, poll_timeout_s=300)
        assert isinstance(del_job, str) and del_job
    except JSONAPIError:
        # If DELETE is disallowed on the server, fall back to unmark
        api.unmark(proj_id)

    # Final existence check
    assert not api.exists(proj_id)
