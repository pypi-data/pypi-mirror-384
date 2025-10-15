# Forgebase

Forgebase reúne três blocos principais usados neste monorepo:

- **forge_utils** – logging estruturado e utilidades de paths/configuração.
- **forgebase** – framework MVC-C enxuto baseado em Pydantic v2 (modelos, commands,
  controllers, views e persistência).
- **llm_client** – cliente agnóstico para a OpenAI Responses API com suporte a streaming,
  tool calling e replays offline.

A biblioteca está disponível em [PyPI](https://pypi.org/project/forgebase/) e também no
TestPyPI para validação prévia.

## Instalação rápida

```bash
pip install forgebase
```

Crie um ambiente virtual limpo antes de instalar (`python -m venv .venv && source .venv/bin/activate`).

---

## ⭐ Novo na v0.2.2: Streaming + Tools (Responses API)

Esta versão foca em robustez do streaming com tool calling sobre a OpenAI Responses API.

- Headers de streaming: adicionamos `Accept: text/event-stream` e melhoramos timeouts (SSE sem read timeout) no cliente HTTP.
- Normalização de tools: agora aceitamos tanto o formato top‑level da Responses API
  (`{\"type\":\"function\",\"name\":...}`) quanto o formato “aninhado” comum no Chat Completions
  (`{\"type\":\"function\",\"function\": {\"name\":..., \"parameters\":...}}`). O cliente normaliza para o contrato oficial da Responses API antes de enviar.
- Sem fallback para Chat Completions: não utilizamos Chat Completions; todo o fluxo permanece na Responses API.
- Header opcional de beta: é possível habilitar `OpenAI-Beta: responses=v1` via `OPENAI_BETA_RESPONSES=1` caso seu ambiente exija este gate.

Documentação relacionada: `docs/api/openai_responses.md`, `docs/api/openai_responses_tool_calling.md` e `docs/api/streaming_tools_guide.md`.

Impacto: corrige erros intermitentes 400 observados durante streaming + tools e melhora compatibilidade com formatos de tools enviados por clientes legados.

---

## ⭐ Novo na v0.2.3: Robustez de Streaming + Follow‑up de Tools

Esta versão refina o fluxo de streaming e o follow‑up de ferramentas:

- Tratamento de erros em SSE:
  - Em 4xx, o cliente drena o corpo e lança `APIResponseError` com a mensagem do provider (elimina o erro "without read()" e evita conexões em mau estado).
- Follow‑ups de tool calling (Responses API):
  - O follow‑up inclui o descritor bruto `tool_use` (além de `function_call`) antes do respectivo `*_output`, alinhando com variantes da Responses API em cenários multi‑turn.
- Testes e documentação:
  - Novos testes de streaming e follow‑up.
  - Guia: `docs/api/streaming_tools_guide.md`.

Compatibilidade: sem mudanças de interface — sua integração atual continua funcionando.

---

## 🧪 Desenvolvimento (v0.2.6+)

Esta seção resume como depurar e validar cenários de streaming + tools no ForgeBase.

- Defaults a partir da v0.2.5/0.2.6
  - Follow‑up em streaming: `outputs-only` habilitado (não reenvia descriptors brutos)
  - `tool_choice` no follow‑up: `none`
  - `name` incluído nos outputs

- Flags de compatibilidade (override)
  - `FORGEBASE_FOLLOWUP_OUTPUTS_ONLY=0|1`
  - `FORGEBASE_FOLLOWUP_TOOL_CHOICE=none|auto|required`
  - `FORGEBASE_OUTPUT_NAME=0|1`
  - `FORGEBASE_OUTPUT_KIND=function_result|tool_result`

- Diagnóstico (sem vazar conteúdo)
  - `FORGEBASE_DEBUG_FOLLOWUP=1` emite em nível INFO a linha:
    `[follow-up] prev=... outputs=N types=[...] call_ids=[...] unique=N`
  - Recomendações:
    - Habilitar `DEBUG` no logger durante testes locais
    - Usar hooks do provider para imprimir o payload do follow‑up quando necessário

- Reconciliação de call_id (v0.2.8+)
  - IDs `call_*` coletados dos eventos de streaming e, se preciso, via `input_items`
  - Substituem IDs alternativos ao montar os outputs no follow‑up
  - Buffer de outputs particionado por `previous_response_id`

- Testes
  - Rodar toda a suíte: `pytest -q`
  - Casos relevantes:
    - `tests/test_streaming_error_handling.py`
    - `tests/test_streaming_tool_use_followup.py`
    - `tests/test_followup_flags_overrides.py`
  - O guia `docs/api/streaming_tools_guide.md` reforça cenários, flags e troubleshooting


## ⭐ Novo na v0.2.1: LLMClientFactory

A partir da v0.2.1, use `LLMClientFactory` para criar providers LLM de forma desacoplada:

```python
from forgebase import LLMClientFactory, Tool

# Opção 1: Criação manual
provider = LLMClientFactory.create("openai", api_key="sk-...", timeout=60)

# Opção 2: Auto-configuração via variável de ambiente (OPENAI_API_KEY)
provider = LLMClientFactory.create_from_env("openai")

# Usar o provider
response = provider.send_message("Hello, world!")
print(response)

# Trocar provider transparentemente (quando disponível)
# provider = LLMClientFactory.create("llama")  # Mesma interface!
```

**Por que usar a factory?**
- ✅ **Desacoplamento**: Código não depende de implementação específica (OpenAI, Llama, etc.)
- ✅ **Extensibilidade**: Trocar provider mudando apenas 1 string
- ✅ **Testabilidade**: Mock de interface `ILLMClient` em vez de classe concreta
- ✅ **Preparado para o futuro**: Suporte a múltiplos providers sem breaking changes

> **⚠️ Deprecação:** `OpenAIProvider` ainda funciona na v0.2.1 (backward compatible), mas recomendamos migrar para `LLMClientFactory`. Veja exemplos abaixo.

---

## Pacote por pacote

### forge_utils

- `forge_utils.log_service.LogService` configura logging com console/arquivo rotativo e filtros.
- `forge_utils.log_service.logger` é a instância global pronta para uso.
- `forge_utils.paths` oferece helpers (`build_app_paths`, `ensure_dirs`) para organizar arquivos
  de configuração, histórico e cache.

### forgebase

Reexporta o framework MVC-C básico. Os pontos de entrada mais usados são:

- `CustomBaseModel` / `BaseModelData`: modelos Pydantic com suporte a *dirty tracking* e observers.
- `CustomCommandBase` + `guard_errors`: encapsulam regras de negócio, padronizando
  o tratamento de exceções (`CommandException`).
- `CustomBaseController` / `CustomBaseView`: composição MVC-C mínima.
- `PersistenceFactory` + `JsonPersistence`: persistência compatível com Pydantic v2.

Todos estes nomes estão disponíveis diretamente com `from forgebase import ...`.

### llm_client

O cliente LLM também é reexportado por `forgebase` para facilitar o consumo:

**API Pública (v0.2.1+):**
- `LLMClientFactory`: factory para criar providers sem conhecer implementação (✅ **use este!**)
- `ILLMClient`: interface Protocol para type hints e extensibilidade
- `Tool`: modelo Pydantic que representa o schema JSON das ferramentas
- `APIResponseError` / `ConfigurationError`: exceções específicas do cliente
- `ContentPart`, `OutputMessage`, `ResponseResult`, `TextFormat`, `TextOutputConfig`: modelos
  retornados pelo Responses API

**Legacy (deprecated - mantido para compatibilidade):**
- `OpenAIProvider`: ⚠️ usar `LLMClientFactory.create("openai")` em vez disso
- `LLMOpenAIClient`: ⚠️ interno - não usar diretamente

**Multi-provider ready:** A arquitetura está preparada para múltiplos providers (Llama, Anthropic, OpenRouter)
sem breaking changes no código cliente. Use `LLMClientFactory` para garantir compatibilidade futura.

## Guia rápido de uso

### Core MVC-C

```python
from forgebase import CustomBaseModel, CustomCommandBase, JsonPersistence, guard_errors

class User(CustomBaseModel):
    id: int
    name: str

class CreateUserCommand(CustomCommandBase):
    @guard_errors
    def execute(self, payload: dict) -> User:
        model = User(**payload)
        # ... lógica de negócio ...
        return model

storage = JsonPersistence("users.json")
```

### Cliente LLM – configuração e chamadas

Crie um arquivo `.env` na raiz do projeto (ou exporte no shell) com:

```
OPENAI_API_KEY=sk-...
```

Todos os exemplos abaixo carregam essa chave automaticamente via `python-dotenv`.

#### Chamada síncrona

```python
import os
from dotenv import load_dotenv
from forgebase import APIResponseError, ConfigurationError, LLMOpenAIClient

load_dotenv()
client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")

try:
    response = client.send_prompt("Por que o céu é azul?")
    answer = "\n".join(
        part.text.strip()
        for item in response.output
        for part in getattr(item, "content", [item])
        if getattr(part, "text", None)
    )
    print(answer)
except (APIResponseError, ConfigurationError) as exc:
    print(f"Falha na chamada: {exc}")
```

##### Migrando do uso direto da OpenAI API

Antes utilizávamos o SDK oficial diretamente. Agora a camada `LLMOpenAIClient` traz timeout,
hooks e tool calling prontos, além de facilitar a troca de provider.

```python
# Legado: uso direto do SDK da OpenAI
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
resp = client.responses.create(model="gpt-4o-mini", input="Por que o céu é azul?")
print(resp.output[0].content[0].text)
```

```python
# Atual: via LLMOpenAIClient encapsulado
from forgebase import LLMOpenAIClient

client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")
resp = client.send_prompt("Por que o céu é azul?")
print(resp.output[0].content[0].text)
```

#### Configurando timeout (⭐ novo na v0.2.0)

Por padrão, as chamadas HTTP usam timeout de 120 segundos. Você pode customizar:

```python
# Timeout de 45 segundos
client = LLMOpenAIClient(
    api_key=os.environ["OPENAI_API_KEY"],
    timeout=45  # segundos
)

# Ou via OpenAIProvider
from forgebase import OpenAIProvider

provider = OpenAIProvider(timeout=45)
provider.set_api_key(os.environ["OPENAI_API_KEY"])
result = provider.send_message("Hello")
```

**Importante:** O timeout se aplica ao tempo total incluindo retries. Com `timeout=45` e `max_tries=4`, o sistema não ultrapassará 45 segundos mesmo com múltiplas tentativas.

#### Chamada com streaming

```python
import os
from dotenv import load_dotenv
from forgebase import LLMOpenAIClient

load_dotenv()
client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")

stream = client.send_prompt("Conte uma história curta sobre um robô e uma criança.", streamed=True)
for delta in stream:
    print(delta, end="", flush=True)
print()
```

#### Chamada multimodal (imagem + áudio)

```python
import os
from dotenv import load_dotenv
from forgebase import LLMOpenAIClient

load_dotenv()
client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o")

response = client.send_prompt(
    "Descreva a imagem e comente o áudio anexado.",
    images=["https://upload.wikimedia.org/wikipedia/commons/9/99/Colorful_sunset.jpg"],
    audio={"base64": "ZGF0YQ==", "mime_type": "audio/wav"},
)
print(response)
```

#### Listar modelos disponíveis

```python
import os
from dotenv import load_dotenv
from forgebase import LLMOpenAIClient

load_dotenv()
client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
models = client.list_models()
print(models["data"][0])
```

#### Tool calling síncrono (v0.2.1+)

```python
import os
from dotenv import load_dotenv
from forgebase import LLMClientFactory, Tool

load_dotenv()

# ✅ Novo: usar factory
provider = LLMClientFactory.create_from_env("openai")

# 1) Descreva a ferramenta com JSON Schema compatível com a Responses API
tool = Tool(
    type="function",
    name="say_hello",
    parameters={"type": "object", "properties": {"who": {"type": "string"}}, "required": ["who"]},
)
# 2) Conte ao provider quais ferramentas estão disponíveis
provider.configure_tools([tool], tool_choice="required")
# 3) Registre o handler Python que será chamado quando o modelo disparar a ferramenta
provider.register_tool("say_hello", lambda args: f"Olá, {args['who']}!")

# 4) Use send_message normalmente: o provider executa as tools e devolve o texto final
print(provider.send_message("Cumprimente Forgebase."))
```

<details>
<summary>📜 Código antigo (deprecated - clique para expandir)</summary>

```python
# ⚠️ Deprecated: usando OpenAIProvider diretamente
from forgebase import OpenAIProvider, Tool

provider = OpenAIProvider()
provider.set_api_key(os.environ["OPENAI_API_KEY"])
# ... resto do código igual
```
</details>

##### Tool calling com orquestração automática

Providers criados pela factory encapsulam todos os ciclos de *tool calling* da Responses API.
Basta definir o schema das ferramentas, registrar os handlers e chamar `send_message`:

```python
from forgebase import LLMClientFactory, Tool

provider = LLMClientFactory.create("openai", api_key=os.environ["OPENAI_API_KEY"], timeout=60)

weather_tool = Tool(
    type="function",
    name="get_weather",
    description="Retorna a temperatura atual para uma cidade brasileira.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)

provider.configure_tools([weather_tool], tool_choice="required")

def get_weather(args: dict[str, str]) -> str:
    city = args["city"]
    return f"{city}, 30 graus."

provider.register_tool("get_weather", get_weather)

print(provider.send_message("Qual a temperatura de hoje em São Paulo?"))
```

Internamente o provider:

- Executa múltiplas rodadas de tool calling até chegar no texto final — o mesmo fluxo usado nos testes `test_demo_tool_call_api_forced` e `test_openai_provider_hooks_with_tools`.
- Gerencia `tool_choice`, IDs de chamadas e payloads `function_call_output` / `custom_tool_call_output`, montando o `input_override` correto para cada rodada, como coberto em `tests/test_openai_tool_calling.py`.
- Expõe hooks (`before_tool_call`, `after_tool_call`, `tool_error`, etc.) que você pode monitorar para métricas e logs.
- Funciona tanto com chamadas síncronas (`send_message`) quanto streaming (`send_stream`) sem alterar o código dos handlers.

**Passo a passo resumido**

- Configure o provider com `set_api_key`.
- Descreva as ferramentas com `forgebase.Tool` em `configure_tools`.
- Registre cada handler com `register_tool`.
- Dispare `send_message` (ou `send_stream`) — o provider executa as ferramentas e devolve apenas o texto final.
- Opcional: adicione hooks (`register_hook`) para inspecionar `before_tool_call`, `after_tool_call` ou erros.

Para validar fluxos sem acessar a API real, use `LLMOpenAIClient` com uma resposta fake
(`response=<objeto compatível>`) ou rode `python -m llm_client.demo_tool_call_api` que inclui
um modo offline utilizando as mesmas rotinas de orquestração (vide `tests/test_demo_tool_call_api.py`).

#### Tool calling com streaming

```python
import os
from dotenv import load_dotenv
from forgebase import OpenAIProvider, Tool

load_dotenv()
provider = OpenAIProvider()
provider.set_api_key(os.environ["OPENAI_API_KEY"])

tool = Tool(
    type="function",
    name="summarize_numbers",
    parameters={"type": "object", "properties": {"nums": {"type": "array", "items": {"type": "number"}}}},
)
provider.configure_tools([tool], tool_choice="auto")
provider.register_tool("summarize_numbers", lambda args: sum(args.get("nums", [])))

for chunk in provider.send_stream("Considere os números 2, 4, 6 e mostre a soma."):
    print(chunk, end="", flush=True)
print()

# Verifique tests/test_openai_tool_calling.py::test_streaming_tool_call_flow
# para um cenário completo de múltiplas rodadas no modo streaming.
```

#### Hooks de eventos

Tanto o `LLMOpenAIClient` quanto o `OpenAIProvider` expõem um sistema simples de
hooks para instrumentar o fluxo:

```python
from forgebase import LLMOpenAIClient, OpenAIProvider

client = LLMOpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
client.register_hook("before_request", lambda ctx: print("▶", ctx["prompt"]))
client.register_hook("after_response", lambda ctx: print("◀", ctx.get("response")))

provider = OpenAIProvider(client=client)
provider.register_hook("before_tool_call", lambda ctx: print("tool", ctx["tool"]))
provider.register_hook("after_tool_call", lambda ctx: print("tool result", ctx["result"]))
```

Eventos disponíveis:

- `before_request`, `after_response`, `on_error`, `on_cache_hit` (cliente LLM)
- `before_send`, `after_send`, `on_error`, `before_tool_call`, `after_tool_call`, `tool_error`, `cache_hit` (provider)

### Demo completo

O projeto inclui uma demo mais abrangente que cobre respostas diretas, streaming,
(tool calling) e replays offline:

```bash
PYTHONPATH=shared/src:apps/llm_client/src python -m llm_client.example_full_usage
```

No Windows (PowerShell):

```powershell
$env:PYTHONPATH = "shared/src;apps/llm_client/src"
python -m llm_client.example_full_usage
```

O arquivo `apps/llm_client/src/llm_client/example_full_usage.py` comenta cada etapa
(passos para configurar `OPENAI_API_KEY`, habilitar tool calling real com
`DEMO_TOOL_CALLING=1`, e como funciona o replay offline).

## Configuração do ambiente

### Opção 1 – Poetry (recomendada)

O `pyproject.toml` já descreve todos os pacotes via `path`. Basta executar na raiz:

```bash
poetry install
poetry run pytest -q
poetry run python -m llm_client.example_full_usage
```

O Poetry cria e gerencia o ambiente virtual automaticamente; não é necessário ajustar o
`PYTHONPATH` manualmente.

### Opção 2 – pip + requirements

Se preferir `pip`, gere um virtualenv e instale as dependências de desenvolvimento com
o arquivo `requirements-dev.txt` gerado a partir do `pyproject`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
```

O arquivo pode ser sincronizado com o `pyproject.toml` executando `python requirements-dev.py`.
Depois disso, exporte `PYTHONPATH=shared/src:framework/src:apps/llm_client/src:cli/src` (ou
use `python -m` para os módulos) e rode `pytest -q` normalmente.

## Desenvolvimento local

- Testes: `pytest -q` (ou `poetry run pytest -q`).
- Linters: `ruff check .` e `mypy --config-file mypy.ini` (com `poetry run` se estiver usando Poetry).
- Build: `python -m build` gera wheel/sdist para publicar em TestPyPI/PyPI.

## Onde continuar

- `docs/api/openai_responses.md`: detalhes da Responses API e eventos de streaming.
 - `docs/api/openai_responses_tool_calling.md`: guia de tool calling, payloads e replays.
 - `docs/api/streaming_tools_guide.md`: guia extensivo de streaming + tools (SSE, timeouts, follow‑ups).
- `docs/architecture/forgebase-architecture.md`: visão completa da arquitetura e fluxos.
- `docs/release-guide.md`: processo recomendado de versionamento e publicação.
- `docs/testing-strategy.md`: abordagem de testes e boas práticas.
- `docs/configuration.md`: variáveis de ambiente e diretórios importantes.
- `docs/providers/adding-new-provider.md`: instruções para suportar novos LLMs.
- `docs/cli/usage.md`: comandos expostos pela CLI.
- `docs/CONTRIBUTING.md`: convenções de contribuição.
- `docs/adr/README.md`: decisões arquiteturais registradas.
- `docs/tech-debts/TD-001-Robustez-Tool-Calling-Responses.md`: backlog de melhorias planejadas.

Sinta-se à vontade para abrir issues ou PRs com sugestões e correções.
