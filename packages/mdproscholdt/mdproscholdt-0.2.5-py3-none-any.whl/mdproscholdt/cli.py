from __future__ import annotations
import argparse
from rich.console import Console
from pathlib import Path
from .config import load_config, SmithConfig
from .scanner import scan_project
from .summarize import build_project_context, build_static_markdown
from .writer import generate_markdown

console = Console()

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("proscholdt", description="Gere Markdown do seu projeto com (ou sem) IA.")
    p.add_argument("--config", type=str, default=None, help="Caminho para mdproscholdt.toml")
    p.add_argument("--root", type=str, help="Raiz do projeto")
    p.add_argument("--include", type=str, help='Padrões separados por vírgula, ex: "**/*.py,**/*.md"')
    p.add_argument("--exclude", type=str, help='Padrões separados por vírgula')
    p.add_argument("--objective", type=str)
    p.add_argument("--style", type=str)
    p.add_argument("--audience", type=str)
    p.add_argument("--agent-name", type=str)
    p.add_argument("--out", type=str, help="Arquivo de saída .md")
    p.add_argument("--model", type=str, help="Modelo (ex: gpt-4o-mini)")
    p.add_argument("--temperature", type=float)
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--use-ai", type=str, help="true|false (default: false)")
    return p.parse_args()

def merge_config(file_cfg: SmithConfig, args: argparse.Namespace) -> SmithConfig:
    cfg = file_cfg.model_copy(deep=True)
    if args.root: cfg.root = args.root
    if args.include: cfg.include = [s.strip() for s in args.include.split(",") if s.strip()]
    if args.exclude: cfg.exclude = [s.strip() for s in args.exclude.split(",") if s.strip()]
    if args.objective: cfg.objective = args.objective
    if args.style: cfg.style = args.style
    if args.audience: cfg.audience = args.audience
    if args.agent_name: cfg.agent_name = args.agent_name
    if args.out: cfg.out_path = args.out
    if args.model: cfg.model.model = args.model
    if args.temperature is not None: cfg.model.temperature = args.temperature
    if args.max_tokens is not None: cfg.model.max_completion_tokens = args.max_tokens
    if args.use_ai:
        val = args.use_ai.strip().lower()
        cfg.use_ai = val in ("1", "true", "yes", "y")
    return cfg

def main():
    args = parse_args()
    file_cfg = load_config(args.config)
    cfg = merge_config(file_cfg, args)

    console.rule("[bold]mdproscholdt[/bold]")
    console.print(f"[bold]Root:[/bold] {cfg.root}")
    console.print(f"[bold]Out:[/bold] {cfg.out_path}")
    console.print(f"[bold]Use AI:[/bold] {cfg.use_ai}")

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

    if not cfg.use_ai:
        md = build_static_markdown(cfg, files, snapshot)
    else:
        md = generate_markdown(cfg, snapshot)

    out = Path(cfg.out_path)
    out.write_text(md, encoding="utf-8")
    console.print(f"[green]Gerado:[/green] {out.resolve().as_posix()}")
