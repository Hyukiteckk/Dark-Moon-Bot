"""
📊 UTILIDADES E FUNÇÕES COMPARTILHADAS
Funções usadas em múltiplos comandos
"""

import re
import requests
import logging
import os
import discord
from googlesearch import search

# Configurações de APIs
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Dados de Pontos (compartilhado globalmente)
import json
import time

VOICE_POINTS_FILE = "voice_points.json"
voice_join_times = {}
voice_pending_seconds = {}
user_points = {}

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 GERENCIAMENTO DE PONTOS
# ═══════════════════════════════════════════════════════════════════════════════

def load_points():
    """Carrega pontos do arquivo JSON."""
    global user_points
    if not os.path.exists(VOICE_POINTS_FILE):
        return {}
    try:
        with open(VOICE_POINTS_FILE, "r") as f:
            user_points = json.load(f)
            return user_points
    except:
        return {}

def save_points(data):
    """Salva pontos no arquivo JSON."""
    with open(VOICE_POINTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_points = load_points()

def add_user_points(user_id: str, points: int):
    """Adiciona pontos a um usuário."""
    if user_id not in user_points:
        user_points[user_id] = 0
    user_points[user_id] += points
    save_points(user_points)

def get_user_points(user_id: str) -> int:
    """Obtém pontos de um usuário."""
    return user_points.get(user_id, 0)

def clear_all_points():
    """Limpa todos os pontos."""
    global user_points
    user_points.clear()
    voice_pending_seconds.clear()
    current_t = time.time()
    for uid in voice_join_times:
        voice_join_times[uid] = current_t
    save_points(user_points)

def update_current_voice_sessions():
    """Calcula pontos de quem está na call AGORA."""
    current_time = time.time()
    active_users = list(voice_join_times.keys())
    
    for user_id in active_users:
        start_time = voice_join_times[user_id]
        session_seconds = current_time - start_time
        voice_join_times[user_id] = current_time
        
        total_seconds = voice_pending_seconds.get(user_id, 0) + session_seconds
        points_to_add = int(total_seconds // 900)
        remainder_seconds = total_seconds % 900
        
        voice_pending_seconds[user_id] = remainder_seconds
        
        if points_to_add > 0:
            add_user_points(user_id, points_to_add)
    
    save_points(user_points)

def start_voice_session(user_id: str):
    """Inicia sessão de voz para um usuário."""
    if user_id not in voice_join_times:
        voice_join_times[user_id] = time.time()
        logging.info(f"🎙️ Usuário {user_id} começou a contar pontos.")

def stop_voice_session(user_id: str):
    """Para sessão de voz e calcula pontos."""
    if user_id not in voice_join_times:
        return
    
    start_time = voice_join_times.pop(user_id)
    session_seconds = time.time() - start_time
    
    total_seconds = voice_pending_seconds.get(user_id, 0) + session_seconds
    points_to_add = int(total_seconds // 900)
    remainder_seconds = total_seconds % 900
    
    voice_pending_seconds[user_id] = remainder_seconds
    
    if points_to_add > 0:
        add_user_points(user_id, points_to_add)
        logging.info(f"💾 Usuário {user_id} ganhou {points_to_add} pontos.")

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 FUNÇÕES AUXILIARES - APIs E BUSCA
# ═══════════════════════════════════════════════════════════════════════════════

def get_weather(city: str, api_key: str) -> dict:
    """Busca dados de clima de uma cidade."""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "pt_br"}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 404:
            return {"success": False, "error": "Cidade não encontrada."}
        elif response.status_code == 401:
            return {"success": False, "error": "Chave de API inválida."}
        else:
            return {"success": False, "error": f"Erro na API: Código {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Erro ao conectar: {e}"}

def perform_google_search(query: str, num_results: int = 4) -> str:
    """Realiza busca no Google e retorna resultados formatados."""
    try:
        results = list(search(query, stop=num_results, lang='pt-br'))
        if not results:
            return "Nenhum resultado encontrado."
        return "\n".join([f"Link: <{link}>" for link in results])
    except Exception as e:
        logging.error(f"Erro ao buscar no Google: {e}")
        return f"Erro ao pesquisar: {e}"

def call_groq(prompt: str, system_message: str = None, modo_agressivo: bool = False) -> str:
    """Chama a API do Groq para IA."""
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY não encontrada")
        return "Erro: API Key não configurada."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 1.2 if modo_agressivo else 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Erro em call_groq: {e}")
        return ""

async def get_member(guild: discord.Guild, user_ref: str):
    """Busca membro no servidor por ID, menção ou nome."""
    if not guild:
        return None
    
    member = None
    user_ref_cleaned = re.sub(r'[<@!>]', '', user_ref)
    
    if user_ref_cleaned.isdigit():
        try:
            member = guild.get_member(int(user_ref_cleaned)) or await guild.fetch_member(int(user_ref_cleaned))
        except (discord.NotFound, discord.HTTPException):
            member = None
    
    if member:
        return member
    
    user_lower = user_ref.lower()
    return discord.utils.find(
        lambda m: m.name.lower() == user_lower or m.display_name.lower() == user_lower,
        guild.members
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ✅ VALIDAÇÕES E VERIFICAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

def check_channel_permission(channel_id: int, channels_allowed: list) -> bool:
    """Verifica se o comando pode ser executado no canal."""
    return channel_id in channels_allowed
