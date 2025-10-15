# tests/test_workitem_batch.py
import os
import uuid
import pytest

from polarion_rest_client.workitem import WorkItem
from polarion_rest_client.error import Unauthorized, Forbidden, Conflict, NotFound


@pytest.mark.integration
def test_workitem_batch_update(polarion_test_client):
    pc = polarion_test_client
    wi = WorkItem(pc)

    project_id = os.getenv("POLARION_TEST_PROJECT_ID")
    if not project_id:
        pytest.skip("Set POLARION_TEST_PROJECT_ID to run Work Item integration tests.")
    wi_type = os.getenv("POLARION_TEST_WI_TYPE", "task")

    # Create 2 items
    token = uuid.uuid4().hex[:6]
    t1 = f"Batch WI A {token}"
    t2 = f"Batch WI B {token}"

    created_ids = []
    try:
        c1 = wi.create(project_id, wi_type=wi_type, title=t1, description="batch test A")
        c2 = wi.create(project_id, wi_type=wi_type, title=t2, description="batch test B")
        for c in (c1, c2):
            full_id = c.get("id", "")
            assert full_id.startswith(f"{project_id}/")
            created_ids.append(full_id.split("/", 1)[1])

        # Batch update titles
        new_title_suffix = " (batch-updated)"
        wi.update_many(
            project_id,
            items=[
                {"id": created_ids[0], "attributes": {"title": t1 + new_title_suffix}},
                {"id": created_ids[1], "attributes": {"title": t2 + new_title_suffix}},
            ],
        )

        # Verify
        g1 = wi.get(project_id, created_ids[0])
        g2 = wi.get(project_id, created_ids[1])
        a1 = ((g1.get("data") or {}).get("attributes") or {})
        a2 = ((g2.get("data") or {}).get("attributes") or {})
        assert a1.get("title") == t1 + new_title_suffix
        assert a2.get("title") == t2 + new_title_suffix

    except (Unauthorized, Forbidden) as e:
        pytest.skip(f"Permission issue running batch update test: {e}")
    finally:
        # Cleanup
        for wid in created_ids:
            try:
                wi.delete_one(project_id, wid)
            except NotFound:
                pass
            except (Unauthorized, Forbidden, Conflict):
                pass


@pytest.mark.integration
def test_workitem_batch_update_same_attrs(polarion_test_client):
    pc = polarion_test_client
    wi = WorkItem(pc)

    project_id = os.getenv("POLARION_TEST_PROJECT_ID")
    if not project_id:
        pytest.skip("Set POLARION_TEST_PROJECT_ID to run Work Item integration tests.")
    wi_type = os.getenv("POLARION_TEST_WI_TYPE", "task")

    token = uuid.uuid4().hex[:6]
    base_title = f"SameAttrs {token}"
    suffix = " (same-attrs)"

    created_ids = []
    try:
        # Create 3 items
        for i in range(3):
            c = wi.create(project_id, wi_type=wi_type, title=f"{base_title} #{i}", description="same attrs batch")
            full_id = c.get("id", "")
            assert full_id.startswith(f"{project_id}/")
            created_ids.append(full_id.split("/", 1)[1])

        # Apply the SAME attributes to all three in one call
        wi.update_many_same_attrs(
            project_id,
            created_ids,
            attributes={"title": base_title + suffix},
        )

        # Verify all three have the exact same title now
        for wid in created_ids:
            got = wi.get(project_id, wid)
            attrs = ((got.get("data") or {}).get("attributes") or {})
            assert attrs.get("title") == base_title + suffix

    except (Unauthorized, Forbidden) as e:
        pytest.skip(f"Permission issue running batch same-attrs test: {e}")
    finally:
        # Cleanup
        for wid in created_ids:
            try:
                wi.delete_one(project_id, wid)
            except NotFound:
                pass
            except (Unauthorized, Forbidden, Conflict):
                pass
