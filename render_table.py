#!/usr/bin/env python3
"""
Regenerate the comparison table in README.md from tools.yaml, or shortlist tools.

    python render_table.py                      # print the table to stdout
    python render_table.py --write              # rewrite the block between the markers
    python render_table.py --check              # exit 1 if README is out of date
    python render_table.py --need ai-mode,claude --max 100
                                                # shortlist tools that list every
                                                # engine you need, under a price cap

The featured pick leads. Other rows are grouped by how the entry plan gets
Google AI Mode data, then sorted by price, so a tool that bills AI Mode as an add on never sits beside one that
bundles it without the difference showing. The engine count is computed from
the engine list, never stored.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

START = "<!-- TABLE:START -->"
END = "<!-- TABLE:END -->"

ACCESS_ORDER = ["included", "addon", "product", "unclear", "absent"]
ACCESS_LABELS = {
    "included": "In base plan",
    "addon": "Paid add on",
    "product": "Separate product",
    "unclear": "Unclear",
    "absent": "Not listed",
}

ENGINE_LABELS = {
    "ai-mode": "AI Mode",
    "ai-overviews": "AI Overviews",
    "google-ai": "Google AI (unspecified)",
    "ai-shopping": "AI Shopping",
    "chatgpt": "ChatGPT",
    "perplexity": "Perplexity",
    "gemini": "Gemini",
    "claude": "Claude",
    "copilot": "Copilot",
    "grok": "Grok",
    "mistral": "Mistral",
    "deepseek": "DeepSeek",
}

SYMBOLS = {"USD": "$", "EUR": "€"}


def linkify(tool: dict) -> str:
    return f"[{tool['name']}]({tool['url']})" if tool.get("url") else tool["name"]


def price(tool: dict) -> str:
    value = tool.get("entry_price")
    if value is None:
        return "Sales only"
    amount = f"{value:,.2f}".replace(".00", "")
    return f"{SYMBOLS.get(tool.get('currency', 'USD'), '')}{amount}/mo"


def engines(tool: dict) -> str:
    listed = tool.get("engines", [])
    unknown = [e for e in listed if e not in ENGINE_LABELS]
    if unknown:
        raise SystemExit(f"{tool['name']}: unknown engine key(s) {unknown}")
    return f"{len(listed)}: " + ", ".join(ENGINE_LABELS[e] for e in listed)


def access(tool: dict) -> str:
    key = tool.get("ai_mode")
    if key not in ACCESS_LABELS:
        raise SystemExit(f"{tool['name']}: ai_mode must be one of {ACCESS_ORDER}")
    return ACCESS_LABELS[key]


def ordered(tools: list[dict]) -> list[dict]:
    return sorted(
        tools,
        key=lambda t: (
            not t.get("featured", False),
            ACCESS_ORDER.index(t["ai_mode"]),
            t.get("entry_price") or 0,
            t["name"],
        ),
    )


def build_table(tools: list[dict]) -> str:
    columns = [
        ("Tool", linkify),
        ("AI Mode access", access),
        ("Engines listed", engines),
        ("Entry price", price),
        ("Best for", lambda t: t.get("best_for", "")),
    ]
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    rows = ["| " + " | ".join(fn(t) for _, fn in columns) + " |" for t in ordered(tools)]
    return "\n".join([header, divider, *rows])


def shortlist(tools: list[dict], need: list[str], cap: float | None) -> str:
    hits = [
        t for t in ordered(tools)
        if all(e in t.get("engines", []) for e in need)
        and (cap is None or (t.get("entry_price") or 0) <= cap)
    ]
    if not hits:
        return "No tool in tools.yaml lists all of: " + ", ".join(need)
    lines = [f"{len(hits)} tool(s) list {', '.join(need) or 'any engine'}"
             + (f" at or under {cap:g}/mo (native currency)" if cap is not None else "") + ":"]
    for t in hits:
        note = f"  ({t['addon_note']})" if t.get("addon_note") else ""
        lines.append(f"  {t['name']:<30} {access(t):<17} {price(t):<12}{note}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the table into README.md")
    ap.add_argument("--check", action="store_true", help="fail if README.md is stale")
    ap.add_argument("--need", default="", help="comma separated engine keys, e.g. ai-mode,claude")
    ap.add_argument("--max", type=float, default=None, help="price cap per month, native currency")
    ap.add_argument("--data", type=Path, default=Path("tools.yaml"))
    ap.add_argument("--readme", type=Path, default=Path("README.md"))
    args = ap.parse_args()

    tools = yaml.safe_load(args.data.read_text(encoding="utf-8"))["tools"]

    if args.need or args.max is not None:
        need = [e.strip() for e in args.need.split(",") if e.strip()]
        bad = [e for e in need if e not in ENGINE_LABELS]
        if bad:
            raise SystemExit(f"Unknown engine key(s) {bad}. Valid: {', '.join(ENGINE_LABELS)}")
        print(shortlist(tools, need, args.max))
        return 0

    table = build_table(tools)
    if not (args.write or args.check):
        print(table)
        return 0

    text = args.readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README.md is missing the TABLE markers.")
    before, rest = text.split(START, 1)
    current, after = rest.split(END, 1)

    if args.check:
        if current.strip("\n") != table:
            print("README table is out of date. Run: python render_table.py --write", file=sys.stderr)
            return 1
        print("README table matches tools.yaml.")
        return 0

    args.readme.write_text(f"{before}{START}\n{table}\n{END}{after}", encoding="utf-8")
    print(f"Updated table in {args.readme} ({len(tools)} tools).")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
