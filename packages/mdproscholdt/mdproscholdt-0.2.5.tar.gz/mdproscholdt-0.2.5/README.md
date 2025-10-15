# mdproscholdt

Gere Markdown de documentação do seu projeto automaticamente, com ou sem IA.

## Instalação (dev)

```bash
pip install -e .
```

## Uso via CLI

```bash
export OPENAI_API_KEY="sua_chave"   # necessário apenas se --use-ai true
proscholdt --root . --out README.generated.md \
           --objective "Documento executivo e visão técnica" \
           --style "Direto, com exemplos" \
           --include "**/*.py,**/*.md" \
           --exclude ".venv/**,node_modules/**,.git/**" \
           --use-ai false
```

Ou via config:

```bash
proscholdt --config examples/mdproscholdt.example.toml
```

## Uso via Python (API mínima)

```python
import mdproscholdt

mdproscholdt.generate(
    root=".",
    objective="README técnico com arquitetura e exemplos",
    style="Clara e prática",
    audience="Desenvolvedores",
    out_path="README.generated.md",
    use_ai=False  # defina True para usar IA
)
```

## Modos de operação

- `use_ai = True`: usa modelo OpenAI (precisa de OPENAI_API_KEY) para criar narrativa e explicações.
- `use_ai = False`: gera documentação estática com:
  - árvore de diretórios,
  - índice de arquivos,
  - extração de **docstrings** (módulo, classes, funções) e **comentários de cabeçalho** de arquivos `.py`,
  - amostras de conteúdo para outros arquivos.

## Segurança
- Respeita `.gitignore` (opcional).
- Blocklist de padrões sensíveis (`.env`, chaves, certificados).
- Amostragem de arquivos grandes para evitar contextos gigantes.


## Uso com IA via parâmetro

```python
import mdproscholdt

mdproscholdt.generate(
    root='.',
    objective='Gerar documentação técnica e explicar arquitetura do projeto',
    style='Clara, detalhada e com exemplos',
    audience='Desenvolvedores',
    out_path='README.auto.md',
    use_ai=True,
    openai_key='SUA_CHAVE_OPENAI_AQUI'
)
```

## Créditos

Desenvolvido por Henrique Proscholdt.

- São Mateus - ES, Brasil
- Telefone: (27) 99513-0691
- Email: proscholdt.h2014@gmail.com
- GitHub: https://github.com/proscholdt
- LinkedIn: https://www.linkedin.com/in/henriqueproscholdt/

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais informações.
