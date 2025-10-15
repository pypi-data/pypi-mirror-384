from __future__ import annotations
import os
from typing import Optional, Any

class LLMInterface:
    def __call__(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        raise NotImplementedError

class OpenAIChat(LLMInterface):
    """
    Adaptador simples para o cliente OpenAI (>= 1.40).
    Requer que OPENAI_API_KEY esteja definida no ambiente (pode ser passada via openai_key na função generate).
    """
    def __init__(self, client: Optional[Any] = None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY ausente. "
                "Passe a chave via parâmetro openai_key= na função generate(...), "
                "ou defina a variável de ambiente OPENAI_API_KEY."
            )
        if client is None:
            try:
                from openai import OpenAI
            except Exception as e:
                raise RuntimeError("Instale `openai>=1.40.0` para usar o adaptador OpenAI.") from e
            self.client = OpenAI()
        else:
            self.client = client

    def __call__(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
