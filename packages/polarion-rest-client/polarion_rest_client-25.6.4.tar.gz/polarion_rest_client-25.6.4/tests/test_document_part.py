import os
import pytest

from polarion_rest_client.document_part import DocumentPart


@pytest.mark.integration
def test_document_part_list_and_get_or_skip(polarion_test_client):
    """
    Read-only tests for Document Parts:
      * Requires POLARION_TEST_PROJECT_ID and POLARION_TEST_DOCUMENT_NAME
      * POLARION_TEST_SPACE_ID is optional (defaults to _default)

    Flow:
      - List parts with small page_size (paging exercised)
      - If there is at least one part, GET it
    """
    pc = polarion_test_client
    api = DocumentPart(pc)

    project_id = os.getenv("POLARION_TEST_PROJECT_ID")
    doc_name = os.getenv("POLARION_TEST_DOCUMENT_NAME")
    space_id = os.getenv("POLARION_TEST_SPACE_ID", "_default")

    if not project_id or not doc_name:
        pytest.skip(
            "Set POLARION_TEST_PROJECT_ID and POLARION_TEST_DOCUMENT_NAME "
            "to run Document Part integration tests."
        )

    # LIST
    items = api.list(project_id, space_id, doc_name, page_number=1, page_size=2)
    assert isinstance(items, list)
    # If there are items, try GET for the first one
    if items:
        first = items[0]
        part_id = first.get("id", "")
        assert part_id and part_id.startswith(f"{project_id}/{space_id}/{doc_name}/")
        got = api.get(
            project_id,
            space_id,
            doc_name,
            part_id.split("/")[-1],  # last path segment is the partId
        )
        assert (got.get("data") or {}).get("id", "") == part_id

    # ITER (grab up to 5 just to exercise pagination)
    seen = []
    for it in api.iter(project_id, space_id, doc_name, page_size=2):
        seen.append(it)
        if len(seen) >= 5:
            break
    assert isinstance(seen, list)
