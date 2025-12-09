import discord
import requests
import asyncio
import os
import re
import logging
from dotenv import load_dotenv
from datetime import datetime
from collections import deque
from googlesearch import search 

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
load_dotenv()

# --- Variáveis de Ambiente ---
DISCORD_TOKEN = os.getenv('TOKEN')
# Configuração do GROQ
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '0'))
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# --- Intents do Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

# --- Estado Global ---
modo_agressivo = False
conversation_history = {}
HISTORY_LIMIT = 32

# --- Funções Auxiliares ---

def get_weather(city: str, api_key: str) -> dict:
    """Busca dados de clima de uma cidade usando a API OpenWeatherMap."""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "pt_br"}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200: return {"success": True, "data": response.json()}
        elif response.status_code == 404: return {"success": False, "error": "Cidade não encontrada."}
        elif response.status_code == 401: return {"success": False, "error": "Chave de API inválida."}
        else: return {"success": False, "error": f"Erro na API de clima: Código {response.status_code}"}
    except Exception as e: return {"success": False, "error": f"Não foi possível conectar à API de clima: {e}"}

def perform_google_search(query: str, num_results: int = 4):
    """Realiza uma busca no Google e retorna os resultados formatados."""
    try:
        results = list(search(query, stop=num_results, lang='pt-br'))
        if not results: 
            return "Nenhum resultado encontrado na busca."
        
        return "\n".join([f"Link: <{link}>" for link in results])
    except Exception as e:
        logging.error(f"Erro ao buscar no Google: {e}")
        return f"Ocorreu um erro ao tentar pesquisar na web: {e}"

def call_groq(prompt: str, system_message: str = None) -> str:
    """Chama a API do Groq (Substituindo o Ollama)."""
    global modo_agressivo
    
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY não encontrada no .env")
        return "Erro: API Key do Groq não configurada."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Monta a lista de mensagens
    messages = []
    
    # Se tiver mensagem de sistema (personalidade), adiciona primeiro
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    # Adiciona a mensagem do usuário
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
        logging.error(f"Erro na função call_groq: {e}")
        return ""

async def get_member(guild: discord.Guild, user_ref: str):
    """Busca um membro no servidor por ID, menção ou nome."""
    if not guild: return None
    member = None
    user_ref_cleaned = re.sub(r'[<@!>]', '', user_ref)
    if user_ref_cleaned.isdigit():
        try:
            member = guild.get_member(int(user_ref_cleaned)) or await guild.fetch_member(int(user_ref_cleaned))
        except (discord.NotFound, discord.HTTPException):
            member = None
    if member: return member
    user_lower = user_ref.lower()
    return discord.utils.find(lambda m: m.name.lower() == user_lower or m.display_name.lower() == user_lower, guild.members)

# --- Eventos do Discord ---

@client.event
async def on_ready():
    logging.info(f"✅ Bot conectado como {client.user}")
    if ALLOWED_CHANNEL_ID == 0: logging.warning("AVISO: ALLOWED_CHANNEL_ID não definido.")
    else: logging.info(f"Monitorando o canal com ID: {ALLOWED_CHANNEL_ID}")
    
    if not GROQ_API_KEY:
        logging.error("❌ CRÍTICO: GROQ_API_KEY não encontrada! O bot não vai responder.")
    else:
        logging.info("✅ GROQ_API_KEY encontrada.")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or (ALLOWED_CHANNEL_ID != 0 and message.channel.id != ALLOWED_CHANNEL_ID): return
    content = message.content.strip()
    if not content: return
    lc = content.lower()
    global modo_agressivo
    channel_id = message.channel.id

    try:
        # --- Bloco de Comandos Explícitos ---
        if lc == "modo agressivo":
            modo_agressivo = True
            await message.channel.send("⚡ **Modo agressivo ativado!**")
            return
        if lc == "modo normal":
            modo_agressivo = False
            await message.channel.send("🕊️ **Modo normal ativado.**")
            return
        if lc == "limpar memoria":
            if channel_id in conversation_history:
                conversation_history[channel_id].clear()
                await message.channel.send("🧠 **Memória da conversa neste canal foi limpa.**")
            else:
                await message.channel.send("🤔 Não há nada para limpar aqui.")
            return

        palavras_chave_clima = ["temperatura", "clima", "tempo em", "previsão para", "graus em"]
        if any(kw in lc for kw in palavras_chave_clima):
            if not OPENWEATHER_API_KEY: return await message.channel.send("❌ A função de clima não está configurada.")
            async with message.channel.typing():
                prompt_extracao = f"Da frase a seguir, extraia APENAS o nome da cidade. Responda somente com o nome da cidade, sem pontuação. Frase: '{content}'"
                # Aqui chamamos o GROQ
                cidade_extraida = await asyncio.to_thread(call_groq, prompt_extracao)
                
                if not cidade_extraida or "N/A" in cidade_extraida:
                    return await message.channel.send("🤔 Não consegui identificar uma cidade na sua pergunta.")
                
                weather_info = await asyncio.to_thread(get_weather, cidade_extraida, OPENWEATHER_API_KEY)
                if not weather_info["success"]:
                    return await message.channel.send(f"❌ Erro ao buscar clima para **{cidade_extraida}**: {weather_info['error']}")
                data = weather_info["data"]
                embed = discord.Embed(title=f"Clima em {data['name']}, {data['sys']['country']}", color=discord.Color.blue())
                embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
                embed.add_field(name="🌡️ Temperatura", value=f"{data['main']['temp']:.1f}°C", inline=True)
                embed.add_field(name="🤔 Sensação", value=f"{data['main']['feels_like']:.1f}°C", inline=True)
                embed.add_field(name="💧 Umidade", value=f"{data['main']['humidity']}%", inline=True)
                embed.add_field(name="📝 Descrição", value=data['weather'][0]['description'].capitalize(), inline=False)
                embed.set_footer(text="Dados fornecidos por DarkMoon Company")
                await message.channel.send(embed=embed)
            return

        if re.match(r'^(linguiçar)\b', lc):
            match = re.search(r'linguiçar\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `linguiçar <usuário>`")
            target_user_ref = match.group(1).strip()
            target_member = await get_member(message.guild, target_user_ref)
            if not target_member: return await message.channel.send(f"❌ Não encontrei o usuário `{target_user_ref}`.")
            await message.channel.send(f"**{target_member.display_name}** foi linguiçado com força 😂")
            return
            
        if any(kw in lc for kw in ["apagar mensagens", "limpar chat", "clear", "purge"]):
            if not message.author.guild_permissions.manage_messages: return await message.channel.send("❌ Você não tem permissão para isso.")
            limit_amount = 300
            match_amount = re.search(r'\b(\d+)\b', content)
            if match_amount:
                requested_amount = int(match_amount.group(1))
                limit_amount = max(1, min(requested_amount, 300))
            check_func = lambda m: True
            deleted = await message.channel.purge(limit=limit_amount, check=check_func)
            await message.channel.send(f"✅ Apaguei **{len(deleted)}** mensagens!", delete_after=10)
            return

        if re.match(r'^(mute|mutar)\b', lc):
            if not message.author.guild_permissions.mute_members: return await message.channel.send("❌ Você não tem permissão para isso.")
            match = re.search(r'(?:mute|mutar)\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `mute <usuário>`")
            member_to_mute = await get_member(message.guild, match.group(1).strip())
            if not member_to_mute: return await message.channel.send("❌ Usuário não encontrado.")
            await member_to_mute.edit(mute=True, reason=f"Mutado por {message.author}")
            await message.channel.send(f"✅ **{member_to_mute.display_name}** foi silenciado nos canais de voz.")
            return

        if re.match(r'^(unmute|desmutar)\b', lc):
            if not message.author.guild_permissions.mute_members: return await message.channel.send("❌ Você não tem permissão para isso.")
            match = re.search(r'(?:unmute|desmutar)\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `desmutar <usuário>`")
            member_to_unmute = await get_member(message.guild, match.group(1).strip())
            if not member_to_unmute: return await message.channel.send("❌ Usuário não encontrado.")
            if not member_to_unmute.voice or not member_to_unmute.voice.mute: return await message.channel.send(f"🤔 O usuário **{member_to_unmute.display_name}** não parece estar silenciado.")
            await member_to_unmute.edit(mute=False, reason=f"Desmutado por {message.author}")
            await message.channel.send(f"✅ **{member_to_unmute.display_name}** teve seu microfone reativado.")
            return

        if re.match(r'^(kick|kickar|kikar)\b', lc):
            if not message.author.guild_permissions.move_members: 
                return await message.channel.send("❌ Você não tem permissão para mover membros.")
            match = re.search(r'(?:kick|kickar|kikar)\s+(.+)', content, re.IGNORECASE)
            if not match: 
                return await message.channel.send("Uso: `kick <usuário>`")
            member_to_disconnect = await get_member(message.guild, match.group(1).strip())
            if not member_to_disconnect: 
                return await message.channel.send("❌ Usuário não encontrado.")
            if not member_to_disconnect.voice:
                 return await message.channel.send(f"🤔 O usuário **{member_to_disconnect.display_name}** não está em uma chamada de voz.")
            await member_to_disconnect.move_to(None, reason=f"Desconectado da call por {message.author}")
            await message.channel.send(f"🔌 **{member_to_disconnect.display_name}** foi desconectado da chamada de voz.")
            return

        if re.match(r'^(expulsar)\b', lc):
            if not message.author.guild_permissions.kick_members: 
                return await message.channel.send("❌ Você não tem permissão para isso.")
            match = re.search(r'(?:expulsar)\s+(.+)', content, re.IGNORECASE)
            if not match: 
                return await message.channel.send("Uso: `expulsar <usuário>`")
            member_to_kick = await get_member(message.guild, match.group(1).strip())
            if not member_to_kick: 
                return await message.channel.send("❌ Usuário não encontrado.")
            await member_to_kick.kick(reason=f"Expulso por {message.author}") 
            await message.channel.send(f"✅ **{member_to_kick.display_name}** foi expulso do servidor.")
            return

        if re.match(r'^(ban|banir)\b', lc):
            if not message.author.guild_permissions.ban_members: return await message.channel.send("❌ Você não tem permissão para isso.")
            match = re.search(r'(?:ban|banir)\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `ban <usuário>`")
            member_to_ban = await get_member(message.guild, match.group(1).strip())
            if not member_to_ban: return await message.channel.send("❌ Usuário não encontrado.")
            await member_to_ban.ban(reason=f"Banido por {message.author}")
            await message.channel.send(f"✅ **{member_to_ban.display_name}** foi banido permanentemente.")
            return

        # --- Se não for um comando explícito, inicia o processo de RACIOCÍNIO ---
        
        if channel_id not in conversation_history:
            conversation_history[channel_id] = deque(maxlen=HISTORY_LIMIT)
        history = conversation_history[channel_id]
        
        async with message.channel.typing():
            historico_formatado = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
            
            prompt_decisao = f"""Você é um roteador de decisão. Escolha: [KNOWLEDGE_BASE] ou [WEB_SEARCH].
Use [WEB_SEARCH] para eventos atuais, notícias, preços, clima atual, etc.
Use [KNOWLEDGE_BASE] para fatos históricos, conhecimentos gerais.
Exemplo 1: "Qual a capital da Itália?" -> FERRAMENTA: [KNOWLEDGE_BASE] | TERMO_DE_BUSCA: N/A
Exemplo 2: "preço do bitcoin?" -> FERRAMENTA: [WEB_SEARCH] | TERMO_DE_BUSCA: preço do bitcoin
Histórico: {historico_formatado}
Pergunta: "{content}"
Responda APENAS no formato: FERRAMENTA: [X] | TERMO_DE_BUSCA: [Y]"""

            # Chamada ao GROQ para decisão
            decisao_ia = await asyncio.to_thread(call_groq, prompt_decisao)
            
            search_results = None
            if "WEB_SEARCH" in decisao_ia:
                termo_de_busca = decisao_ia.split("TERMO_DE_BUSCA:")[-1].strip()
                if not termo_de_busca or termo_de_busca.lower() == 'n/a': termo_de_busca = content
                
                feedback_msg = await message.channel.send(f"🔎 Pesquisando na web sobre: **{termo_de_busca}**...")
                search_results = await asyncio.to_thread(perform_google_search, termo_de_busca)
                await feedback_msg.delete()

            agora = datetime.now()
            try:
                import locale
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                logging.warning("Locale pt_BR não encontrado, usando formatação padrão.")
                
            data_hora_formatada = agora.strftime("%A, %d de %B de %Y")
            contexto_temporal = f"Contexto Importante: A data atual é {data_hora_formatada}."
            
            prompt_sintese = f"{contexto_temporal}\n"
            
            if search_results:
                prompt_sintese += f"Use os seguintes resultados da web para formular sua resposta:\n---\n{search_results}\n---\n"
            
            prompt_sintese += "Com base no histórico e no contexto, responda à pergunta do usuário de forma natural e completa.\n"
            prompt_sintese += f"Histórico:\n{historico_formatado}\n\nPergunta do Usuário: {content}"

            system_prompt = None
            if modo_agressivo:
                system_prompt = "Aja como 'Cobra', um chatbot tóxico, ofensivo, irritado e arrogante. Use gírias e seja direto. Não peça desculpas."
                
            # Chamada Final ao GROQ
            resposta_final = await asyncio.to_thread(call_groq, prompt_sintese, system_message=system_prompt)


            if resposta_final:
                history.append({"role": "user", "content": content})
                history.append({"role": "assistant", "content": resposta_final})
            
            for i in range(0, len(resposta_final), 1990):
                await message.reply(resposta_final[i:i+1990], mention_author=False)

    except Exception as e:
        logging.exception("Ocorreu um erro não tratado no evento on_message:")
        await message.channel.send(f"🐞 Ocorreu um erro inesperado: `{e}`")

# --- Inicialização do Bot ---
if not DISCORD_TOKEN:
    logging.error("CRÍTICO: TOKEN do Disco  rd não encontrado.")
else:
    client.run(DISCORD_TOKEN)