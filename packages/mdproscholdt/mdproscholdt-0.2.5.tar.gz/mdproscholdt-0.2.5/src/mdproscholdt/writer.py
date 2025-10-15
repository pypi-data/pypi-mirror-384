from __future__ import annotations
from typing import Optional
from .config import SmithConfig
from .prompts import DOC_WRITER_SYSTEM, DOC_WRITER_USER_TEMPLATE
from .llm import LLMInterface, OpenAIChat

def generate_markdown(config: SmithConfig, snapshot_md: str, llm: Optional[LLMInterface] = None) -> str:
    if llm is None:
        if config.model.provider == "openai":
            llm = OpenAIChat()
        else:
            raise ValueError("Provider custom requer passar um LLMInterface próprio.")

    system = DOC_WRITER_SYSTEM.format(agent_name=config.agent_name)
    user = DOC_WRITER_USER_TEMPLATE.format(
        objective=config.objective,
        style=config.style,
        audience=config.audience,
        snapshot=snapshot_md[:180000]
    )
    return llm(
        system=system,
        user=user,
        model=config.model.model,
        temperature=config.model.temperature,
        max_tokens=config.model.max_completion_tokens,
    )
