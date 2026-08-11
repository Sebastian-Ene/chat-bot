"""Content-as-data pipeline: Markdown in, PDF/DOCX/HTML out.

Bulk documents are authored as Markdown under `scripts/corpus/content/` and
rendered by this module into `corpus/docs-initial/bulk/`. Content stays reviewable and editable; layout lives
here.

Supported syntax — deliberately a small subset:

    ---                     front matter: title, lang, format, layout
    # / ## / ###            headings
    - item                  bullet list
    | a | b |               pipe table (preceded by `{.unruled}` for a borderless one)
    ![caption](path)        figure; empty caption renders uncaptioned
    ::: two-column          two-column block, closed by :::

`layout` picks one of several visual treatments, so the bulk of the corpus does
not share a single layout fingerprint.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
TABLE_DIVIDER = re.compile(r"^\|[\s:|-]+\|\s*$")
FIGURE = re.compile(r"^!\[(.*)\]\((.+)\)\s*$")


@dataclass
class Block:
    kind: str  # heading | para | bullets | table | figure | columns
    text: str = ""
    level: int = 1
    items: list[str] = field(default_factory=list)
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    ruled: bool = True
    caption: str | None = None
    blocks: list["Block"] = field(default_factory=list)


@dataclass
class Doc:
    meta: dict[str, str]
    blocks: list[Block]

    @property
    def title(self) -> str:
        return self.meta.get("title", "Untitled")

    @property
    def lang(self) -> str:
        return self.meta.get("lang", "en")

    @property
    def fmt(self) -> str:
        return self.meta.get("format", "html")

    @property
    def layout(self) -> str:
        return self.meta.get("layout", "report")

    @property
    def batch(self) -> str:
        """`initial` renders into the bulk set, `later` into the second batch."""
        return self.meta.get("batch", "initial")


def _split_front_matter(text: str) -> tuple[dict[str, str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, lines[end + 1 :]


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in TABLE_ROW.match(line).group(1).split("|")]


def _parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    index = 0
    unruled_next = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped == "{.unruled}":
            unruled_next = True
            index += 1
            continue

        if stripped.startswith("::: two-column"):
            index += 1
            nested: list[str] = []
            while index < len(lines) and lines[index].strip() != ":::":
                nested.append(lines[index])
                index += 1
            index += 1  # closing :::
            blocks.append(Block(kind="columns", blocks=_parse_blocks(nested)))
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append(Block(kind="heading", level=level, text=stripped[level:].strip()))
            index += 1
            continue

        figure = FIGURE.match(stripped)
        if figure:
            caption = figure.group(1).strip()
            blocks.append(
                Block(kind="figure", text=figure.group(2), caption=caption or None)
            )
            index += 1
            continue

        if TABLE_ROW.match(stripped):
            header = _cells(stripped)
            index += 1
            if index < len(lines) and TABLE_DIVIDER.match(lines[index].strip()):
                index += 1
            rows = []
            while index < len(lines) and TABLE_ROW.match(lines[index].strip()):
                rows.append(_cells(lines[index].strip()))
                index += 1
            blocks.append(Block(kind="table", header=header, rows=rows, ruled=not unruled_next))
            unruled_next = False
            continue

        if stripped.startswith("- "):
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(lines[index].strip()[2:])
                index += 1
            blocks.append(Block(kind="bullets", items=items))
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not _starts_block(lines[index]):
            paragraph.append(lines[index].strip())
            index += 1
        blocks.append(Block(kind="para", text=" ".join(paragraph)))

    return blocks


def _starts_block(line: str) -> bool:
    stripped = line.strip()
    return bool(
        stripped.startswith(("#", "- ", ":::", "{.unruled}"))
        or TABLE_ROW.match(stripped)
        or FIGURE.match(stripped)
    )


def parse(path: Path) -> Doc:
    meta, lines = _split_front_matter(path.read_text(encoding="utf-8"))
    return Doc(meta=meta, blocks=_parse_blocks(lines))
