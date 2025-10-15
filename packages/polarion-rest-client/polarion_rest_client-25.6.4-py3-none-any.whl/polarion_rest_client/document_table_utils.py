from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from bs4 import BeautifulSoup  # type: ignore
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore

from .client import PolarionClient
from .document_part import DocumentPart


_WS_RE = re.compile(r"\s+", re.UNICODE)


def _clean(s: str) -> str:
    """Normalize whitespace and non-breaking spaces."""
    return _WS_RE.sub(" ", (s or "").replace("\xa0", " ")).strip()


def extract_cell_text(cell) -> str:
    """Return the text content of a <td>/<th> cell with normalized whitespace."""
    return _clean(cell.get_text(" ", strip=True))


def _headers_match(found: Sequence[str], expected: Sequence[str]) -> bool:
    """
    Case-insensitive, order-sensitive header match (trimmed/normalized).
    We still return DataFrames with the original header text.
    """
    f = [_clean(x).lower() for x in found]
    e = [_clean(x).lower() for x in expected]
    return f == e


# --------------------------- HTML → DataFrame parsers (unit-tested) ---------------------------

def parse_first_table_matching_columns(html: str, expected_columns: Sequence[str]) -> Optional["pd.DataFrame"]:
    """
    Parse the first <table> whose header row matches `expected_columns` (order-sensitive, case-insensitive).
    Returns a DataFrame or None if not found.
    """
    if pd is None:  # pragma: no cover
        raise ImportError("pandas is required for table extraction")

    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        thead = table.find("thead")
        first_row = thead.find("tr") if thead else table.find("tr")
        if not first_row:
            continue

        header_cells = first_row.find_all("th")
        if header_cells:
            headers = [extract_cell_text(th) for th in header_cells]
            data_rows = table.find_all("tr")[1:]
        else:
            td_cells = first_row.find_all("td")
            headers = [extract_cell_text(td) for td in td_cells]
            data_rows = table.find_all("tr")[1:]

        if not headers or not _headers_match(headers, expected_columns):
            continue

        rows: List[List[str]] = []
        for tr in data_rows:
            cells = tr.find_all(["td", "th"])
            row = [extract_cell_text(c) for c in cells]
            if len(row) < len(headers):
                row += [""] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[: len(headers)]
            rows.append(row)

        return pd.DataFrame(rows, columns=list(headers))
    return None


def parse_all_tables_matching_columns(html: str, expected_columns: Sequence[str]) -> List["pd.DataFrame"]:
    """
    Parse all <table> elements in the HTML whose headers match `expected_columns`.
    Returns a list of DataFrames (possibly empty).
    """
    if pd is None:  # pragma: no cover
        raise ImportError("pandas is required for table extraction")

    soup = BeautifulSoup(html, "html.parser")
    dfs: List["pd.DataFrame"] = []
    for table in soup.find_all("table"):
        thead = table.find("thead")
        first_row = thead.find("tr") if thead else table.find("tr")
        if not first_row:
            continue

        header_cells = first_row.find_all("th")
        if header_cells:
            headers = [extract_cell_text(th) for th in header_cells]
            data_rows = table.find_all("tr")[1:]
        else:
            td_cells = first_row.find_all("td")
            headers = [extract_cell_text(td) for td in td_cells]
            data_rows = table.find_all("tr")[1:]

        if not headers or not _headers_match(headers, expected_columns):
            continue

        rows: List[List[str]] = []
        for tr in data_rows:
            cells = tr.find_all(["td", "th"])
            row = [extract_cell_text(c) for c in cells]
            if len(row) < len(headers):
                row += [""] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[: len(headers)]
            rows.append(row)

        dfs.append(pd.DataFrame(rows, columns=list(headers)))
    return dfs


# --------------------------- Server helpers (uses DocumentPart) ---------------------------

def _iter_document_parts(
    pc: PolarionClient,
    project_id: str,
    space_id: str,
    document_name: str,
) -> Iterable[Tuple[str, dict]]:
    """
    Yield (part_id, part_item) for ALL parts in the document.
    No ID/type heuristics; some servers don’t use 'table_' in IDs.
    """
    dp = DocumentPart(pc)
    for item in dp.iter(project_id, space_id, document_name, page_size=100):
        part_id = item.get("id", "")
        if part_id:
            yield part_id, item


def _iter_document_parts_filtered_by_type(
    pc: PolarionClient,
    project_id: str,
    space_id: str,
    document_name: str,
    *,
    type_value: str = "table",
) -> Iterable[Tuple[str, dict]]:
    """
    Prefer fast path: list parts requesting only 'type' and filter client-side.
    Falls back to empty if server returns no attributes; caller may then scan all parts.
    """
    dp = DocumentPart(pc)
    # ask for minimal attrs so LIST is cheap
    parts = dp.list(
        project_id,
        space_id,
        document_name,
        page_number=1,
        page_size=-1,                # fetch all (client-side paging in DocumentPart)
        fields_parts=["type", "title"],
    )
    for it in parts:
        attrs = it.get("attributes") or {}
        if (attrs.get("type") or "").lower() == type_value:
            yield it.get("id", ""), it


def _extract_html_from_attrs(attrs: dict) -> Optional[str]:
    """
    Best-effort extraction of HTML from a part's attributes across server variants.
    Accepts plain strings or dict objects with 'value'/'html'.
    """
    keys = ("content", "contentHtml", "content_html", "html")
    for k in keys:
        v = attrs.get(k)
        if v is None:
            continue
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            if isinstance(v.get("value"), str):
                return v["value"]
            if isinstance(v.get("html"), str):
                return v["html"]
    v = attrs.get("value")
    if isinstance(v, str):
        return v
    return None


def _fetch_part_html(
    pc: PolarionClient,
    project_id: str,
    space_id: str,
    document_name: str,
    part_id: str,
) -> Optional[str]:
    """
    Fetch part payload and return its HTML content (if any).
    Uses fields_parts='@all' via the deep-field support in DocumentPart,
    so the server returns full content reliably.
    """
    dp = DocumentPart(pc)
    part = dp.get(
        project_id,
        space_id,
        document_name,
        part_id.split("/")[-1],
        fields_parts="@all",  # ensure HTML content is present
    )
    data = part.get("data") or {}
    attrs = data.get("attributes") or {}
    return _extract_html_from_attrs(attrs)


# --------------------------- Public high-level API ---------------------------

def extract_document_tables_by_columns(
    pc: PolarionClient,
    project_id: str,
    space_id: str,
    document_name: str,
    expected_columns: Sequence[str],
    *,
    all_matches: bool = False,
    prefer_type_filter: bool = True,   # ← new flag
) -> Union["pd.DataFrame", List["pd.DataFrame"], None]:
    """
    List parts → (optionally) pre-filter by type='table' → fetch HTML → parse + match headers.
    Returns one DataFrame (default), all matches (list), or None/[] if none match.
    """
    if pd is None:  # pragma: no cover
        raise ImportError("pandas is required for table extraction")

    def _parse_selected(candidates: Iterable[Tuple[str, dict]]):
        if all_matches:
            out: List["pd.DataFrame"] = []
            for part_id, _ in candidates:
                html = _fetch_part_html(pc, project_id, space_id, document_name, part_id)
                if not html:
                    continue
                df = parse_first_table_matching_columns(html, expected_columns)
                if df is not None:
                    out.append(df)
            return out
        else:
            for part_id, _ in candidates:
                html = _fetch_part_html(pc, project_id, space_id, document_name, part_id)
                if not html:
                    continue
                df = parse_first_table_matching_columns(html, expected_columns)
                if df is not None:
                    return df
            return None

    # 1) Fast path: type filter (table)
    if prefer_type_filter:
        candidates = list(_iter_document_parts_filtered_by_type(pc, project_id, space_id, document_name))
        result = _parse_selected(candidates)
        # Found something? return now.
        if (isinstance(result, list) and result) or (result is not None and not isinstance(result, list)):
            return result

    # 2) Fallback: scan all parts (covers embedded tables in non-'table' parts)
    candidates_all = list(_iter_document_parts(pc, project_id, space_id, document_name))
    return _parse_selected(candidates_all)
