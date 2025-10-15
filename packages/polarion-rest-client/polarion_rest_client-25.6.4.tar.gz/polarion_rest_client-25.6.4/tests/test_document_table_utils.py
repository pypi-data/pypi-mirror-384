import os
import pytest

from polarion_rest_client.document_table_utils import (
    parse_first_table_matching_columns,
    parse_all_tables_matching_columns,
    extract_document_tables_by_columns,
)


# --------------------------- Pure unit tests (no server) ---------------------------

HTML_ONE_TABLE = """
<html><body>
<table>
  <tr><th>A</th><th>B</th><th>C</th></tr>
  <tr><td>1</td><td>2</td><td>3</td></tr>
  <tr><td>4</td><td>5</td><td>6</td></tr>
</table>
</body></html>
"""

HTML_MULTI_TABLE = """
<html><body>
<table id="t0">
  <tr><th>X</th><th>Y</th></tr>
  <tr><td>9</td><td>8</td></tr>
</table>
<table id="t1">
  <tr><th>A</th><th>B</th><th>C</th></tr>
  <tr><td>7</td><td>8</td><td>9</td></tr>
</table>
<table id="t2">
  <tr><td>A</td><td>B</td><td>C</td></tr>
  <tr><td>k</td><td>l</td><td>m</td></tr>
</table>
</body></html>
"""


@pytest.mark.unit
def test_parse_first_table_matching_columns_single_match():
    df = parse_first_table_matching_columns(HTML_ONE_TABLE, ["A", "B", "C"])
    assert df is not None
    assert list(df.columns) == ["A", "B", "C"]
    assert df.shape == (2, 3)
    assert df.iloc[0, 0] == "1"


@pytest.mark.unit
def test_parse_all_tables_matching_columns_multi_match():
    dfs = parse_all_tables_matching_columns(HTML_MULTI_TABLE, ["A", "B", "C"])
    # tables t1 and t2 both match (one with th, one with td header)
    assert isinstance(dfs, list)
    assert len(dfs) == 2
    assert list(dfs[0].columns) == ["A", "B", "C"]
    assert list(dfs[1].columns) == ["A", "B", "C"]


# --------------------------- Optional integration (server) ---------------------------


@pytest.mark.integration
def test_extract_document_tables_by_columns_or_skip(polarion_test_client):
    """
    Integration:
      - Requires POLARION_TEST_PROJECT_ID and POLARION_TEST_DOCUMENT_NAME.
      - POLARION_TEST_SPACE_ID optional (defaults to _default).
      - POLARION_TEST_DOC_TABLE_EXPECTED_COLS must be set (comma-separated).
    """
    project_id = os.getenv("POLARION_TEST_PROJECT_ID")
    doc_name = os.getenv("POLARION_TEST_DOCUMENT_NAME")
    space_id = os.getenv("POLARION_TEST_SPACE_ID", "_default")
    cols = os.getenv("POLARION_TEST_DOC_TABLE_EXPECTED_COLS")

    if not (project_id and doc_name and cols):
        pytest.skip(
            "Set POLARION_TEST_PROJECT_ID, POLARION_TEST_DOCUMENT_NAME, "
            "and POLARION_TEST_DOC_TABLE_EXPECTED_COLS (comma-separated) for this test."
        )

    expected = [c.strip() for c in cols.split(",") if c.strip()]

    pc = polarion_test_client

    # First match
    df = extract_document_tables_by_columns(
        pc, project_id, space_id, doc_name, expected_columns=expected, all_matches=False
    )
    if df is not None:
        assert list(df.columns) == [c for c in expected]
        assert df.shape[1] == len(expected)

    # All matches
    dfs = extract_document_tables_by_columns(
        pc, project_id, space_id, doc_name, expected_columns=expected, all_matches=True
    )
    assert isinstance(dfs, list)
    for one in dfs:
        assert list(one.columns) == [c for c in expected]
