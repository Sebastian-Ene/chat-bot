#!/usr/bin/env python3
"""Export Claude Code chat transcript events since the last commit into chat-logs/.

Run by the pre-commit git hook (see .githooks/pre-commit). Reads the raw
session JSONL files that Claude Code writes under ~/.claude/projects/<slug>/,
keeps everything newer than the previous commit's timestamp, and writes a
single markdown file per commit with the full raw detail (text, thinking,
tool calls, tool results).
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "chat-logs"

Event = dict[str, Any]


def project_slug(path: Path) -> str:
    return str(path).replace("/", "-")


def last_commit_time() -> str | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip()


def load_events(project_dir: Path, since: str | None) -> list[Event]:
    events: list[Event] = []
    if not project_dir.is_dir():
        return events
    for jsonl_file in project_dir.glob("*.jsonl"):
        with jsonl_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = entry.get("timestamp")
                if not ts:
                    continue
                if since and ts <= since:
                    continue
                entry["_source_file"] = jsonl_file.name
                events.append(entry)
    events.sort(key=lambda e: e["timestamp"])
    return events


def format_content(content: str | list[dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        btype = block.get("type")
        if btype == "text":
            parts.append(block.get("text", ""))
        elif btype == "thinking":
            parts.append(f"_(thinking)_\n{block.get('thinking', '')}")
        elif btype == "tool_use":
            parts.append(
                f"**Tool call: `{block.get('name')}`**\n```json\n"
                f"{json.dumps(block.get('input', {}), indent=2)}\n```"
            )
        elif btype == "tool_result":
            inner = block.get("content", "")
            inner_text = inner if isinstance(inner, str) else json.dumps(inner, indent=2)
            parts.append(f"**Tool result**\n```\n{inner_text}\n```")
        else:
            parts.append(f"```json\n{json.dumps(block, indent=2)}\n```")
    return "\n\n".join(parts)


def render(events: list[Event]) -> str:
    lines: list[str] = []
    for entry in events:
        ts = entry.get("timestamp", "")
        etype = entry.get("type", "?")
        message = entry.get("message")
        lines.append(f"## [{ts}] {etype}")
        if message:
            role = message.get("role", etype)
            lines.append(f"**{role}**\n")
            lines.append(format_content(message.get("content", "")))
        else:
            lines.append(f"```json\n{json.dumps(entry, indent=2)}\n```")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    slug = project_slug(REPO_ROOT)
    project_dir = Path.home() / ".claude" / "projects" / slug
    since = last_commit_time()
    events = load_events(project_dir, since)
    if not events:
        return

    LOG_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_path = LOG_DIR / f"{now}.md"
    header = (
        f"# Claude Code chat log\n\n"
        f"Exported: {now}\n"
        f"Range: {since or 'beginning'} .. {now}\n\n"
    )
    out_path.write_text(header + render(events))

    subprocess.run(["git", "add", str(out_path)], cwd=REPO_ROOT)


if __name__ == "__main__":
    main()
