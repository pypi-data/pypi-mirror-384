"""
DocMD models and helpers.

This module defines a compact, index-aware DocMD representation for Google Docs
documents, plus helpers to build DocMD from a Document and render/parse the
string format expected for LLM consumption.

Example DocMD as a string:
@document_id: 1t9igNb2XSo_1FOkFXy3bI9bIQKvQgk_JUWpoomADkX4
@revision_id: ALBJ4LtLdNr30MBQxnybwwss4gpEhWixhJrjhCy29BVprpmcjurkGCqQOPyW2w9RibJcFdvchJqJ5bd-V_-K4g

[H1 1-18 HEADING_1 headingId=h.5wd8jf8y8o2n styles=italic:1-18,fontSize=23.0pt:1-18] Project Lightning
[P1 19-51 PARAGRAPH styles=bold:19-51] Confidential - Internal Use Only
[P2 52-73 PARAGRAPH styles=bold:52-56] Date: August 23, 2025
[P3 74-104 PARAGRAPH styles=bold:74-86] Prepared by: [Bob F, Alice H.]
[P4 105-115 PARAGRAPH styles=bold:105-113] Version: 1
[P5 116-117 PARAGRAPH]
[H2 118-138 HEADING_2 headingId=h.775rila7csjc styles=color=rgb(0.20784314,0.21568628,0.26666668):118-137,fontSize=17.0pt:118-137] 1. Executive Summary
[P6 139-731 PARAGRAPH] Project Lightning is a strategic initiative aimed at developing an advanced, AI-enhanced platform capable of processing and responding to intricate data requests with near real-time efficiency. The primary goals of this project are to achieve a 60% reduction in latency, including meeting p95 latency of 100 ms and p99 latency of 170 ms (measured from ingress receive to first byte to client and encompassing authentication, routing, model call, and post-processing), enhance system reliability to 99.99%, and introduce adaptive scaling mechanisms to effectively manage fluctuating workloads.
[P7 732-1373 PARAGRAPH] The team is targeting a 60% reduction in latency, aiming for a p95 latency of ≤100 ms and a p99 latency of ≤170 ms, covering end-to-end processes from ingress to client delivery. Reliability is set at 99.99%, equating to a 13-minute error budget per quarter. Adaptive scaling should handle up to 1 million concurrent sessions within five minutes, maintaining an error rate below 0.1%. The architecture involves a comprehensive flow from ingress to egress, with specific latency budgets and cold-start mitigations in place. Observability and data security are emphasized through advanced logging, monitoring, and stringent security protocols.
[P8 1374-1374 PARAGRAPH]
[H3 1375-1388 HEADING_2 headingId=h.54wtcb9egpyb styles=color=rgb(0.20784314,0.21568628,0.26666668):1375-1388,fontSize=17.0pt:1375-1388] 2. Objectives
[UL1 1389-1469 UL_ITEM listId=kix.xqqibvne3ovq styles=bold:1389-1399,italic:1389-1399] Performance - We will optimize algorithms to enhance data processing efficiency.
[UL2 1470-1558 UL_ITEM listId=kix.xqqibvne3ovq styles=bold:1470-1480,italic:1470-1480,italic:1483-1483] Reliability - Build redundancy into all critical components to ensure continuous uptime.
[UL3 1559-1645 UL_ITEM listId=kix.xqqibvne3ovq styles=bold:1559-1569,italic:1559-1569] Scalability - Implement adaptive scaling to increase capacity from 10,000 to 1,000,000
[UL4 1646-1746 UL_ITEM listId=kix.xqqibvne3ovq styles=bold:1646-1658,italic:1646-1658] Observability - Integrate advanced logging, monitoring, and alerting for proactive issue resolution.
[P9 1747-1747 PARAGRAPH]
[P10 1748-1748 PARAGRAPH]
[TABLE1 1749-1831 TABLE rows=2 cols=4]
[TR1 1750-1805 TABLE_ROW row=0]
[TC1 1751-1764 TABLE_CELL row=0 col=0] Performance
[TC2 1764-1777 TABLE_CELL row=0 col=1] Reliability
[TC3 1777-1790 TABLE_CELL row=0 col=2] Scalability
[TC4 1790-1805 TABLE_CELL row=0 col=3] Observability
[TR2 1805-1830 TABLE_ROW row=1]
[TC5 1806-1812 TABLE_CELL row=1 col=0] DONE
[TC6 1812-1818 TABLE_CELL row=1 col=1] DONE
[TC7 1818-1824 TABLE_CELL row=1 col=2] DONE
[TC8 1824-1830 TABLE_CELL row=1 col=3] DONE
[H4 1831-1831 HEADING_2 headingId=h.7h4kp6390h67]
[H5 1832-1840 HEADING_2 headingId=h.cx3le136ppi styles=color=rgb(0.20784314,0.21568628,0.26666668):1832-1840,fontSize=17.0pt:1832-1840] 3. Scope
[P11 1841-1850 PARAGRAPH styles=bold:1841-1850] In Scope:
[UL5 1851-1880 UL_ITEM listId=kix.s0qmo6yotpsp] Backend architecture redesign
[UL6 1881-1915 UL_ITEM listId=kix.s0qmo6yotpsp] AI model selection and fine-tuning
[UL7 1916-1953 UL_ITEM listId=kix.s0qmo6yotpsp] Cloud-based deployment infrastructure
[UL8 1954-1995 UL_ITEM listId=kix.s0qmo6yotpsp] Load testing and performance benchmarking
[UL9 1996-2026 UL_ITEM listId=kix.s0qmo6yotpsp] Altering the document's style.
[P12 2027-2040 PARAGRAPH styles=bold:2027-2040] Out of Scope:
[UL10 2041-2062 UL_ITEM listId=kix.3940kw992qy5] End-user UI/UX design
[UL11 2063-2087 UL_ITEM listId=kix.3940kw992qy5] Public launch activities
[UL12 2088-2139 UL_ITEM listId=kix.3940kw992qy5] Purchasing billboards that show off our new feature
"""  # noqa: E501

from collections.abc import Callable
from enum import Enum

from pydantic import BaseModel

from arcade_google_docs.models.document import (
    Document,
    NamedStyleType,
    Paragraph,
    Table,
    TextStyle,
)


class DocMDBlockType(Enum):
    PARAGRAPH = "PARAGRAPH"
    HR = "HR"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"
    UL_ITEM = "UL_ITEM"
    OL_ITEM = "OL_ITEM"  # Reserved for future use if ordering is inferred
    TABLE = "TABLE"
    TABLE_ROW = "TABLE_ROW"
    TABLE_CELL = "TABLE_CELL"


class DocMDBlock(BaseModel):
    id: str
    startIndex: int
    endIndex: int
    type: str
    attrs: dict[str, str] | None = None
    text: str

    def to_string(self) -> str:
        """Return a string representation of the block."""
        attr_parts: list[str] = []
        if self.attrs:
            for k, v in self.attrs.items():
                if v is None:
                    continue
                # Skip tab attribute if it's empty (default tab)
                if k == "tab" and not v:
                    continue
                attr_parts.append(f"{k}={v}")
        attr_str = " ".join(attr_parts)
        if attr_str:
            return (
                f"[{self.id} {self.startIndex}-{self.endIndex} {self.type} {attr_str}] {self.text}"
            )
        else:
            return f"[{self.id} {self.startIndex}-{self.endIndex} {self.type}] {self.text}"


class DocMD(BaseModel):
    documentId: str
    revisionId: str | None = None
    tab: str = ""
    blocks: list[DocMDBlock]

    @property
    def block_ids(self) -> list[str]:
        return [b.id for b in self.blocks]

    def get_block_from_id(self, block_id: str) -> DocMDBlock:
        return self.blocks[self.block_ids.index(block_id)]

    def to_string(self) -> str:
        lines: list[str] = []
        lines.append(f"@document_id: {self.documentId}")
        if self.revisionId:
            lines.append(f"@revision_id: {self.revisionId}")
        if self.tab:  # Only include @tab line if tab is not empty
            lines.append(f"@tab: {self.tab}")
        lines.append("")
        for b in self.blocks:
            lines.append(b.to_string())
        return "\n".join(lines)

    def get_docmd_with_annotated_block(self, block_id: str) -> "DocMD":
        """
        Get a new DocMD with the provided block id's text
        annotated with location tags on each word.
        """

        block = self.get_block_from_id(block_id)
        text = block.text

        annotated_text = ""
        i = 0

        while i < len(text):
            if text[i].isspace():
                # Preserve whitespace
                annotated_text += text[i]
                i += 1
            else:
                # We're at the start of a word, find where it ends
                word_start = i
                while i < len(text) and not text[i].isspace():
                    i += 1

                word = text[word_start:i]
                word_length = len(word)
                start_pos = block.startIndex + word_start
                end_pos = start_pos + word_length

                annotated_text += f"<@{start_pos}>{word}</@{end_pos}>"

        annotated_block = DocMDBlock(
            id=block.id,
            startIndex=block.startIndex,
            endIndex=block.endIndex,
            type=block.type,
            attrs=block.attrs,
            text=annotated_text,
        )

        new_blocks = []
        for b in self.blocks:
            if b.id == block_id:
                new_blocks.append(annotated_block)
            else:
                new_blocks.append(b)

        return DocMD(
            documentId=self.documentId,
            revisionId=self.revisionId,
            tab=self.tab,
            blocks=new_blocks,
        )


def build_docmd(document: Document) -> DocMD:  # noqa: C901
    doc_id = document.documentId or ""
    rev = document.revisionId
    tab = ""

    counters: dict[str, int] = {
        "H": 0,
        "P": 0,
        "UL": 0,
        "OL": 0,
        "HR": 0,
        "TABLE": 0,
        "TR": 0,
        "TC": 0,
    }

    def next_id(prefix: str) -> str:
        counters[prefix] += 1
        return f"{prefix}{counters[prefix]}"

    blocks: list[DocMDBlock] = []

    for se in document.body.content or [] if document.body else []:
        if se.paragraph is not None:
            p: Paragraph = se.paragraph
            named = p.paragraphStyle.namedStyleType if p.paragraphStyle else None
            is_heading = named in (
                NamedStyleType.HEADING_1,
                NamedStyleType.HEADING_2,
                NamedStyleType.HEADING_3,
                NamedStyleType.HEADING_4,
                NamedStyleType.HEADING_5,
                NamedStyleType.HEADING_6,
            )

            block_type: str
            block_id: str
            attrs: dict[str, str] = {}
            # Only add tab attribute if it's not empty (not the default tab)
            if tab:
                attrs["tab"] = tab

            if is_heading:
                level = int(str(named).split("_")[-1])
                block_type = f"HEADING_{level}"
                block_id = next_id("H")
                if p.paragraphStyle and p.paragraphStyle.headingId:
                    attrs["headingId"] = p.paragraphStyle.headingId
            else:
                if p.bullet and p.bullet.listId:
                    block_type = DocMDBlockType.UL_ITEM.value
                    block_id = next_id("UL")
                    attrs["listId"] = p.bullet.listId
                    if p.bullet.nestingLevel is not None:
                        attrs["level"] = str(p.bullet.nestingLevel)
                else:
                    block_type = DocMDBlockType.PARAGRAPH.value
                    block_id = next_id("P")

            vis_start, vis_end, text, style_runs = _visible_span_and_text(p)
            start = vis_start if vis_start is not None else se.startIndex or 0
            end = vis_end if vis_end is not None else se.endIndex or start
            text_line = (text or "").rstrip("\n")

            # Add style ranges to attrs if any styles are present
            if style_runs:
                style_ranges = _format_style_ranges(style_runs, start)
                if style_ranges:
                    attrs["styles"] = style_ranges

            blocks.append(
                DocMDBlock(
                    id=block_id,
                    startIndex=start,
                    endIndex=end,
                    type=block_type,
                    attrs=attrs if attrs else None,
                    text=text_line,
                )
            )

        elif se.table is not None:
            _process_table(se.table, se, next_id, tab, blocks)

    return DocMD(documentId=doc_id, revisionId=rev, tab=tab, blocks=blocks)


def _process_table(  # type: ignore[no-untyped-def]
    table: Table,
    se,
    next_id_func: Callable[[str], str],
    tab: str,
    blocks: list[DocMDBlock],
) -> None:
    """Process a table structural element and add table/row/cell blocks."""
    table_id = next_id_func("TABLE")
    table_attrs: dict[str, str] = {}

    # Only add tab attribute if it's not empty (not the default tab)
    if tab:
        table_attrs["tab"] = tab

    if table.rows is not None:
        table_attrs["rows"] = str(table.rows)
    if table.columns is not None:
        table_attrs["cols"] = str(table.columns)

    table_start = se.startIndex or 0
    table_end = se.endIndex or table_start

    blocks.append(
        DocMDBlock(
            id=table_id,
            startIndex=table_start,
            endIndex=table_end,
            type=DocMDBlockType.TABLE.value,
            attrs=table_attrs if table_attrs else None,
            text="",
        )
    )

    for row_idx, table_row in enumerate(table.tableRows or []):
        _process_table_row(table_row, row_idx, table_start, next_id_func, tab, blocks)


def _process_table_row(  # type: ignore[no-untyped-def]
    table_row,
    row_idx: int,
    table_start: int,
    next_id_func: Callable[[str], str],
    tab: str,
    blocks: list[DocMDBlock],
) -> None:
    """Process a table row and add row/cell blocks."""
    row_id = next_id_func("TR")
    row_attrs: dict[str, str] = {"row": str(row_idx)}

    if tab:
        row_attrs["tab"] = tab

    row_start = table_row.startIndex or table_start
    row_end = table_row.endIndex or row_start

    blocks.append(
        DocMDBlock(
            id=row_id,
            startIndex=row_start,
            endIndex=row_end,
            type=DocMDBlockType.TABLE_ROW.value,
            attrs=row_attrs,
            text="",
        )
    )

    for cell_idx, table_cell in enumerate(table_row.tableCells or []):
        _process_table_cell(table_cell, row_idx, cell_idx, row_start, next_id_func, tab, blocks)


def _process_table_cell(  # type: ignore[no-untyped-def]  # noqa: C901
    table_cell,
    row_idx: int,
    cell_idx: int,
    row_start: int,
    next_id_func: Callable[[str], str],
    tab: str,
    blocks: list[DocMDBlock],
) -> None:
    """Process a table cell and add cell block."""
    cell_id = next_id_func("TC")
    cell_attrs: dict[str, str] = {
        "row": str(row_idx),
        "col": str(cell_idx),
    }

    if tab:
        cell_attrs["tab"] = tab

    # Add cell styling attributes if present
    if (
        table_cell.tableCellStyle
        and table_cell.tableCellStyle.rowSpan is not None
        and table_cell.tableCellStyle.rowSpan > 1
    ):
        cell_attrs["rowspan"] = str(table_cell.tableCellStyle.rowSpan)

    if (
        table_cell.tableCellStyle
        and table_cell.tableCellStyle.columnSpan is not None
        and table_cell.tableCellStyle.columnSpan > 1
    ):
        cell_attrs["colspan"] = str(table_cell.tableCellStyle.columnSpan)

    cell_start = table_cell.startIndex or row_start
    cell_end = table_cell.endIndex or cell_start

    # Extract text content from cell
    cell_text_parts: list[str] = []
    cell_style_runs: list[dict] = []
    if table_cell.content:
        for cell_se in table_cell.content:
            if cell_se.paragraph:
                _, _, text, style_runs = _visible_span_and_text(cell_se.paragraph)
                if text:
                    cell_text_parts.append(text.rstrip("\n"))
                # Collect style runs for the cell (we'll merge them if needed)
                if style_runs:
                    cell_style_runs.extend(style_runs)

    cell_text = " ".join(cell_text_parts)

    # Add style ranges to cell attrs if any styles are present
    if cell_style_runs:
        style_ranges = _format_style_ranges(cell_style_runs, cell_start)
        if style_ranges:
            cell_attrs["styles"] = style_ranges

    blocks.append(
        DocMDBlock(
            id=cell_id,
            startIndex=cell_start,
            endIndex=cell_end,
            type=DocMDBlockType.TABLE_CELL.value,
            attrs=cell_attrs,
            text=cell_text,
        )
    )


def _visible_span_and_text(p: Paragraph) -> tuple[int | None, int | None, str, list[dict]]:
    """Extract visible text and style information from a paragraph.

    Returns:
        tuple of (start_index, end_index, text_content, style_runs)
        where style_runs is a list of dicts with style info and relative positions
    """
    start: int | None = None
    end: int | None = None
    parts: list[str] = []
    style_runs: list[dict] = []

    for el in p.elements or []:
        if el.textRun and el.textRun.content is not None:
            if start is None and el.startIndex is not None:
                start = el.startIndex
            if el.endIndex is not None:
                end = el.endIndex - 1

            # Track style information for this text run
            if el.textRun.textStyle and el.startIndex is not None and el.endIndex is not None:
                style_info = _extract_text_style(el.textRun.textStyle)
                if style_info:  # Only add if there are actual styles
                    style_runs.append({
                        "start": el.startIndex,
                        "end": el.endIndex - 1,
                        "styles": style_info,
                    })

            parts.append(el.textRun.content)
        elif el.horizontalRule is not None:
            if start is None and el.startIndex is not None:
                start = el.startIndex
            if el.endIndex is not None:
                end = el.endIndex - 1

    return start, end, "".join(parts), style_runs


def _extract_text_style(text_style: TextStyle) -> dict[str, bool | str | int]:  # noqa: C901
    """Extract relevant style properties from a TextStyle object."""
    styles: dict[str, bool | str | int] = {}

    # Boolean styles
    if text_style.bold:
        styles["bold"] = True
    if text_style.italic:
        styles["italic"] = True
    if text_style.underline:
        styles["underline"] = True
    if text_style.strikethrough:
        styles["strikethrough"] = True

    # Color styles
    if text_style.backgroundColor and text_style.backgroundColor.color:
        rgb = text_style.backgroundColor.color.rgbColor
        if rgb:
            styles["bgColor"] = f"rgb({rgb.red or 0},{rgb.green or 0},{rgb.blue or 0})"

    if text_style.foregroundColor and text_style.foregroundColor.color:
        rgb = text_style.foregroundColor.color.rgbColor
        if rgb:
            styles["color"] = f"rgb({rgb.red or 0},{rgb.green or 0},{rgb.blue or 0})"

    # Font size
    if text_style.fontSize and text_style.fontSize.magnitude:
        styles["fontSize"] = f"{text_style.fontSize.magnitude}pt"

    # Font family
    if text_style.weightedFontFamily:
        if text_style.weightedFontFamily.fontFamily:
            styles["font"] = text_style.weightedFontFamily.fontFamily
        if text_style.weightedFontFamily.weight and text_style.weightedFontFamily.weight != 400:
            styles["fontWeight"] = text_style.weightedFontFamily.weight

    # Baseline offset
    if text_style.baselineOffset and text_style.baselineOffset != "NONE":
        styles["baseline"] = text_style.baselineOffset.lower()

    return styles


def _format_style_ranges(style_runs: list[dict], block_start: int) -> str:
    """Format style runs into a compact string representation for attrs.

    Args:
        style_runs: List of style run dictionaries with absolute positions
        block_start: The start index of the block (unused, kept for compatibility)

    Returns:
        Formatted string like "bold:10-21,italic:15-20,color=red:25-30"
        with absolute document positions
    """
    if not style_runs:
        return ""

    # Consolidate overlapping ranges with the same styles
    consolidated = []

    for run in style_runs:
        # Use absolute document positions (not relative to block)
        abs_start = run["start"]
        abs_end = run["end"]

        for style_name, style_value in run["styles"].items():
            # Format the style entry
            if isinstance(style_value, bool):
                # For boolean styles, just use the name
                style_str = style_name
            else:
                # For valued styles, include the value
                style_str = f"{style_name}={style_value}"

            consolidated.append(f"{style_str}:{abs_start}-{abs_end}")

    return ",".join(consolidated) if consolidated else ""
