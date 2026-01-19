import discord
import requests
import asyncio
import os
import re
import logging
import json # Adicionado para salvar pontos
import time # Adicionado para contar o tempo
from dotenv import load_dotenv
from datetime import datetime
from collections import deque
from googlesearch import search 
from discord import app_commands # --- ADICIONADO: Necessário para Slash Commands (Badge) ---

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
load_dotenv()

# --- Variáveis de Ambiente ---
DISCORD_TOKEN = os.getenv('TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# ==============================================================================
# --- CONFIGURAÇÃO DE CANAIS (EDITE AQUI PARA MUDAR OS LOCAIS) ---
# ==============================================================================

# Canal 1: Onde roda Rank, IA, Pontos, etc. (Canal Principal)
ID_CANAL_PRINCIPAL = 1447794003691962490 

# Canal 2: Onde o Carro aparece (Canal Secundário)
ID_CANAL_CARRO = 1454696650025992222

# (Opcional) Canal extra definido no arquivo .env
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '0'))

# ==============================================================================

# --- Intents do Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True # --- IMPORTANTE: Ativado para rastrear call ---
intents.invites = True      # --- ADICIONADO: Ativado para rastrear convites ---
client = discord.Client(intents=intents)

# --- ADICIONADO: Árvore de Comandos para a Badge ---
tree = app_commands.CommandTree(client)

# --- Estado Global ---
modo_agressivo = False
conversation_history = {}
HISTORY_LIMIT = 32
carro_task = None # Variável para controlar o loop do carro

# --- SISTEMA DE PONTOS DE VOZ (CALL) ---
VOICE_POINTS_FILE = "voice_points.json"
voice_join_times = {}       # Armazena temporariamente a hora que entrou na call
voice_pending_seconds = {}  # Armazena segundos acumulados (memória)
invites_cache = {}          # --- ADICIONADO: Cache dos convites ---

def load_points():
    if not os.path.exists(VOICE_POINTS_FILE):
        return {}
    try:
        with open(VOICE_POINTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_points(data):
    with open(VOICE_POINTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Carrega os pontos na memória ao iniciar
user_points = load_points()

# --- NOVA FUNÇÃO: ATUALIZAR EM TEMPO REAL ---
def update_current_voice_sessions():
    """Calcula os pontos de quem está na call AGORA sem precisar sair"""
    current_time = time.time()
    # Copia a lista de chaves para não dar erro de iteração
    active_users = list(voice_join_times.keys())
    
    for user_id in active_users:
        start_time = voice_join_times[user_id]
        session_seconds = current_time - start_time
        
        # Reinicia o contador para o momento atual (para não contar dobrado depois)
        voice_join_times[user_id] = current_time
        
        # Soma ao banco de pendência
        total_seconds = voice_pending_seconds.get(user_id, 0) + session_seconds
        
        # Calcula pontos (1 a cada 900s/15min)
        points_to_add = int(total_seconds // 900)
        remainder_seconds = total_seconds % 900
        
        voice_pending_seconds[user_id] = remainder_seconds
        
        if points_to_add > 0:
            if user_id not in user_points: user_points[user_id] = 0
            user_points[user_id] += points_to_add
    
    # Salva tudo
    save_points(user_points)

# --- CLASSE DO BOTÃO DO CARRO DA ALT ---
class CarroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Sem timeout, o botão fica até encher
        self.winners = [] # Lista de quem já clicou

    @discord.ui.button(label="PEGAR 🚗", style=discord.ButtonStyle.success, custom_id="carro_alt_pegar")
    async def pegar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        # Verifica se já pegou
        if user_id in self.winners:
            # Mensagem de erro continua privada pra não flodar o chat
            return await interaction.response.send_message("❌ Você já pegou sua recompensa neste carro!", ephemeral=True)

        # Adiciona na lista de vencedores
        self.winners.append(user_id)
        position = len(self.winners)
        points_to_give = 0

        # Lógica de Pontos
        if position == 1:
            points_to_give = 50
        elif 2 <= position <= 4:
            points_to_give = 25
        elif 5 <= position <= 6:
            points_to_give = 15
        else:
            # Se chegou aqui é pq clicou simultaneamente mas já encheu
            return await interaction.response.send_message("🏁 O carro já lotou! Mais sorte na próxima.", ephemeral=True)

        # Adiciona os pontos
        if user_id not in user_points: user_points[user_id] = 0
        user_points[user_id] += points_to_give
        save_points(user_points)

        # --- ATUALIZA A MENSAGEM DO CARRO COM A LISTA ---
        embed = interaction.message.embeds[0]
        
        # Formata a nova linha da lista
        new_entry = f"**{position}.** {user_name} — **{points_to_give} pts**"
        
        # Procura se já tem o campo de lista, se não, cria
        found_field = False
        for i, field in enumerate(embed.fields):
            if field.name == "🏆 Quem já pegou:":
                # Adiciona o novo ganhador na lista existente
                new_value = field.value + "\n" + new_entry
                embed.set_field_at(i, name="🏆 Quem já pegou:", value=new_value, inline=False)
                found_field = True
                break
        
        if not found_field:
            embed.add_field(name="🏆 Quem já pegou:", value=new_entry, inline=False)

        # Verifica se encheu (6 pessoas)
        if len(self.winners) >= 6:
            button.label = "CARRO CHEIO 🚫"
            button.style = discord.ButtonStyle.secondary
            button.disabled = True
            embed.set_footer(text="The ALT System • CARRO LOTADO")
            self.stop()
        
        # Edita a mensagem original (Isso todos veem)
        await interaction.message.edit(embed=embed, view=self)
        
        # Manda a mensagem de confirmação PÚBLICA (ephemeral=False)
        await interaction.response.send_message(f"🚗 **VRUM!** {interaction.user.mention} pegou a vaga **#{position}** e ganhou **{points_to_give}** pontos!", ephemeral=False)

# --- FUNÇÃO PARA GERAR O CARRO ---
async def spawn_carro_func(channel):
    hora_atual = datetime.now().strftime("%H:%M")
    embed = discord.Embed(
        title="🚗 O CARRO DA ALT PASSOU!",
        description=f"**Horário:** {hora_atual}\n\nClique rápido em **PEGAR** para ganhar pontos!\n\n"
                    "🥇 **1º Lugar:** 50 Pontos\n"
                    "🥈 **2º ao 4º:** 25 Pontos\n"
                    "🥉 **5º ao 6º:** 15 Pontos",
        color=discord.Color.gold()
    )
    # --- ALTERADO: Texto do rodapé para 4h ---
    embed.set_footer(text="The ALT System • Proximo em 4h")
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3097/3097180.png") # Icone de carro generico
    
    view = CarroView()
    await channel.send(embed=embed, view=view)

# --- LOOP AUTOMÁTICO DO CARRO ---
async def carro_background_loop():
    await client.wait_until_ready()
    # --- ALTERADO: Usa o ID_CANAL_CARRO ---
    channel = client.get_channel(ID_CANAL_CARRO)
    
    # Se não achar o canal especifico, avisa.
    if not channel:
        logging.warning(f"⚠️ Não consegui encontrar o ID_CANAL_CARRO ({ID_CANAL_CARRO}) para enviar o Carro.")
        return

    while not client.is_closed():
        await spawn_carro_func(channel)
        # --- ALTERADO: 4 horas = 4 * 60 * 60 = 14400 segundos ---
        await asyncio.sleep(14400) 

# --- Texto das Regras (Formatado) ---
REGRAS_MSG = """
🛡️ **Seja bem-vindo(a) ao Servidor ALT**

As regras de um servidor são comuns a todos, principalmente as próprias diretrizes do Discord, mas cada servidor destaca regras essenciais que devem ser seguidas.
Para manter relações acolhedoras, siga todas as regras abaixo.

**🤝 Regras de comportamento:**
▫️ Respeite os Termos de Serviço do Discord!
▫️ Respeite as Diretrizes da Comunidade;
▫️ Respeite todos os membros do servidor;
▫️ Não pratique nenhum tipo de divulgação sem ter permissão;
▫️ Evite marcações desnecessárias;

**🚫 Proibições em Canais de Texto:**
▫️ Racismo, homofobia, xenofobia;
▫️ Flood e/ou spam;
▫️ Comércio dentro do servidor;
▫️ Divulgação, seja nos chats ou no pv;
▫️ Explanação;
▫️ Compartilhamento de conteúdo explícito (NSFW, gore);

**🔇 Proibições em canais de voz:**
▫️ Racismo, homofobia, xenofobia;
▫️ Gritar, assoprar ou colocar áudios estourados;
▫️ Explanar outros membros em call;
▫️ Transmissão de pornografia, gore e entre outros;
"""

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
    """Chama a API do Groq."""
    global modo_agressivo
    
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY não encontrada no .env")
        return "Erro: API Key do Groq não configurada."

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

# --- COMANDO SLASH PARA A BADGE (INSÍGNIA) ---
@tree.command(name="badge", description="Execute este comando para contar para a Insígnia de Desenvolvedor")
async def badge_command(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Comando registrado com sucesso! Aguarde até 24h e verifique o Portal do Desenvolvedor para resgatar sua Insígnia.")

# --- COMANDO SLASH PARA FORÇAR O CARRO ---
@tree.command(name="carro", description="Força o Carro da ALT a aparecer e reinicia o timer de 4h") # -- Descrição atualizada
@app_commands.checks.has_permissions(administrator=True)
async def carro_force_command(interaction: discord.Interaction):
    global carro_task
    
    # --- ALTERADO: Usa o canal específico do CARRO ---
    channel = client.get_channel(ID_CANAL_CARRO)
        
    if not channel:
        return await interaction.response.send_message("❌ Erro: Não achei o canal para enviar o carro.", ephemeral=True)

    await interaction.response.send_message("✅ Carro da ALT forçado! O timer automático foi reiniciado.", ephemeral=True)
    
    # Cancela o loop atual para reiniciar o timer
    if carro_task:
        carro_task.cancel()
    
    # Envia o carro imediatamente
    await spawn_carro_func(channel)
    
    # Reinicia o loop (que vai esperar 4h para o próximo)
    carro_task = client.loop.create_task(carro_loop_with_delay())

async def carro_loop_with_delay():
    # Helper para esperar 4h ANTES de enviar o proximo (usado no force)
    # --- ALTERADO: 4 horas = 14400 segundos ---
    await asyncio.sleep(14400)
    # Depois volta pro loop normal que envia e depois espera
    await carro_background_loop()

# --- Eventos do Discord ---

@client.event
async def on_ready():
    global carro_task
    # --- Sincroniza os comandos slash (/badge e /carro) ---
    await tree.sync()
    logging.info("✅ Slash Commands sincronizados! Use /badge e /carro.")
    
    logging.info(f"✅ Bot conectado como {client.user} (The ALT)")
    
    # --- Inicia o loop automático do Carro ---
    if carro_task is None:
        carro_task = client.loop.create_task(carro_background_loop())
        logging.info("🚗 Loop do Carro da ALT iniciado (4 em 4 horas).")
    
    # --- ADICIONADO: Cache de convites ao iniciar o bot ---
    for guild in client.guilds:
        # --- FILTRO: Ignora qualquer servidor que não seja o 'ALT' ---
        if guild.name != "ALT":
            continue

        try:
            current_invites = await guild.invites()
            invites_cache[guild.id] = {invite.code: invite.uses for invite in current_invites}
            logging.info(f"📨 Cache de convites carregado para: {guild.name}")
        except Exception as e:
            logging.warning(f"⚠️ Não consegui carregar convites de {guild.name}: {e}")
            
    if ALLOWED_CHANNEL_ID == 0: logging.warning("AVISO: ALLOWED_CHANNEL_ID não definido.")
    else: logging.info(f"Monitorando o canal com ID: {ALLOWED_CHANNEL_ID}")
    
    if not GROQ_API_KEY:
        logging.error("❌ CRÍTICO: GROQ_API_KEY não encontrada! O bot não vai responder.")
    else:
        logging.info("✅ GROQ_API_KEY encontrada.")

# --- SISTEMA DE BOAS VINDAS ---
@client.event
async def on_member_join(member):
    # --- FILTRO: Ignora se não for no servidor ALT ---
    if member.guild.name != "ALT":
        return

    # --- ADICIONADO: Lógica de Pontos por Convite (Invite Tracker) ---
    inviter_user = None
    try:
        # Pega a lista nova de convites
        new_invites = await member.guild.invites()
        # Pega a lista antiga do cache
        old_invites = invites_cache.get(member.guild.id, {})
        
        for invite in new_invites:
            # Se o uso desse convite aumentou em relação ao cache
            if invite.uses > old_invites.get(invite.code, 0):
                inviter_user = invite.inviter
                if inviter_user and not inviter_user.bot:
                    inviter_id = str(inviter_user.id)
                    
                    # Adiciona 1 ponto
                    if inviter_id not in user_points: user_points[inviter_id] = 0
                    user_points[inviter_id] += 1
                    save_points(user_points)
                    
                    logging.info(f"📨 {inviter_user.name} convidou {member.name} e ganhou +1 ponto!")
                break
        
        # Atualiza o cache com os dados novos
        invites_cache[member.guild.id] = {i.code: i.uses for i in new_invites}
    except Exception as e:
        logging.error(f"Erro no sistema de convites: {e}")

    # -----------------------------------------------------------
    # ATENÇÃO: COLOQUE AQUI O ID DO CANAL DE BOAS VINDAS:
    canal_boas_vindas_id = 1450883550550294750  # <--- SEU ID JÁ CONFIGURADO
    # -----------------------------------------------------------
    
    channel = client.get_channel(canal_boas_vindas_id)
    
    # Se não achar pelo ID fixo, tenta pelo ID do .env como fallback
    if not channel and ALLOWED_CHANNEL_ID != 0:
        channel = client.get_channel(ALLOWED_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title=f"Bem-vindo(a) a **ALT!**",
            description=f"Bem-vindo(a), {member.mention}, a **ALT!**\n\nFique à vontade para explorar o servidor.\nQualquer dúvida, estamos por aqui. Aproveite!",
            color=discord.Color.red()
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        elif member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
            
        footer_text = f"Membro nº {len(member.guild.members)} | The ALT System"
        
        # Se achou quem convidou, mostra no footer
        if inviter_user:
            footer_text += f" | Convidado por: {inviter_user.display_name}"
            
        embed.set_footer(text=footer_text)
        await channel.send(embed=embed)

# --- LÓGICA DE CONTAR PONTOS NA CALL (SÓ DESMUTADO) ---
@client.event
async def on_voice_state_update(member, before, after):
    if member.bot: return
    
    # --- FILTRO: Ignora se não for no servidor ALT ---
    if member.guild.name != "ALT":
        return

    user_id = str(member.id)
    
    # Verifica se o usuário pode falar (Não mutado, não surdo e NÃO SUPRESSO/push-to-talk forced)
    is_talking_allowed = not after.self_mute and not after.mute and not after.suppress
    
    # 1. PARAR DE CONTAR: Se saiu da call OU se mutou
    if user_id in voice_join_times:
        has_left_channel = after.channel is None
        is_now_muted = not is_talking_allowed
        
        if has_left_channel or is_now_muted:
            start_time = voice_join_times.pop(user_id)
            session_seconds = time.time() - start_time
            
            # Soma com o que estava pendente
            total_seconds = voice_pending_seconds.get(user_id, 0) + session_seconds
            
            # Calcula quantos pontos inteiros (1 ponto a cada 15 min = 900s)
            points_to_add = int(total_seconds // 900)
            
            # O que sobrar volta pro banco
            remainder_seconds = total_seconds % 900
            voice_pending_seconds[user_id] = remainder_seconds
            
            if points_to_add > 0:
                if user_id not in user_points: user_points[user_id] = 0
                user_points[user_id] += points_to_add
                save_points(user_points)
                logging.info(f"💾 {member.name} ganhou {points_to_add} pontos (Acumulou tempo).")
            else:
                logging.info(f"⏱️ {member.name} acumulou {int(total_seconds/60)} min (ainda sem novo ponto).")

    # 2. COMEÇAR A CONTAR: Se entrou na call E está desmutado/ativo
    if after.channel is not None and is_talking_allowed:
        # Só começa se já não estiver contando
        if user_id not in voice_join_times:
            voice_join_times[user_id] = time.time()
            logging.info(f"🎙️ {member.name} começou a contar pontos (Desmutado/Ativo).")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    if message.guild and message.guild.name != "ALT": return
    
    # ==============================================================================
    # --- CONFIGURAÇÃO DE PERMISSÕES POR CANAL ---
    # Aqui definimos o que funciona em qual lugar.
    # ==============================================================================
    
    # Lista de canais onde funciona RANK e PONTOS e IA
    canais_rank_ia = [ID_CANAL_PRINCIPAL]
    
    # Lista de canais onde funciona LINGUIÇAR e CLIMA (Funciona nos dois)
    canais_fun = [ID_CANAL_PRINCIPAL, ID_CANAL_CARRO]
    
    # Adiciona o canal do .env se existir
    if ALLOWED_CHANNEL_ID != 0:
        canais_rank_ia.append(ALLOWED_CHANNEL_ID)
        canais_fun.append(ALLOWED_CHANNEL_ID)

    # ------------------------------------------------------------------------------

    content = message.content.strip()
    if not content: return
    lc = content.lower()
    global modo_agressivo
    channel_id = message.channel.id

    # --- DEFINIÇÃO DE GRUPOS DE COMANDOS ---
    triggers_points = ["pontos", "points", "meus pontos", "tempo call", "stats", "meu tempo"]
    triggers_rank = ["rank", "ranking", "classificação", "classificacao", "top call", "top 10"]
    palavras_chave_clima = ["temperatura", "clima", "tempo em", "previsão para", "graus em"]
    
    is_linguicar = bool(re.match(r'^(linguiçar)\b', lc))
    is_climate = any(kw in lc for kw in palavras_chave_clima)
    is_rank_or_points = (
        any(trig == lc for trig in triggers_points) or 
        any(trig in lc for trig in triggers_rank) or 
        (lc == "zerar pontos" or lc == "zerar ranking")
    )

    # ==============================================================================
    # --- LÓGICA DE ROTEAMENTO (ROUTING) ---
    # Verifica se o comando pode ser usado no canal atual
    # ==============================================================================

    # 1. Se for comando de RANK ou PONTOS -> Só no CANAL PRINCIPAL
    if is_rank_or_points:
        if channel_id not in canais_rank_ia:
            return # Ignora se não for no canal certo

    # 2. Se for LINGUIÇAR ou CLIMA -> Nos DOIS CANAIS (Principal e Carro)
    elif is_linguicar or is_climate:
        if channel_id not in canais_fun:
            return # Ignora se não for num dos canais permitidos

    # 3. Se não for nenhum comando acima (ou seja, conversa com IA ou comandos gerais)
    else:
        # A IA só deve responder no CANAL PRINCIPAL (para não atrapalhar o jogo do carro)
        if channel_id not in canais_rank_ia:
            return

    # ==============================================================================
    
    try:
        # --- NOVO COMANDO: ZERAR PONTOS (ADMIN) ---
        if lc == "zerar pontos" or lc == "zerar ranking":
            if not message.author.guild_permissions.administrator:
                return await message.channel.send("❌ Apenas administradores podem zerar os pontos.")
            
            user_points.clear()
            voice_pending_seconds.clear()
            
            # Reinicia o timer de quem está na call agora para evitar bugs
            current_t = time.time()
            for uid in voice_join_times:
                voice_join_times[uid] = current_t
                
            save_points(user_points) # Salva vazio
            await message.channel.send("🧹 **O Ranking de pontos de voz foi ZERADO com sucesso!**")
            return

        # --- VERIFICAR MEUS PONTOS (NO PV) ---
        if any(trig == lc for trig in triggers_points):
            # ATUALIZA EM TEMPO REAL ANTES DE MOSTRAR
            update_current_voice_sessions()
            
            user_id = str(message.author.id)
            total_points = user_points.get(user_id, 0)
            current_seconds = voice_pending_seconds.get(user_id, 0)
            
            # Se a pessoa estiver online na call agora, soma o tempo da sessão atual
            if user_id in voice_join_times:
                session_time = time.time() - voice_join_times[user_id]
                current_seconds += session_time

            total_minutes_accumulated = int(current_seconds // 60)
            # 15 minutos
            minutes_needed = 15 - (total_minutes_accumulated % 15)
            
            response_dm = (
                f"📊 **Seus Status no Servidor ALT**\n\n"
                f"🏆 **Pontos Totais:** {total_points}\n"
                f"⏱️ **Tempo Ativo (Desmutado):** {total_minutes_accumulated} minutos acumulados\n"
                f"⏳ **Próximo ponto em:** {minutes_needed} minutos\n\n"
                f"*Continue ativo nas calls para subir no Ranking!*"
            )
            
            try:
                await message.author.send(response_dm)
                await message.reply("📩 Mandei seus status no seu privado!")
            except discord.Forbidden:
                await message.reply("❌ Sua DM está fechada, não consegui te enviar os pontos.")
            return

        # --- COMANDO DE RANKING DE CALL (TOP 10 + CLASSIFICAÇÃO PESSOAL) ---
        if any(trig in lc for trig in triggers_rank):
            # ATUALIZA EM TEMPO REAL ANTES DE MOSTRAR
            update_current_voice_sessions()
            
            if not user_points:
                return await message.channel.send("📊 Ainda não há dados de ranking de voz (ninguém pontuou ainda).")
            
            # Ordena do maior para o menor
            sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
            # PEGA O TOP 10
            top_10 = sorted_users[:10]
            
            # Cor Dourada (RGB)
            embed = discord.Embed(title="〔 🏆 〕Membros em Destaque", color=discord.Color.from_rgb(255, 215, 0))
            
            # HEADER DA DESCRIÇÃO
            description_text = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "​Regra: 1 AltPoint a cada 15 minutos de interação.\n"
                "O tempo é acumulativo. O bot preserva seu progresso ao mutar.\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🎖**Top 10 Membros — Microfone Ativo**\n\n"
            )
            
            for i, (uid, points) in enumerate(top_10):
                membro = message.guild.get_member(int(uid))
                nome = membro.display_name if membro else f"Desconhecido ({uid})"
                
                # Definição dos ícones por posição
                if i == 0: emoji = "🥇"
                elif i == 1: emoji = "🥈"
                elif i == 2: emoji = "🥉"
                elif i == 3 or i == 4: emoji = "🏅"
                else: emoji = "⭐️"
                
                description_text += f"{emoji}- {nome} — {points} AltPoints\n"
            
            # --- CALCULAR CLASSIFICAÇÃO PESSOAL DO USUÁRIO ---
            user_id = str(message.author.id)
            my_points = user_points.get(user_id, 0)
            pending = voice_pending_seconds.get(user_id, 0)
            
            # Se estiver na call agora, soma o tempo visualmente
            if user_id in voice_join_times:
                pending += (time.time() - voice_join_times[user_id])

            min_pending = int(pending // 60)
            
            # Encontra a posição no ranking completo
            try:
                ranked_ids = [u[0] for u in sorted_users]
                my_rank_pos = ranked_ids.index(user_id) + 1
                rank_str = f"{my_rank_pos}º"
            except ValueError:
                rank_str = "Sem classificação"

            # RODAPÉ COM STATUS EM NEGRITO (Dentro da descrição)
            description_text += (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "**🎖Status Atual:**\n"
                f"**Posição: {rank_str}  | AltPoints: {my_points}  | Acumulado: {min_pending} min**"
            )
            
            embed.description = description_text
            embed.set_footer(text="The ALT System")
            
            await message.channel.send(embed=embed)
            return

        # --- COMANDO DE REGRAS NO PRIVADO ---
        triggers_regras = ["regras", "quais são as regras", "me de as regras", "ler as regras"]
        if any(trigger in lc for trigger in triggers_regras):
            try:
                await message.author.send(REGRAS_MSG)
                await message.reply("📩 Enviei as regras do servidor no seu privado! Dá uma olhada lá.")
            except discord.Forbidden:
                await message.reply("❌ Tentei te enviar as regras no privado, mas sua DM está fechada.")
            return

        # --- MODOS E CONFIG ---
        if lc == "modo agressivo":
            modo_agressivo = True
            await message.channel.send("⚡ **Modo agressivo ativado! The ALT não está para brincadeira.**")
            return
        if lc == "modo normal":
            modo_agressivo = False
            await message.channel.send("🕊️ **Modo normal ativado.**")
            return
        if lc == "limpar memoria":
            if channel_id in conversation_history:
                conversation_history[channel_id].clear()
                await message.channel.send("🧠 **Memória limpa.**")
            else:
                await message.channel.send("🤔 Nada para limpar.")
            return

        # --- FERRAMENTAS EXTRAS ---
        if re.match(r'^(imaginar|desenhar)\b', lc):
            match = re.search(r'(?:imaginar|desenhar)\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `imaginar <descrição>`")
            prompt_img = match.group(1).strip()
            await message.channel.send(f"🎨 **The ALT** está criando: **{prompt_img}**...")
            image_url = f"https://image.pollinations.ai/prompt/{prompt_img.replace(' ', '%20')}"
            embed = discord.Embed(title="Imagem Gerada", color=discord.Color.dark_purple())
            embed.set_image(url=image_url)
            embed.set_footer(text="Gerado por The ALT")
            await message.channel.send(embed=embed)
            return

        if lc == "serverinfo" or lc == "info servidor":
            guild = message.guild
            embed = discord.Embed(title=f"📊 Informações de {guild.name}", color=discord.Color.dark_teal())
            if guild.icon: embed.set_thumbnail(url=guild.icon.url)
            embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
            embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
            embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
            await message.channel.send(embed=embed)
            return

        if re.match(r'^(traduzir)\b', lc):
            match = re.search(r'traduzir\s+(.+)', content, re.IGNORECASE)
            if not match: return await message.channel.send("Uso: `traduzir <texto>`")
            texto = match.group(1).strip()
            async with message.channel.typing():
                traducao = await asyncio.to_thread(call_groq, f"Traduza para Portugues (ou para Inglês se já for PT): '{texto}'")
                await message.reply(f"🔄 **Tradução:**\n{traducao}")
            return

        # --- CLIMA ---
        # (A lista 'palavras_chave_clima' já foi definida acima)
        if any(kw in lc for kw in palavras_chave_clima):
            if not OPENWEATHER_API_KEY: return await message.channel.send("❌ Clima não configurado.")
            async with message.channel.typing():
                cidade = await asyncio.to_thread(call_groq, f"Extraia APENAS o nome da cidade: '{content}'")
                if not cidade or "N/A" in cidade: return await message.channel.send("🤔 Não entendi a cidade.")
                
                weather = await asyncio.to_thread(get_weather, cidade, OPENWEATHER_API_KEY)
                if not weather["success"]: return await message.channel.send(f"❌ Erro: {weather['error']}")
                
                data = weather["data"]
                embed = discord.Embed(title=f"Clima em {data['name']}", color=discord.Color.blue())
                embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
                embed.add_field(name="🌡️ Temp", value=f"{data['main']['temp']:.1f}°C", inline=True)
                embed.add_field(name="💧 Umidade", value=f"{data['main']['humidity']}%", inline=True)
                embed.add_field(name="📝 Descrição", value=data['weather'][0]['description'].capitalize(), inline=False)
                embed.set_footer(text="Dados fornecidos por The ALT")
                await message.channel.send(embed=embed)
            return

        # --- MODERAÇÃO ---
        if re.match(r'^(linguiçar)\b', lc):
            match = re.search(r'linguiçar\s+(.+)', content, re.IGNORECASE)
            if match:
                target = await get_member(message.guild, match.group(1).strip())
                if target: await message.channel.send(f"**{target.display_name}** foi linguiçado com força pela **ALT**! 😂")
            return
            
        if any(kw in lc for kw in ["apagar mensagens", "limpar chat", "clear", "purge"]):
            if not message.author.guild_permissions.manage_messages: return await message.channel.send("❌ Sem permissão.")
            limit = 300
            match = re.search(r'\b(\d+)\b', content)
            if match: limit = max(1, min(int(match.group(1)), 300))
            deleted = await message.channel.purge(limit=limit)
            await message.channel.send(f"✅ **The ALT** apagou **{len(deleted)}** mensagens!", delete_after=5)
            return

        if re.match(r'^(mute|mutar)\b', lc):
            if not message.author.guild_permissions.mute_members: return await message.channel.send("❌ Sem permissão.")
            match = re.search(r'(?:mute|mutar)\s+(.+)', content, re.IGNORECASE)
            if match:
                target = await get_member(message.guild, match.group(1).strip())
                if target:
                    await target.edit(mute=True)
                    await message.channel.send(f"✅ **{target.display_name}** silenciado.")
            return

        if re.match(r'^(unmute|desmutar)\b', lc):
            if not message.author.guild_permissions.mute_members: return await message.channel.send("❌ Sem permissão.")
            match = re.search(r'(?:unmute|desmutar)\s+(.+)', content, re.IGNORECASE)
            if match:
                target = await get_member(message.guild, match.group(1).strip())
                if target:
                    await target.edit(mute=False)
                    await message.channel.send(f"✅ **{target.display_name}** liberado.")
            return

        if re.match(r'^(kick|kickar)\b', lc):
            if not message.author.guild_permissions.move_members: return await message.channel.send("❌ Sem permissão.")
            match = re.search(r'(?:kick|kickar)\s+(.+)', content, re.IGNORECASE)
            if match:
                target = await get_member(message.guild, match.group(1).strip())
                if target and target.voice:
                    await target.move_to(None)
                    await message.channel.send(f"🔌 **{target.display_name}** desconectado.")
            return

        if re.match(r'^(ban|banir)\b', lc):
            if not message.author.guild_permissions.ban_members: return await message.channel.send("❌ Sem permissão.")
            match = re.search(r'(?:ban|banir)\s+(.+)', content, re.IGNORECASE)
            if match:
                target = await get_member(message.guild, match.group(1).strip())
                if target:
                    await target.ban(reason=f"Banido por {message.author}")
                    await message.channel.send(f"🚫 **{target.display_name}** foi banido pelo The ALT.")
            return

        # --- INTELIGÊNCIA ARTIFICIAL (Raciocínio) ---
        
        if channel_id not in conversation_history:
            conversation_history[channel_id] = deque(maxlen=HISTORY_LIMIT)
        history = conversation_history[channel_id]
        
        async with message.channel.typing():
            historico_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
            
            prompt_decisao = f"""Você é o bot 'The ALT'. Escolha: [KNOWLEDGE_BASE] ou [WEB_SEARCH].
[WEB_SEARCH]: para notícias, clima atual, preços.
[KNOWLEDGE_BASE]: para conversa, história, código.
Histórico: {historico_str}
Pergunta: "{content}"
Responda APENAS: FERRAMENTA: [X] | TERMO_DE_BUSCA: [Y]"""

            decisao = await asyncio.to_thread(call_groq, prompt_decisao)
            
            search_res = None
            if "WEB_SEARCH" in decisao:
                termo = decisao.split("TERMO_DE_BUSCA:")[-1].strip()
                if not termo or 'n/a' in termo.lower(): termo = content
                feedback = await message.channel.send(f"🔎 **The ALT** pesquisando: **{termo}**...")
                search_res = await asyncio.to_thread(perform_google_search, termo)
                await feedback.delete()

            data_hj = datetime.now().strftime("%d/%m/%Y")
            prompt_final = f"Data atual: {data_hj}. Você é 'The ALT', um assistente avançado.\n"
            
            if search_res:
                prompt_final += f"Dados da web:\n{search_res}\n"
            
            prompt_final += f"Histórico:\n{historico_str}\nUsuário: {content}"

            sys_msg = "Você é 'The ALT'. Responda de forma útil e inteligente."
            if modo_agressivo:
                sys_msg = "Você é o 'Cobra'. Seja tóxico e agressivo."

            resposta = await asyncio.to_thread(call_groq, prompt_final, system_message=sys_msg)

            if resposta:
                history.append({"role": "user", "content": content})
                history.append({"role": "assistant", "content": resposta})
                for i in range(0, len(resposta), 1990):
                    await message.reply(resposta[i:i+1990], mention_author=False)

    except Exception as e:
        logging.exception("Erro no on_message:")
        await message.channel.send(f"🐞 Erro no sistema The ALT: `{e}`")

if not DISCORD_TOKEN:
    logging.error("CRÍTICO: TOKEN do Discord não encontrado.")
else:
    client.run(DISCORD_TOKEN)