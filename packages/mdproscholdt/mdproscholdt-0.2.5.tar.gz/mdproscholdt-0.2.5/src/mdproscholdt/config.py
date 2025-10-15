from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
try:
    import tomllib as tomli  # Python 3.11+
except Exception:
    import tomli  # Python 3.9-3.10

DEFAULT_INCLUDE = ["**/*.py", "**/*.md", "**/*.toml", "**/*.yaml", "**/*.yml"]
DEFAULT_EXCLUDE = [
    ".git/**", ".hg/**", ".svn/**",
    ".venv/**", "venv/**", "env/**",
    "node_modules/**", "dist/**", "build/**",
    "**/__pycache__/**", "**/*.pyc",
]
DEFAULT_BLOCKLIST = [
    "**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/id_rsa", "**/id_ed25519",
    "**/*.p12", "**/*.pfx", "**/*.keystore", "**/*.jks",
]

class ModelConfig(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    temperature: float = 0.2
    max_completion_tokens: int = 6000
    system_prompt_variant: str = "doc-writer-v1"

class SmithConfig(BaseModel):
    root: str = "."
    include: List[str] = Field(default_factory=lambda: DEFAULT_INCLUDE.copy())
    exclude: List[str] = Field(default_factory=lambda: DEFAULT_EXCLUDE.copy())
    blocklist: List[str] = Field(default_factory=lambda: DEFAULT_BLOCKLIST.copy())
    follow_gitignore: bool = True

    max_files: int = 2000
    max_bytes_per_file: int = 60_000
    sample_bytes_head: int = 15_000
    sample_bytes_tail: int = 10_000

    objective: str = "Gerar documentação técnica e visão geral do projeto."
    style: str = "Clara, estruturada, com exemplos."
    audience: str = "Desenvolvedores e stakeholders técnicos."
    agent_name: str = "DocProscholdt"

    out_path: str = "README.generated.md"
    template_path: Optional[str] = None

    model: ModelConfig = Field(default_factory=ModelConfig)
    use_ai: bool = False

class FileConfig(SmithConfig):
    pass

def load_config(path: Optional[str]) -> SmithConfig:
    if path is None:
        return SmithConfig()
    with open(path, "rb") as f:
        data = tomli.load(f)
    return FileConfig(**data.get("mdproscholdt", {}))
