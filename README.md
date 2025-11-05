# IA Bot - FastAPI Adapter

Este repositório contém uma versão mínima em FastAPI das funções principais do seu bot Discord (`IA.py`). A API expõe endpoints para chat (via Ollama), busca web e consulta de clima.

Arquivos importantes:
- `api/main.py` - aplicação FastAPI com endpoints: `/health`, `/chat`, `/weather`, `/search`.
- `.env.example` - exemplo de arquivo de configuração (copie para `.env` e preencha suas chaves).
- `requirements.txt` - dependências Python.
- `Dockerfile` - imagem mínima para rodar a API.

Variáveis de ambiente (configurar em `.env`):
- TOKEN (opcional, apenas se for rodar o bot Discord localmente)
- OLLAMA_MODEL (ex: `gemma2:9b`)
- OLLAMA_URL (ex: `http://localhost:11434/api/generate`)
- ALLOWED_CHANNEL_ID (opcional)
- OPENWEATHER_API_KEY (necessária para o endpoint `/weather`)

Como rodar localmente (virtuais):

1) Criar virtualenv e instalar dependências:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```

2) Copiar `.env.example` para `.env` e preencher as chaves.

3) Rodar a API:

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:
- GET /health -> {"status": "ok"}
- POST /chat -> body JSON {"prompt": "texto", "mode_aggressive": false, "use_web_search": false}
- GET /weather?city=Nome -> retorna dados do OpenWeatherMap
- GET /search?q=termo&num=4 -> resultados da busca

Deploy com Docker (exemplo):

```powershell
docker build -t ia-bot-api .
docker run -p 8000:8000 --env-file .env ia-bot-api
```

Observações:
- Não coloque chaves reais em commits públicos. Use secrets do provedor de deploy ou ferramentas como Docker secrets / GitHub Actions Secrets.
- Se quiser, posso refatorar para reusar funções existentes em `IA.py` (transformar em módulo) ou adicionar testes.
