"""Shared ReportLab scaffolding for the PDF documents.

Provides the two things the corpus needs and a plain PDF writer would not give:
a **two-column** page template, and tables that **split across a page break**
with their header repeated (requirements.md §4).
"""
from collections.abc import Callable
from pathlib import Path

from reportlab import rl_config

# Fixed dates and no random document IDs, so regenerating produces byte-identical
# PDFs. Content hashes then stay stable for the incremental-ingestion manifest.
rl_config.invariant = 1

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    Frame,
    Image,
    LongTable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

MARGIN = 20 * mm
GUTTER = 8 * mm


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AuroraTitle", parent=base["Title"], fontSize=22, leading=26, spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "AuroraSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#555555"),
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "AuroraH1", parent=base["Heading1"], fontSize=15, leading=19, spaceBefore=14
        ),
        "h2": ParagraphStyle(
            "AuroraH2", parent=base["Heading2"], fontSize=12.5, leading=16, spaceBefore=10
        ),
        "body": ParagraphStyle(
            "AuroraBody",
            parent=base["BodyText"],
            fontSize=10,
            leading=14.5,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "AuroraBullet", parent=base["BodyText"], fontSize=10, leading=14.5, leftIndent=10
        ),
        "caption": ParagraphStyle(
            "AuroraCaption",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#444444"),
            spaceBefore=4,
            spaceAfter=12,
        ),
        "note": ParagraphStyle(
            "AuroraNote",
            parent=base["BodyText"],
            fontSize=9.5,
            leading=13,
            leftIndent=8,
            textColor=colors.HexColor("#333333"),
            backColor=colors.HexColor("#f4f1ea"),
            borderPadding=6,
            spaceAfter=10,
        ),
    }


def _wrapped(data: list[list], bold_header: bool) -> list[list]:
    """Cells as Paragraphs so long text wraps.

    Plain strings do not wrap in ReportLab — they overflow the column and
    overprint the neighbouring cell.
    """
    cell = ParagraphStyle("Cell", fontName="Helvetica", fontSize=8.5, leading=10.5)
    head = ParagraphStyle(
        "CellHead", fontName="Helvetica-Bold" if bold_header else "Helvetica", fontSize=8.5, leading=10.5
    )
    return [
        [Paragraph(str(text), head if index == 0 else cell) for text in row]
        for index, row in enumerate(data)
    ]


def ruled_table(data: list[list], widths: list[float], repeat_header: bool = True) -> Table:
    """Bordered table. `LongTable` so it splits across pages, header repeated."""
    table = LongTable(
        _wrapped(data, bold_header=True), colWidths=widths, repeatRows=1 if repeat_header else 0
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e3d8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def unruled_table(data: list[list], widths: list[float]) -> Table:
    """No borders at all — alignment is the only cue that it is a table.

    Deliberately hard: a layout parser has to infer the structure rather than
    read ruling lines.
    """
    table = Table(_wrapped(data, bold_header=True), colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def figure(path: Path, width: float, caption: str | None, style: ParagraphStyle) -> list:
    """A figure, optionally captioned.

    Passing `caption=None` is the point of several documents: Docling finds no
    caption, so the generated-description path has to produce one.
    """
    image = Image(str(path))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth = width
    image.drawHeight = width * ratio
    flowables: list = [Spacer(1, 6), image]
    if caption is not None:
        flowables.append(Paragraph(caption, style))
    else:
        flowables.append(Spacer(1, 12))
    return flowables


def build_pdf(path: Path, title: str, author: str, story_fn: Callable[[dict, float], list]) -> Path:
    """One- and two-column page templates; the story switches with
    `NextPageTemplate` + `PageBreak`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = A4
    usable = page_width - 2 * MARGIN
    column = (usable - GUTTER) / 2

    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=title,
        author=author,
    )
    one = Frame(MARGIN, MARGIN, usable, page_height - 2 * MARGIN, id="single")
    left = Frame(MARGIN, MARGIN, column, page_height - 2 * MARGIN, id="left")
    right = Frame(
        MARGIN + column + GUTTER, MARGIN, column, page_height - 2 * MARGIN, id="right"
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="OneCol", frames=[one]),
            PageTemplate(id="TwoCol", frames=[left, right]),
        ]
    )
    doc.build(story_fn(styles(), usable))
    return path
