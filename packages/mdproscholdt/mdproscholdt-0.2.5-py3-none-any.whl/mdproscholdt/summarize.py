from __future__ import annotations
from typing import List, Dict
from .scanner import ScannedFile
from pathlib import Path
import ast
import io
import tokenize

def build_project_context(files: List[ScannedFile]) -> str:
    tree_lines = [f"- {f.path} ({f.size} bytes){' [sampled]' if f.sampled else ''}" for f in files]

    index_lines = ["| File | Bytes | SHA1 |", "|---|---:|---|"]
    for f in files:
        index_lines.append(f"| {f.path} | {f.size} | `{f.sha1[:10]}` |")

    blocks = []
    for f in files:
        blocks.append("\n### `{}`\n\n```text\n{}\n```\n".format(f.path, f.content))

    return (
        "# Project Snapshot\n\n"
        "## Tree\n" + "\n".join(tree_lines) + "\n\n"
        "## Index\n" + "\n".join(index_lines) + "\n\n"
        "## File Samples\n" + "\n".join(blocks) + "\n"
    )

def _extract_python_docstrings_and_comments(text: str) -> Dict[str, list]:
    result = {"module": [], "classes": [], "functions": [], "comments": []}
    try:
        mod = ast.parse(text)
    except Exception:
        return result

    mdoc = ast.get_docstring(mod)
    if mdoc:
        result["module"].append(mdoc)

    for node in ast.walk(mod):
        if isinstance(node, ast.ClassDef):
            cdoc = ast.get_docstring(node)
            if cdoc:
                result["classes"].append("class {}:\n{}".format(node.name, cdoc))
        elif isinstance(node, ast.FunctionDef):
            fdoc = ast.get_docstring(node)
            if fdoc:
                result["functions"].append("def {}(...):\n{}".format(node.name, fdoc))

    try:
        buf = io.StringIO(text)
        tokens = tokenize.generate_tokens(buf.readline)
        collected = []
        for tok in tokens:
            if tok.type == tokenize.COMMENT and tok.start[0] <= 80:
                c = tok.string.lstrip("# ").rstrip()
                if c:
                    collected.append(c)
        if collected:
            result["comments"] = collected
    except Exception:
        pass

    return result

def build_static_markdown(cfg, files: List[ScannedFile], snapshot_md: str) -> str:
    lines = []
    lines.append("# Project Documentation (Static)")
    lines.append("")
    lines.append("Este documento foi gerado sem IA com base na análise do projeto.")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- Objetivo: {cfg.objective}")
    lines.append(f"- Estilo: {cfg.style}")
    lines.append(f"- Público: {cfg.audience}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(snapshot_md)

    py_files = [f for f in files if f.path.endswith(".py")]
    if py_files:
        lines.append("## Python Docstrings and Comments")
        for f in py_files:
            lines.append(f"### {f.path}")
            extracted = _extract_python_docstrings_and_comments(f.content)
            if any(extracted.values()):
                if extracted["module"]:
                    lines.append("**Module Docstring**")
                    for d in extracted["module"]:
                        lines.append("```text\n{}\n```".format(d))
                if extracted["classes"]:
                    lines.append("**Classes**")
                    for d in extracted["classes"]:
                        lines.append("```text\n{}\n```".format(d))
                if extracted["functions"]:
                    lines.append("**Functions**")
                    for d in extracted["functions"]:
                        lines.append("```text\n{}\n```".format(d))
                if extracted["comments"]:
                    lines.append("**Top-of-file Comments**")
                    lines.append("```text")
                    for c in extracted["comments"]:
                        lines.append(c)
                    lines.append("```")
            else:
                lines.append("_Sem docstrings ou comentários detectados._")
            lines.append("")
    return "\n".join(lines)
