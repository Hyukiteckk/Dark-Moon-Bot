"""
📊 COMANDOS DE PONTOS E RANKING
pontos, ranking, zerar pontos
"""

import discord
import time
import logging
from utils import (
    update_current_voice_sessions, get_user_points, clear_all_points,
    user_points, voice_pending_seconds, voice_join_times
)

async def cmd_zerar_pontos(message: discord.Message):
    """Comando: Zera todos os pontos (apenas admin)."""
    if not message.author.guild_permissions.administrator:
        return await message.channel.send("❌ Apenas administradores podem zerar os pontos.")
    
    clear_all_points()
    await message.channel.send("🧹 **O Ranking de pontos de voz foi ZERADO com sucesso!**")

async def cmd_meus_pontos(message: discord.Message):
    """Comando: Mostra seus pontos e estatísticas."""
    update_current_voice_sessions()
    
    user_id = str(message.author.id)
    total_points = get_user_points(user_id)
    current_seconds = voice_pending_seconds.get(user_id, 0)
    
    if user_id in voice_join_times:
        session_time = time.time() - voice_join_times[user_id]
        current_seconds += session_time

    total_minutes = int(current_seconds // 60)
    minutes_needed = 15 - (total_minutes % 15)
    
    response = (
        f"📊 **Seus Status no Servidor Dark Moon**\n\n"
        f"🏆 **Pontos Totais:** {total_points}\n"
        f"⏱️ **Tempo Ativo (Desmutado):** {total_minutes} minutos\n"
        f"⏳ **Próximo ponto em:** {minutes_needed} minutos\n\n"
        f"*Continue ativo nas calls para subir no Ranking!*"
    )
    
    try:
        await message.author.send(response)
        await message.reply("📩 Mandei seus status no seu privado!")
    except discord.Forbidden:
        await message.reply("❌ Sua DM está fechada.")

async def cmd_ranking(message: discord.Message):
    """Comando: Mostra o ranking TOP 10 de pontos."""
    update_current_voice_sessions()
    
    if not user_points:
        return await message.channel.send("📊 Ainda não há dados de ranking.")
    
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_users[:10]
    
    embed = discord.Embed(title="〔 🏆 〕Membros em Destaque", color=discord.Color.from_rgb(255, 215, 0))
    
    description = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Regra: 1 MoonPoint a cada 15 minutos de interação.\n"
        "O tempo é acumulativo.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎖 **Top 10 Membros — Microfone Ativo**\n\n"
    )
    
    for i, (uid, points) in enumerate(top_10):
        membro = message.guild.get_member(int(uid))
        nome = membro.display_name if membro else f"Desconhecido ({uid})"
        
        emojis = ["🥇", "🥈", "🥉", "🏅", "🏅", "⭐", "⭐", "⭐", "⭐", "⭐"]
        emoji = emojis[i] if i < len(emojis) else "⭐"
        
        description += f"{emoji} {nome} — {points} MoonPoints\n"
    
    user_id = str(message.author.id)
    my_points = get_user_points(user_id)
    pending = voice_pending_seconds.get(user_id, 0)
    
    if user_id in voice_join_times:
        pending += (time.time() - voice_join_times[user_id])
    
    min_pending = int(pending // 60)
    ranked_ids = [u[0] for u in sorted_users]
    
    try:
        my_rank_pos = ranked_ids.index(user_id) + 1
        rank_str = f"{my_rank_pos}º"
    except ValueError:
        rank_str = "Sem classificação"

    description += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**🎖 Status Atual:**\n"
        f"**Posição: {rank_str}  | MoonPoints: {my_points}  | Acumulado: {min_pending} min**"
    )
    
    embed.description = description
    embed.set_footer(text="Dark Moon System")
    
    await message.channel.send(embed=embed)

async def setup_pontos_commands(client, message: discord.Message):
    """Setup dos comandos de pontos."""
    lc = message.content.lower()
    
    triggers_points = ["pontos", "points", "meus pontos", "tempo call", "stats", "meu tempo"]
    triggers_rank = ["rank", "ranking", "classificação", "classificacao", "top call", "top 10"]
    
    if lc == "zerar pontos" or lc == "zerar ranking":
        await cmd_zerar_pontos(message)
        return True
    
    if any(trig == lc for trig in triggers_points):
        await cmd_meus_pontos(message)
        return True
    
    if any(trig in lc for trig in triggers_rank):
        await cmd_ranking(message)
        return True
    
    return False
