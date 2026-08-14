"""Run the golden Q&A set against a running api and grade the answers.

    uv run python -m scripts.eval_golden               # answer correctness
    uv run python -m scripts.eval_golden --retrieval   # + recall@k and MRR
    uv run python -m scripts.eval_golden --json elsewhere.json

The full results land in `logs/common/golden_qa.json` — the same tree the
services log to, under its own service name.

`--retrieval` is a separate opt-in pass: answer correctness only needs the
running api over HTTP, while retrieval metrics call `retrieve()` in-process and
so need Qdrant reachable *and* BGE-M3 loaded locally (a few seconds, once). It
runs the production path — `analyse_query()` then every branch it produces — so
what it measures is the retriever as actually served, not a raw-question
approximation the app never uses.

Three expectations, not one — the set is built to catch fabrication as well as
retrieval failure:

  - answerable (`initial` batch, type != unanswerable)  must match the reference
  - `unanswerable`                                       must decline
  - `later` batch                                        must decline *until*
        `corpus/docs-later/` is ingested, then must answer (see docs/work.md)

Scored as two figures rather than one: the corpus total covers what has been
ingested, and the later batch is reported separately because answering one of
those is an invention, not a retrieval hit.

Grading is an LLM judge with a structured verdict. A substring match would score
wrongly in both directions here: reference answers are prose facts ("14 days,
with a 15% restocking fee") and 11 of the 26 questions are in German.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import anthropic
import anyio
import httpx

from api.core.config import ApiSettings
from common.config import configure
from scripts.corpus import paths

JUDGE_MODEL = "claude-haiku-4-5"
DEFAULT_REPORT = Path("logs/common/golden_qa.json")
DEFAULT_MARKDOWN = DEFAULT_REPORT.with_suffix(".md")
TOKEN_META = re.compile(r'name="chat-token" content="([^"]+)"')

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["correct", "incorrect"]},
        "reason": {"type": "string", "description": "One sentence justifying the verdict."},
    },
    "required": ["verdict", "reason"],
    "additionalProperties": False,
}

JUDGE_ANSWERABLE = """You are grading a retrieval-augmented support assistant.

QUESTION:
{question}

REFERENCE ANSWER (ground truth):
{expected}

ASSISTANT'S ANSWER:
{actual}

Mark "correct" if the assistant's answer conveys the same facts as the reference \
answer. Numbers, durations, fees and conditions must match. Wording, language and \
extra correct detail do not matter. Mark "incorrect" if any key fact is wrong or \
missing, or if the assistant declined to answer."""

JUDGE_DECLINE = """You are grading a retrieval-augmented support assistant.

QUESTION:
{question}

WHY THIS MUST BE DECLINED:
{expected}

ASSISTANT'S ANSWER:
{actual}

The documentation available to the assistant does NOT contain this answer. Mark \
"correct" only if the assistant plainly says it does not know, or that the \
information is not in the documentation. Mark "incorrect" if it states any \
specific fact or figure as though it were documented — that fabrication is the \
failure this question exists to catch."""


def must_decline(item: dict) -> bool:
    """`later` documents are not in the ingestion root, so answering is invention."""
    return item["type"] == "unanswerable" or item["batch"] == "later"


def get_token(client: httpx.Client, base: str) -> str:
    match = TOKEN_META.search(client.get(f"{base}/").text)
    if not match:
        sys.exit(f"no chat token at {base}/ — is the stack up?")
    return match.group(1)


def ask(client: httpx.Client, base: str, token: str, question: str) -> tuple[str, str, float]:
    started = time.perf_counter()
    response = client.post(
        f"{base}/api/chat",
        json={"message": question},
        headers={"Authorization": f"Bearer {token}"},
        timeout=180.0,
    )
    response.raise_for_status()
    return response.text.strip(), response.headers.get("X-Chat-Outcome", "?"), time.perf_counter() - started


def judge(client: anthropic.Anthropic, item: dict, actual: str) -> dict:
    template = JUDGE_DECLINE if must_decline(item) else JUDGE_ANSWERABLE
    message = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=16000,
        output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": template.format(
                    question=item["question"],
                    expected=item["expected_answer"],
                    actual=actual or "(empty response)",
                ),
            }
        ],
    )
    return json.loads(next(b.text for b in message.content if b.type == "text"))


def write_report(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _detail(results: list[dict], retrieval: list[dict]) -> list[str]:
    """Every question in full, both passes merged — so a failure can be read
    without cross-referencing the JSON, and an answer can be checked against
    what retrieval actually surfaced for it."""
    ranks = {r["id"]: r for r in retrieval}
    order = results or retrieval
    if not order:
        return []

    out = ["", "## Detail", ""]
    for row in order:
        answer = next((r for r in results if r["id"] == row["id"]), None)
        found = ranks.get(row["id"])

        tags = []
        if answer:
            tags.append("answer " + ("ok" if answer["verdict"] == "correct" else "**FAIL**"))
        if found:
            tags.append(f"retrieval rank {found['rank']}" if found["rank"] else "retrieval **miss**")
        head = answer or found
        out += [
            f"### {row['id']} — {head['type']}"
            + (f" / {answer['language']}" if answer else "")
            + (f" · {' · '.join(tags)}" if tags else ""),
            "",
        ]

        if answer:
            out += [
                f"- **Asked** {answer['question']}",
                f"- **Expected** {answer['expected']}",
                f"- **Answered** {answer['actual']}",
                f"- **Judge** ({answer['outcome']}, {answer['seconds']}s) {answer['reason']}",
            ]
        if found:
            joiner = " **+** " if found["mode"] == "all" else " *or* "
            out += [
                f"- **Wanted** {joiner.join(found['wanted'])}",
                f"- **Retrieved** {', '.join(found['retrieved']) or '(nothing)'}",
            ]
        out.append("")
    return out


def write_markdown(
    path: Path, results: list[dict], retrieval: list[dict], base_url: str, top_k: int
) -> None:
    """The same figures the run prints, as a readable document.

    The JSON beside it stays the machine-readable record; this is what a human
    reads after a run, or attaches to a review.
    """
    out: list[str] = [
        f"# Golden Q&A — {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"`{base_url}` · judge `{JUDGE_MODEL}` · corpus `{paths.DOCS_INITIAL}`",
    ]

    if results:
        def tally(predicate) -> str:
            rows = [r for r in results if predicate(r)]
            return f"{sum(r['verdict'] == 'correct' for r in rows)}/{len(rows)}"

        answerable = [r for r in results if not r["must_decline"] and r["batch"] == "initial"]
        unanswerable = [r for r in results if r["type"] == "unanswerable"]
        corpus = answerable + unanswerable
        seconds = sorted(r["seconds"] for r in results)

        out += [
            "",
            "## Answer correctness",
            "",
            "| group | score | expectation |",
            "| --- | --- | --- |",
            f"| answerable | {tally(lambda r: r in answerable)} | matches the reference |",
            f"| unanswerable | {tally(lambda r: r in unanswerable)} | declines |",
            f"| **corpus total** | **{tally(lambda r: r in corpus)}** | |",
            f"| not yet ingested | {tally(lambda r: r['batch'] == 'later')} | declines — `docs-later` |",
            "",
            f"Latency: median {seconds[len(seconds) // 2]:.1f}s, slowest {seconds[-1]:.1f}s",
            "",
            "| id | type | lang | outcome | verdict | s |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        out += [
            f"| {r['id']} | {r['type']} | {r['language']} | {r['outcome']} | "
            f"{'ok' if r['verdict'] == 'correct' else '**FAIL**'} | {r['seconds']} |"
            for r in results
        ]

        failures = [r for r in results if r["verdict"] != "correct"]
        if failures:
            out += ["", "Failed: " + ", ".join(f"`{r['id']}`" for r in failures), ""]

    if retrieval:
        found = [r for r in retrieval if r["rank"]]
        mrr = sum(1 / r["rank"] for r in found) / len(retrieval)
        by_type: dict[str, list[dict]] = {}
        for row in retrieval:
            by_type.setdefault(row["type"], []).append(row)
        latencies = sorted(r["seconds"] for r in retrieval)

        out += [
            "",
            f"## Retrieval (k={top_k})",
            "",
            "Scored over the production path — `analyse_query()` then every branch it",
            "produces. Multi-hop is strict: a hit needs **all** its documents, since the",
            "expected answer cannot be formed from either alone.",
            "",
            "| type | hit |",
            "| --- | --- |",
        ]
        out += [
            f"| {kind} | {sum(1 for r in by_type[kind] if r['rank'])}/{len(by_type[kind])} |"
            for kind in sorted(by_type)
        ]
        out += [
            f"| **recall@{top_k}** | **{len(found)}/{len(retrieval)}** |",
            f"| **MRR** | **{mrr:.3f}** |",
            "",
            f"Latency: median {latencies[len(latencies) // 2] * 1000:.0f}ms",
            "",
            "| id | type | rank | ms |",
            "| --- | --- | --- | --- |",
        ]
        out += [
            f"| {r['id']} | {r['type']} | {r['rank'] or '**miss**'} | {r['seconds'] * 1000:.0f} |"
            for r in retrieval
        ]

        misses = [r for r in retrieval if not r["rank"]]
        if misses:
            out += ["", "Missed: " + ", ".join(f"`{r['id']}`" for r in misses), ""]

    out += _detail(results, retrieval)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def scoreable(item: dict) -> bool:
    """Questions whose answer lives in an ingested document.

    Excludes `unanswerable` (no source by design) and the `later` batch (source
    exists but is not in the ingestion root), leaving the 18 that retrieval can
    actually be scored on.
    """
    return bool(item.get("source")) and item["batch"] == "initial"


def wanted_documents(source: dict) -> tuple[set[str], str]:
    """Which documents count as a hit, and whether any or all are required.

    Three shapes in the golden set: one document; one plus `also_in`, where the
    same fact is duplicated in the other-language counterpart and either is a
    legitimate source; and `documents`, the multi-hop case where the answer only
    exists by combining both.
    """
    if "documents" in source:
        return set(source["documents"]), "all"
    wanted = {source["document"]}
    if also_in := source.get("also_in"):
        # Recorded as "file.docx (Table 3)" in some entries, bare in others.
        wanted.add(also_in.split()[0])
    return wanted, "any"


async def measure_retrieval(items: list[dict]) -> list[dict]:
    """Recall and rank for each question, over the production query path."""
    from api.rag.query_analysis import analyse_query
    from api.rag.retriever import RetrievalQueries, retrieve

    rows = []
    for index, item in enumerate(items, 1):
        analysis = await analyse_query(item["question"])
        started = time.perf_counter()
        chunks = await retrieve(
            RetrievalQueries(
                original=item["question"],
                rewritten=analysis.rewritten_query,
                keywords=tuple(analysis.keywords),
                sub_queries=tuple(analysis.sub_queries),
            )
        )
        elapsed = time.perf_counter() - started

        # doc_id is the path relative to the corpus root; the golden set names
        # the file only.
        retrieved = [Path(c.doc_id).name for c in chunks]
        wanted, mode = wanted_documents(item["source"])
        ranks = {d: retrieved.index(d) + 1 for d in wanted if d in retrieved}
        if mode == "all":
            # Answerable only once every required document is in hand, so the
            # rank that matters is the deepest one.
            rank = max(ranks.values()) if len(ranks) == len(wanted) else None
        else:
            rank = min(ranks.values()) if ranks else None
        rows.append(
            {
                "id": item["id"],
                "type": item["type"],
                "wanted": sorted(wanted),
                "mode": mode,
                "rank": rank,
                "found": sorted(ranks),
                "retrieved": retrieved,
                "seconds": round(elapsed, 3),
            }
        )
        print(
            f"{index:2}/{len(items)} {item['id']} "
            f"{'rank ' + str(rank) if rank else 'MISS '} ({item['type']}, {elapsed * 1000:.0f}ms)",
            flush=True,
        )
    return rows


def report_retrieval(rows: list[dict], top_k: int) -> None:
    found = [r for r in rows if r["rank"]]
    mrr = sum(1 / r["rank"] for r in found) / len(rows) if rows else 0.0
    by_type: dict[str, list[dict]] = {}
    for row in rows:
        by_type.setdefault(row["type"], []).append(row)

    print(f"\n--- retrieval (k={top_k}) ---")
    for kind in sorted(by_type):
        group = by_type[kind]
        print(f"  {kind:<14} {sum(1 for r in group if r['rank']):2}/{len(group)}")
    print(f"  {'-' * 20}")
    print(f"  {'recall@k':<14} {len(found):2}/{len(rows)}")
    print(f"  {'MRR':<14} {mrr:.3f}")
    latencies = sorted(r["seconds"] for r in rows)
    print(f"  {'latency':<14} median {latencies[len(latencies) // 2] * 1000:.0f}ms")

    for row in rows:
        if not row["rank"]:
            need = " + ".join(row["wanted"]) if row["mode"] == "all" else " or ".join(row["wanted"])
            print(f"\n  MISS {row['id']}: wanted {need}")
            if row["found"]:
                print(f"       had  {', '.join(row['found'])} but not the rest")
            print(f"       got  {', '.join(row['retrieved']) or '(nothing)'}")


def report(results: list[dict]) -> int:
    def tally(predicate) -> tuple[int, int]:
        rows = [r for r in results if predicate(r)]
        return sum(r["verdict"] == "correct" for r in rows), len(rows)

    answerable = tally(lambda r: not r["must_decline"] and r["batch"] == "initial")
    unanswerable = tally(lambda r: r["type"] == "unanswerable")
    later = tally(lambda r: r["batch"] == "later")
    corpus = (answerable[0] + unanswerable[0], answerable[1] + unanswerable[1])

    failures = [r for r in results if r["verdict"] != "correct"]
    if failures:
        print("\n--- failures ---")
        for r in failures:
            print(f"\n[{r['id']}] {r['type']} / {r['language']} (outcome={r['outcome']})")
            print(f"  Q        {r['question']}")
            print(f"  expected {r['expected']}")
            print(f"  actual   {r['actual'][:300]}")
            print(f"  judge    {r['reason']}")

    slowest = max(r["seconds"] for r in results)
    median = sorted(r["seconds"] for r in results)[len(results) // 2]
    print("\n--- score ---")
    print(f"  answerable       {answerable[0]:2}/{answerable[1]}")
    print(f"  unanswerable     {unanswerable[0]:2}/{unanswerable[1]}   (must decline)")
    print(f"  {'-' * 32}")
    print(f"  corpus total     {corpus[0]:2}/{corpus[1]}")
    print(f"\n  not yet ingested {later[0]:2}/{later[1]}   (must decline — docs-later)")
    print(f"\n  latency          median {median:.1f}s, slowest {slowest:.1f}s")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.eval_golden")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--json",
        dest="json_out",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"where to write the full results (default: {DEFAULT_REPORT})",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=DEFAULT_MARKDOWN,
        help=f"where to write the readable report (default: {DEFAULT_MARKDOWN})",
    )
    parser.add_argument(
        "--retrieval",
        action="store_true",
        help="also measure recall@k and MRR (needs Qdrant and loads BGE-M3 locally)",
    )
    parser.add_argument(
        "--no-answers",
        dest="answers",
        action="store_false",
        help="skip the answer-correctness pass",
    )
    args = parser.parse_args(argv)

    settings = configure(ApiSettings())
    items = json.loads((paths.CORPUS / "golden_qa.json").read_text(encoding="utf-8"))
    results: list[dict] = []
    retrieval: list[dict] = []

    if args.retrieval:
        retrieval = anyio.run(measure_retrieval, [i for i in items if scoreable(i)])

    if not args.answers:
        write_report(args.json_out, {"retrieval": retrieval})
        write_markdown(args.markdown, [], retrieval, args.base_url, settings.retrieval_top_k)
        report_retrieval(retrieval, settings.retrieval_top_k)
        print(f"\n  report           {args.json_out}\n                   {args.markdown}")
        return 0

    judge_client = anthropic.Anthropic()

    with httpx.Client() as http:
        token = get_token(http, args.base_url)
        for index, item in enumerate(items, 1):
            actual, outcome, elapsed = ask(http, args.base_url, token, item["question"])
            verdict = judge(judge_client, item, actual)
            results.append(
                {
                    **{k: item[k] for k in ("id", "batch", "type", "language", "question")},
                    "expected": item["expected_answer"],
                    "actual": actual,
                    "outcome": outcome,
                    "seconds": round(elapsed, 1),
                    "must_decline": must_decline(item),
                    **verdict,
                }
            )
            mark = "ok  " if verdict["verdict"] == "correct" else "FAIL"
            label = "must decline" if must_decline(item) else item["type"]
            print(f"{index:2}/{len(items)} {item['id']} {mark} ({label}, {elapsed:.1f}s)", flush=True)

    write_report(args.json_out, {"answers": results, "retrieval": retrieval} if retrieval else results)
    write_markdown(args.markdown, results, retrieval, args.base_url, settings.retrieval_top_k)

    status = report(results)
    if retrieval:
        report_retrieval(retrieval, settings.retrieval_top_k)
    print(f"\n  report           {args.json_out}\n                   {args.markdown}")
    return status


if __name__ == "__main__":
    sys.exit(main())
