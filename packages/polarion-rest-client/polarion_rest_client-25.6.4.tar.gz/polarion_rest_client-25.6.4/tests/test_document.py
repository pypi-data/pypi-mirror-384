import os
import uuid
import pytest

from polarion_rest_client.document import Document


@pytest.mark.integration
def test_document_create_get_update_or_get_only(polarion_test_client):
    """
    Behavior:
      - If POLARION_TEST_DOC_CREATE_OK == '1' -> run CREATE + GET + UPDATE.
      - Else if POLARION_TEST_DOCUMENT_NAME is set -> run GET-only.
      - Else -> skip with guidance.

    Note: Current OpenAPI exposes no DELETE or LIST for Documents.
    """
    pc = polarion_test_client
    api = Document(pc)

    project_id = os.getenv("POLARION_TEST_PROJECT_ID")
    space_id = os.getenv("POLARION_TEST_SPACE_ID")
    if not project_id:
        pytest.skip("Set POLARION_TEST_PROJECT_ID to run Document tests.")
    if not space_id:
        space_id = "_default"

    allow_create = os.getenv("POLARION_TEST_DOC_CREATE_OK") == "1"

    # -------- GET-only path ----------
    if not allow_create:
        doc_name = os.getenv("POLARION_TEST_DOCUMENT_NAME")
        if not doc_name:
            pytest.skip(
                "Set POLARION_TEST_DOC_CREATE_OK=1 for create flow, "
                "or set POLARION_TEST_DOCUMENT_NAME for GET-only."
            )
        payload = api.get(project_id, space_id, doc_name)
        assert (payload.get("data") or {}).get("id", "").endswith(f"/{doc_name}")
        return

    # -------- CREATE + GET + UPDATE ---
    token = uuid.uuid4().hex[:6]
    module_name = f"hl-doc-{token}"
    title = f"HL Doc {token}"

    created = api.create(
        project_id,
        space_id,
        module_name=module_name,
        title=title,
        doc_type="req_specification",
        status="draft",
        # send valid HTML and declare its type
        home_page_content=f"<p>Created by tests ({token})</p>",
        home_page_content_type="text/html",
        structure_link_role=os.getenv("POLARION_TEST_DOC_STRUCTURE_ROLE", "relates_to"),
    )
    created_full_id = created.get("id", "")
    assert created_full_id.endswith(f"/{module_name}")

    got = api.get(project_id, space_id, module_name)
    assert (got.get("data") or {}).get("id", "") == created_full_id

    new_title = title + " (updated)"
    api.update(project_id, space_id, module_name, title=new_title)
    got2 = api.get(project_id, space_id, module_name)
    attrs = ((got2.get("data") or {}).get("attributes") or {})
    if "title" in attrs:
        assert attrs["title"] == new_title


# ---------------------------------------------------------------------------
# TODO: implement when Polarion 25.12 is available
# Add paging & search tests once the list endpoint exists:
#
# @pytest.mark.integration
# def test_document_list_iter_find(polarion_test_client):
#     pc = polarion_test_client
#     api = Document(pc)
#     project_id = os.getenv("POLARION_TEST_PROJECT_ID")
#     space_id = os.getenv("POLARION_TEST_SPACE_ID")
#     if not project_id or not space_id:
#         pytest.skip("Set POLARION_TEST_PROJECT_ID and POLARION_TEST_SPACE_ID.")
#
#     # Create a couple of docs, then:
#     items = api.list(project_id, space_id, page_number=1, page_size=1, query='title:"something"')
#     assert items
#
#     got = list(api.iter(project_id, space_id, page_size=1, query='title:"something"'))
#     assert got
#
#     found = api.find_by_title(project_id, space_id, "something", limit=1, query_via_server=True)
#     assert found
# ---------------------------------------------------------------------------
