#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "paper_final.md"
DST = ROOT / "paper" / "paper_final.html"

STYLE = """<style>
.ue-paper{width:100%;max-width:none;margin:0;padding:20px;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Arial,sans-serif;line-height:1.6;color:#111}
.ue-paper h1{font-size:1.8rem}
.ue-paper h2{font-size:1.4rem;margin-top:2rem;border-bottom:1px solid #eee;padding-bottom:4px}
.ue-paper h3{font-size:1.15rem;margin-top:1.5rem}
.ue-paper h4{font-size:1rem}
.ue-paper p,.ue-paper li{font-size:15px}
.ue-paper table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.9rem}
.ue-paper th,.ue-paper td{border:1px solid #ddd;padding:7px 10px;vertical-align:top}
.ue-paper th{background:#f5f5f5}
.ue-paper blockquote{border-left:4px solid #ddd;margin:1rem 0;padding:8px 14px;background:#fafafa}
.ue-paper code{background:#f4f4f4;padding:1px 4px;border-radius:4px;font-family:Consolas,Monaco,monospace;font-size:.92em}
.ue-paper pre{background:#f8f8f8;padding:12px;overflow-x:auto;border:1px solid #e5e5e5;border-radius:6px}
.ue-paper img{max-width:100%;height:auto;display:block;margin:0 auto}
.ue-figure{margin:1.2rem 0}
.ue-figcaption{font-size:.92rem;color:#444;text-align:center;margin-top:.5rem}
.ue-paper .table-wrap{overflow-x:auto;width:100%}
.math-block{margin:1rem 0;overflow-x:auto}
</style>
"""

MATHJAX = """<script>
window.MathJax = {
  tex: {
        inlineMath: [['\\\\(', '\\\\)']],
        displayMath: [['\\\\[', '\\\\]']],
    processEscapes: true
  },
  options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
};
</script>
<script defer src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js\"></script>
"""


def extract_math(md_text: str):
    blocks: list[str] = []
    inlines: list[str] = []

    def repl_block_dollars(m: re.Match[str]) -> str:
        idx = len(blocks)
        blocks.append(m.group(1).strip())
        return f"@@MATHBLOCK_{idx}@@"

    def repl_block_brackets(m: re.Match[str]) -> str:
        idx = len(blocks)
        blocks.append(m.group(1).strip())
        return f"@@MATHBLOCK_{idx}@@"

    # Display math first
    text = re.sub(r"\$\$(.*?)\$\$", repl_block_dollars, md_text, flags=re.DOTALL)
    text = re.sub(r"\\\[(.*?)\\\]", repl_block_brackets, text, flags=re.DOTALL)

    def repl_inline_paren(m: re.Match[str]) -> str:
        idx = len(inlines)
        inlines.append(m.group(1).strip())
        return f"@@MATHINLINE_{idx}@@"

    def repl_inline_dollar(m: re.Match[str]) -> str:
        idx = len(inlines)
        inlines.append(m.group(1).strip())
        return f"@@MATHINLINE_{idx}@@"

    text = re.sub(r"\\\((.*?)\\\)", repl_inline_paren, text)
    text = re.sub(r"(?<!\\)\$(?!\$)([^\n$]+?)(?<!\\)\$", repl_inline_dollar, text)

    return text, blocks, inlines


def restore_math(html: str, blocks: list[str], inlines: list[str]) -> str:
    for i, expr in enumerate(blocks):
        html = html.replace(
            f"@@MATHBLOCK_{i}@@",
            f"<div class=\"math-block\">\\[{expr}\\]</div>",
        )
    for i, expr in enumerate(inlines):
        html = html.replace(
            f"@@MATHINLINE_{i}@@",
            f"<span class=\"math-inline\">\\({expr}\\)</span>",
        )
    html = re.sub(r"<p>\s*(<div class=\"math-block\">[\s\S]*?</div>)\s*</p>", r"\1", html)
    return html


def main() -> None:
    md_text = SRC.read_text(encoding="utf-8")
    protected, blocks, inlines = extract_math(md_text)

    body = markdown.markdown(
        protected,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
            "toc",
        ],
    )
    body = restore_math(body, blocks, inlines)

    out = f"{STYLE}\n{MATHJAX}\n<div class=\"ue-paper\">\n{body}\n</div>\n"
    DST.write_text(out, encoding="utf-8")
    print(f"Wrote: {DST}")
    print(f"Display blocks: {len(blocks)} | Inline math: {len(inlines)}")


if __name__ == "__main__":
    main()
