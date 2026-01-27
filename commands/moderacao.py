"""
🔨 COMANDOS DE MODERAÇÃO
kick, ban, mute, unmute, limpar chat
"""

import discord
import re
import logging
from utils import get_member

async def cmd_mute(message: discord.Message, content: str):
    """Comando: Muta um membro."""
    if not message.author.guild_permissions.mute_members:
        return await message.channel.send("❌ Sem permissão.")
    
    match = re.search(r'(?:mute|mutar)\s+(.+)', content, re.IGNORECASE)
    if match:
        target = await get_member(message.guild, match.group(1).strip())
        if target:
            await target.edit(mute=True)
            await message.channel.send(f"✅ **{target.display_name}** foi mutado.")

async def cmd_unmute(message: discord.Message, content: str):
    """Comando: Desmuta um membro."""
    if not message.author.guild_permissions.mute_members:
        return await message.channel.send("❌ Sem permissão.")
    
    match = re.search(r'(?:unmute|desmutar)\s+(.+)', content, re.IGNORECASE)
    if match:
        target = await get_member(message.guild, match.group(1).strip())
        if target:
            await target.edit(mute=False)
            await message.channel.send(f"✅ **{target.display_name}** foi desmutado.")

async def cmd_kick(message: discord.Message, content: str):
    """Comando: Remove um membro do call."""
    if not message.author.guild_permissions.move_members:
        return await message.channel.send("❌ Sem permissão.")
    
    match = re.search(r'(?:kick|kickar)\s+(.+)', content, re.IGNORECASE)
    if match:
        target = await get_member(message.guild, match.group(1).strip())
        if target and target.voice:
            await target.move_to(None)
            await message.channel.send(f"🔌 **{target.display_name}** foi desconectado.")

async def cmd_ban(message: discord.Message, content: str):
    """Comando: Bane um membro."""
    if not message.author.guild_permissions.ban_members:
        return await message.channel.send("❌ Sem permissão.")
    
    match = re.search(r'(?:ban|banir)\s+(.+)', content, re.IGNORECASE)
    if match:
        target = await get_member(message.guild, match.group(1).strip())
        if target:
            await target.ban(reason=f"Banido por {message.author}")
            await message.channel.send(f"🚫 **{target.display_name}** foi banido.")

async def cmd_limpar_chat(message: discord.Message, content: str):
    """Comando: Apaga mensagens do chat."""
    if not message.author.guild_permissions.manage_messages:
        return await message.channel.send("❌ Sem permissão.")
    
    limit = 300
    match = re.search(r'\b(\d+)\b', content)
    if match:
        limit = max(1, min(int(match.group(1)), 300))
    
    deleted = await message.channel.purge(limit=limit)
    await message.channel.send(f"✅ Apaguei **{len(deleted)}** mensagens!", delete_after=5)

async def cmd_linguicar(message: discord.Message, content: str):
    """Comando: Linguiça um membro."""
    match = re.search(r'linguiçar\s+(.+)', content, re.IGNORECASE)
    if match:
        target = await get_member(message.guild, match.group(1).strip())
        if target:
            await message.channel.send(f"**{target.display_name}** foi linguiçado com força! 😂")

async def setup_moderacao_commands(client, message: discord.Message):
    """Setup dos comandos de moderação."""
    lc = message.content.lower()
    
    if re.match(r'^(mute|mutar)\b', lc):
        await cmd_mute(message, message.content)
        return True
    
    if re.match(r'^(unmute|desmutar)\b', lc):
        await cmd_unmute(message, message.content)
        return True
    
    if re.match(r'^(kick|kickar)\b', lc):
        await cmd_kick(message, message.content)
        return True
    
    if re.match(r'^(ban|banir)\b', lc):
        await cmd_ban(message, message.content)
        return True
    
    if any(kw in lc for kw in ["apagar mensagens", "limpar chat", "clear", "purge"]):
        await cmd_limpar_chat(message, message.content)
        return True
    
    if re.match(r'^(linguiçar)\b', lc):
        await cmd_linguicar(message, message.content)
        return True
    
    return False
