from pathlib import Path
from .config import SmithConfig
from .scanner import scan_project
from .summarize import build_project_context, build_static_markdown
from .writer import generate_markdown

def generate(
    root=".",
    objective="Documentação técnica e visão geral",
    style="Clara e estruturada",
    audience="Desenvolvedores",
    out_path="README.generated.md",
    use_ai=False,
    openai_key: str | None = None
):
    """
    Gera documentação Markdown automaticamente com um único ponto de entrada.

    Se use_ai=False, gera documentação estática (árvore, índice, docstrings e comentários).
    Se use_ai=True, usa LLM para redigir um documento narrativo com base no snapshot.
    """
    cfg = SmithConfig(
        root=root,
        objective=objective,
        style=style,
        audience=audience,
        out_path=out_path,
        use_ai=use_ai
    )

    files = scan_project(
        root=cfg.root,
        include_patterns=cfg.include,
        exclude_patterns=cfg.exclude,
        blocklist_patterns=cfg.blocklist,
        follow_gitignore=cfg.follow_gitignore,
        max_files=cfg.max_files,
        max_bytes_per_file=cfg.max_bytes_per_file,
        sample_bytes_head=cfg.sample_bytes_head,
        sample_bytes_tail=cfg.sample_bytes_tail,
    )

    snapshot = build_project_context(files)

    # Session-only key handling
    if cfg.use_ai and openai_key:
        import os
        os.environ['OPENAI_API_KEY'] = openai_key

    if not cfg.use_ai:
        markdown = build_static_markdown(cfg, files, snapshot)
    else:
        markdown = generate_markdown(cfg, snapshot)

    Path(cfg.out_path).write_text(markdown, encoding="utf-8")
    print(f"Gerado: {Path(cfg.out_path).resolve().as_posix()}")
