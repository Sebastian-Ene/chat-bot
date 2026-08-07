#!/usr/bin/env python3
"""Export Claude Code chat transcript events since the last commit into chat-logs/.

Run by the pre-commit git hook (see .githooks/pre-commit). Reads the raw
session JSONL files that Claude Code writes under ~/.claude/projects/<slug>/,
keeps everything newer than the previous commit's timestamp, and writes a
single markdown file per commit. Pure session bookkeeping (mode changes,
snapshots, tool-listing deltas) is dropped; user/assistant text renders as a
readable transcript, and tool calls/results are kept in full but folded into
collapsible <details> blocks so they don't bury the conversation.
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


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def last_commit_time() -> datetime | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return parse_iso(result.stdout.strip())


def load_events(project_dir: Path, since: datetime | None) -> list[Event]:
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
                if not ts or (since and parse_iso(ts) <= since):
                    continue
                entry["_source_file"] = jsonl_file.name
                events.append(entry)
    events.sort(key=lambda e: e["timestamp"])
    return events


def truncate(text: str, limit: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def summarize_tool_use(name: str, tool_input: dict[str, Any]) -> str:
    for key in ("command", "file_path", "pattern", "query", "description", "prompt"):
        if key in tool_input:
            return f"tool_use: {name} — {truncate(str(tool_input[key]))}"
    return f"tool_use: {name}"


def collect_tool_results(events: list[Event]) -> dict[str, Any]:
    """Map tool_use_id -> raw result content, so results can render under the
    assistant's tool_use instead of the user turn the API delivers them in."""
    results: dict[str, Any] = {}
    for entry in events:
        content = (entry.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") == "tool_result" and block.get("tool_use_id"):
                results[block["tool_use_id"]] = block.get("content", "")
    return results


def format_content(content: str | list[dict[str, Any]], tool_results: dict[str, Any]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        btype = block.get("type")
        if btype == "text":
            parts.append(block.get("text", ""))
        elif btype == "thinking":
            continue  # skip assistant thinking blocks
        elif btype == "tool_use":
            summary = summarize_tool_use(block.get("name", ""), block.get("input", {}))
            detail = f"<details><summary>{summary}</summary>\n\n```json\n{json.dumps(block.get('input', {}), indent=2)}\n```"
            result = tool_results.get(block.get("id"))
            if result is not None:
                result_text = result if isinstance(result, str) else json.dumps(result, indent=2)
                detail += f"\n\n**Result**\n```\n{result_text}\n```"
            parts.append(detail + "\n</details>")
        elif btype == "tool_result":
            continue  # rendered inline with its tool_use above, not as a user turn
        else:
            parts.append(f"```json\n{json.dumps(block, indent=2)}\n```")
    return "\n\n".join(parts)


def render(events: list[Event]) -> str:
    tool_results = collect_tool_results(events)

    # (role, time_label, body) per non-empty turn; consecutive turns with the
    # same role (e.g. a run of assistant tool calls) collapse into one section.
    sections: list[list[str]] = []
    for entry in events:
        message = entry.get("message")
        if not message:
            continue  # drop pure session bookkeeping (mode, snapshots, deltas)
        body = format_content(message.get("content", ""), tool_results)
        if not body.strip():
            continue  # e.g. a user turn that was only a tool_result, or thinking-only assistant turn
        ts = entry.get("timestamp", "")
        time_label = ts.split("T")[1].rstrip("Z")[:5] if "T" in ts else ts
        role = message.get("role", entry.get("type", "?"))
        if sections and sections[-1][0] == role:
            sections[-1][2] += "\n\n" + body
        else:
            sections.append([role, time_label, body])

    lines: list[str] = []
    for role, time_label, body in sections:
        lines.append(f"## {role} — {time_label}")
        lines.append("")
        lines.append(body)
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
    )
    out_path.write_text(header + render(events))

    subprocess.run(["git", "add", str(out_path)], cwd=REPO_ROOT)


if __name__ == "__main__":
    main()
