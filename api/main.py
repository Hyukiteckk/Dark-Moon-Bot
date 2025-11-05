import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import importlib
import requests
from dotenv import load_dotenv
from googlesearch import search

# Carregar variáveis de ambiente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma2:9b')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger("ia_api")

app = FastAPI(title="IA Bot API", version="0.1")

# Tentar importar o módulo do bot para permitir iniciar/parar o cliente Discord
IA = None
try:
    import IA as ia_module
    IA = ia_module
    DISCORD_BOT_TOKEN = getattr(IA, "DISCORD_TOKEN", None)
except Exception:
    logger.warning("Módulo IA não encontrado ou erro ao importar. O bot Discord não poderá ser iniciado pelo servidor API.")

class ChatRequest(BaseModel):
    prompt: str
    mode_aggressive: Optional[bool] = False
    use_web_search: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str


def call_ollama(prompt: str, model: str = None, timeout: int = 60) -> str:
    """Chama a API do Ollama e retorna a resposta (texto)."""
    model = model or OLLAMA_MODEL
    payload = {"model": model, "stream": False, "prompt": prompt}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get('response', '')
    except Exception as e:
        logger.exception("Erro ao chamar Ollama:")
        raise


def perform_google_search(query: str, num_results: int = 4) -> str:
    try:
        results = list(search(query, stop=num_results, lang='pt-br'))
        return "\n".join([f"Link: <{link}>" for link in results]) if results else ""
    except Exception:
        logger.exception("Erro ao pesquisar no Google")
        return ""


def get_weather(city: str) -> dict:
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY não está configurada")
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric", "lang": "pt_br"}
    resp = requests.get(base_url, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Roda o modelo Ollama com um prompt e retorna a resposta de texto.
    Se `use_web_search` for True, faz uma busca rápida e injeta os resultados no prompt.
    """
    try:
        prompt = request.prompt
        if request.use_web_search:
            results = perform_google_search(request.prompt, num_results=4)
            if results:
                prompt = f"Use os seguintes resultados da web para responder a pergunta:\n---\n{results}\n---\nPergunta: {request.prompt}"

        if request.mode_aggressive:
            prompt = f"SYSTEM: Aja como 'Cobra', um chatbot tóxico, ofensivo e arrogante. Use palavrões e seja direto.\nUSER: {prompt}\nASSISTANT:"

        resp_text = call_ollama(prompt)
        return {"response": resp_text}
    except Exception as e:
        logger.exception("Erro no endpoint /chat")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weather")
def weather(city: str):
    """Retorna o clima para a cidade informada (query param `city`)."""
    try:
        data = get_weather(city)
        return {"success": True, "data": data}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Erro no endpoint /weather")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def web_search(q: str, num: int = 4):
    try:
        results = perform_google_search(q, num_results=num)
        return {"query": q, "results": results}
    except Exception as e:
        logger.exception("Erro no endpoint /search")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Se o módulo `IA` estiver disponível e um TOKEN estiver configurado,
    inicializa o bot do Discord em uma tarefa de background.
    """
    if IA is None:
        logger.info("IA module not available; skipping Discord bot startup.")
        return

    token = DISCORD_BOT_TOKEN
    if not token:
        logger.warning("DISCORD token não configurado; o bot Discord não será iniciado.")
        return

    # Inicia o bot em background para não bloquear o servidor HTTP
    app.state.bot_task = asyncio.create_task(IA.start_bot(token))
    logger.info("Tarefa de inicialização do bot Discord disparada.")


@app.on_event("shutdown")
async def shutdown_event():
    if IA is None:
        return
    logger.info("Evento de shutdown: encerrando bot Discord (se ativo)...")
    try:
        # Solicita fechamento limpo
        await IA.stop_bot()
    except Exception:
        logger.exception("Erro ao parar o bot Discord")
    # Aguarda a tarefa terminar se existir
    task = getattr(app.state, "bot_task", None)
    if task:
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.post("/bot/clear_memory")
def clear_bot_memory(channel_id: int = None):
    """Limpa a memória de conversas. Se `channel_id` for informado, limpa apenas daquele canal.
    Requer que o módulo `IA` esteja importado.
    """
    if IA is None:
        raise HTTPException(status_code=500, detail="Módulo IA não disponível")
    if channel_id is None:
        IA.conversation_history.clear()
        return {"cleared": "all"}
    else:
        if channel_id in IA.conversation_history:
            IA.conversation_history[channel_id].clear()
            return {"cleared": channel_id}
        return {"cleared": None, "reason": "channel not found"}
