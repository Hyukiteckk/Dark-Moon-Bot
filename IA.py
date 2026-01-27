"""
🤖 Dark Moon - Bot Discord Multi-funcionalidades
Gerenciador de Pontos de Voz, IA, Clima e muito mais!

ESTRUTURA MODULAR - Cada comando é um arquivo separado
"""

import discord
import asyncio
import os
import logging
import time
from dotenv import load_dotenv
from discord import app_commands

# ═══════════════════════════════════════════════════════════════════════════════
# 📥 IMPORTS DOS MÓDULOS
# ═══════════════════════════════════════════════════════════════════════════════

from commands.pontos import setup_pontos_commands
from commands.moderacao import setup_moderacao_commands
from commands.imagens import setup_imagens_commands
from commands.clima import setup_clima_commands
from commands.ia import setup_ia_commands
from commands.carro import carro_background_loop, carro_loop_with_delay, spawn_carro_func

from utils import (
    start_voice_session, stop_voice_session, load_points, voice_join_times,
    invites_cache
)

# ═══════════════════════════════════════════════════════════════════════════════
# ✅ CONFIGURAÇÃO INICIAL
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
load_dotenv()

# Variáveis de Ambiente
DISCORD_TOKEN = os.getenv('TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
PUBLIC_KEY = os.getenv('PUBLIC_KEY')

# Configuração de Canais
ID_CANAL_PRINCIPAL = 1447794003691962490
ID_CANAL_CARRO = 1454696650025992222
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '0'))

# Discord Client Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.invites = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Estado Global
carro_task = None

# Carrega pontos ao iniciar
load_points()

# ═══════════════════════════════════════════════════════════════════════════════
# 💬 MENSAGENS
# ═══════════════════════════════════════════════════════════════════════════════

REGRAS_MSG = """
🛡️ **Seja bem-vindo(a) ao Servidor Dark Moon**

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

# ═══════════════════════════════════════════════════════════════════════════════
# ⚡ SLASH COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@tree.command(name="badge", description="Registra para obter Insígnia de Desenvolvedor")
async def badge_command(interaction: discord.Interaction):
    """Comando slash para registrar insígnia."""
    await interaction.response.send_message(
        "✅ Comando registrado com sucesso! Aguarde até 24h e verifique o Portal do Desenvolvedor."
    )

@tree.command(name="carro", description="Força o Carro da Dark Moon a aparecer (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def carro_force_command(interaction: discord.Interaction):
    """Comando slash para forçar spawn do carro."""
    global carro_task
    
    channel = client.get_channel(ID_CANAL_CARRO)
    
    if not channel:
        return await interaction.response.send_message(
            "❌ Erro: Não achei o canal para enviar o carro.",
            ephemeral=True
        )

    await interaction.response.send_message(
        "✅ Carro da Dark Moon forçado! O timer automático foi reiniciado.",
        ephemeral=True
    )
    
    if carro_task:
        carro_task.cancel()
    
    await spawn_carro_func(channel, ID_CANAL_CARRO)
    carro_task = client.loop.create_task(carro_loop_with_delay(client, ID_CANAL_CARRO))

# ═══════════════════════════════════════════════════════════════════════════════
# 📡 EVENT HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@client.event
async def on_ready():
    """Evento acionado quando o bot conecta ao Discord."""
    global carro_task
    
    await tree.sync()
    logging.info("✅ Slash Commands sincronizados!")
    logging.info(f"✅ Bot conectado como {client.user}")
    
    if carro_task is None:
        carro_task = client.loop.create_task(carro_background_loop(client, ID_CANAL_CARRO))
        logging.info("🚗 Loop do Carro iniciado (4 em 4 horas).")
    
    # Carrega cache de convites
    for guild in client.guilds:
        if guild.name != "Dark Moon":
            continue
        try:
            current_invites = await guild.invites()
            invites_cache[guild.id] = {invite.code: invite.uses for invite in current_invites}
            logging.info(f"📨 Cache de convites carregado: {guild.name}")
        except Exception as e:
            logging.warning(f"⚠️ Erro ao carregar convites: {e}")
    
    if ALLOWED_CHANNEL_ID == 0:
        logging.warning("⚠️ ALLOWED_CHANNEL_ID não definido.")
    else:
        logging.info(f"✅ Monitorando canal: {ALLOWED_CHANNEL_ID}")

@client.event
async def on_member_join(member):
    """Evento acionado quando um membro entra no servidor."""
    if member.guild.name != "Dark Moon":
        return

    from utils import add_user_points
    
    inviter_user = None
    try:
        new_invites = await member.guild.invites()
        old_invites = invites_cache.get(member.guild.id, {})
        
        for invite in new_invites:
            if invite.uses > old_invites.get(invite.code, 0):
                inviter_user = invite.inviter
                if inviter_user and not inviter_user.bot:
                    add_user_points(str(inviter_user.id), 1)
                    logging.info(f"📨 {inviter_user.name} convidou {member.name} (+1 ponto)")
                break
        
        invites_cache[member.guild.id] = {i.code: i.uses for i in new_invites}
    except Exception as e:
        logging.error(f"❌ Erro no tracker de convites: {e}")

    canal_boas_vindas_id = 1450883550550294750
    channel = client.get_channel(canal_boas_vindas_id)
    
    if not channel and ALLOWED_CHANNEL_ID != 0:
        channel = client.get_channel(ALLOWED_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title="Bem-vindo(a) a **Dark Moon!**",
            description=(
                f"Bem-vindo(a), {member.mention}, a **Dark Moon!**\n\n"
                "Fique à vontade para explorar o servidor.\n"
                "Qualquer dúvida, estamos por aqui. Aproveite!"
            ),
            color=discord.Color.red()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        elif member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        
        footer_text = f"Membro nº {len(member.guild.members)} | Dark Moon System"
        if inviter_user:
            footer_text += f" | Convidado por: {inviter_user.display_name}"
        
        embed.set_footer(text=footer_text)
        await channel.send(embed=embed)

@client.event
async def on_voice_state_update(member, before, after):
    """Evento acionado quando usuário muda status de voz."""
    if member.bot:
        return
    
    if member.guild.name != "Dark Moon":
        return

    user_id = str(member.id)
    is_talking_allowed = not after.self_mute and not after.mute and not after.suppress
    
    # Para de contar se saiu ou mutou
    if user_id in voice_join_times:
        has_left = after.channel is None
        is_now_muted = not is_talking_allowed
        
        if has_left or is_now_muted:
            stop_voice_session(user_id)
    
    # Começa a contar se entrou e está desmutado
    if after.channel is not None and is_talking_allowed:
        start_voice_session(user_id)

# ═══════════════════════════════════════════════════════════════════════════════
# 📨 MAIN MESSAGE EVENT HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

async def route_command(message: discord.Message, channel_id: int) -> bool:
    """Roteia a mensagem para o comando correto."""
    lc = message.content.lower()
    
    # Tenta cada módulo de comando
    if await setup_pontos_commands(client, message):
        return True
    
    if await setup_moderacao_commands(client, message):
        return True
    
    if await setup_imagens_commands(client, message):
        return True
    
    if await setup_clima_commands(client, message):
        return True
    
    if await setup_ia_commands(client, message, REGRAS_MSG):
        return True
    
    return False

@client.event
async def on_message(message: discord.Message):
    """Evento acionado quando uma mensagem é enviada."""
    if message.author.bot:
        return
    if message.guild and message.guild.name != "Dark Moon":
        return

    content = message.content.strip()
    if not content:
        return

    lc = content.lower()
    channel_id = message.channel.id

    # Define canais permitidos
    canais_rank_ia = [ID_CANAL_PRINCIPAL]
    canais_fun = [ID_CANAL_PRINCIPAL, ID_CANAL_CARRO]
    
    if ALLOWED_CHANNEL_ID != 0:
        canais_rank_ia.append(ALLOWED_CHANNEL_ID)
        canais_fun.append(ALLOWED_CHANNEL_ID)

    # Verifica permissão básica de canal
    if channel_id not in canais_rank_ia and channel_id not in canais_fun:
        return

    try:
        await route_command(message, channel_id)
    except Exception as e:
        logging.exception("❌ Erro no on_message:")
        await message.channel.send(f"🐞 Erro no sistema Dark Moon: `{e}`")

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

if not DISCORD_TOKEN:
    logging.error("❌ CRÍTICO: TOKEN do Discord não encontrado.")
else:
    client.run(DISCORD_TOKEN)
