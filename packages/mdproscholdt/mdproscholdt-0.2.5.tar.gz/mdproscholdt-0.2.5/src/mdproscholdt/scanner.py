from __future__ import annotations
from dataclasses import dataclass
from typing import List, Iterable, Tuple
from pathlib import Path
from pathspec import PathSpec
from rich.progress import track

@dataclass
class ScannedFile:
    path: str
    size: int
    sha1: str
    sampled: bool
    content: str

def _sha1_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha1(b).hexdigest()

def _load_gitignore(root: Path) -> PathSpec:
    gitignore = root / ".gitignore"
    if gitignore.exists():
        return PathSpec.from_lines("gitwildmatch", gitignore.read_text().splitlines())
    return PathSpec.from_lines("gitwildmatch", [])

def _compile_spec(patterns: Iterable[str]) -> PathSpec:
    return PathSpec.from_lines("gitwildmatch", patterns)

def iter_files(root: Path, include: PathSpec, exclude: PathSpec, blocklist: PathSpec):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if blocklist.match_file(rel):
            continue
        if exclude.match_file(rel):
            continue
        if not include.match_file(rel):
            continue
        yield p

def sample_bytes(raw: bytes, head: int, tail: int) -> Tuple[str, bool]:
    n = len(raw)
    if n <= head + tail:
        return raw.decode(errors="replace"), False
    head_b = raw[:head].decode(errors="replace")
    tail_b = raw[-tail:].decode(errors="replace")
    marker = "\n\n---\n[truncated: {} bytes total; showing head {} + tail {}]\n---\n\n".format(n, head, tail)
    return head_b + marker + tail_b, True

def scan_project(
    root: str,
    include_patterns: List[str],
    exclude_patterns: List[str],
    blocklist_patterns: List[str],
    follow_gitignore: bool,
    max_files: int,
    max_bytes_per_file: int,
    sample_bytes_head: int,
    sample_bytes_tail: int,
) -> List[ScannedFile]:
    root_path = Path(root).resolve()
    gitignore_spec = _load_gitignore(root_path) if follow_gitignore else _compile_spec([])
    include_spec = _compile_spec(include_patterns)
    exclude_spec = _compile_spec(exclude_patterns) if exclude_patterns else _compile_spec([])
    blocklist_spec = _compile_spec(blocklist_patterns)

    files = []
    candidates = [p for p in iter_files(root_path, include_spec, exclude_spec, blocklist_spec)
                  if not gitignore_spec.match_file(p.relative_to(root_path).as_posix())]
    candidates = sorted(candidates)[:max_files]

    for p in track(candidates, description="Lendo arquivos"):
        rel = p.relative_to(root_path).as_posix()
        raw = p.read_bytes()
        sha1 = _sha1_bytes(raw)
        if len(raw) > max_bytes_per_file:
            content, sampled = sample_bytes(raw, sample_bytes_head, sample_bytes_tail)
        else:
            content, sampled = raw.decode(errors="replace"), False
        files.append(ScannedFile(path=rel, size=len(raw), sha1=sha1, sampled=sampled, content=content))
    return files
