"""
☀️ COMANDOS DE CLIMA E TRADUÇÃO
clima, temperatura, traduzir
"""

import discord
import re
import asyncio
import logging
from utils import get_weather, call_groq, OPENWEATHER_API_KEY

async def cmd_climate(message: discord.Message, content: str):
    """Comando: Mostra clima de uma cidade."""
    if not OPENWEATHER_API_KEY:
        return await message.channel.send("❌ Clima não configurado.")
    
    async with message.channel.typing():
        cidade = await asyncio.to_thread(call_groq, f"Extraia APENAS o nome da cidade: '{content}'")
        if not cidade or "N/A" in cidade:
            return await message.channel.send("🤔 Não entendi a cidade.")
        
        weather = await asyncio.to_thread(get_weather, cidade, OPENWEATHER_API_KEY)
        if not weather["success"]:
            return await message.channel.send(f"❌ Erro: {weather['error']}")
        
        data = weather["data"]
        embed = discord.Embed(title=f"Clima em {data['name']}", color=discord.Color.blue())
        embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
        embed.add_field(name="🌡️ Temp", value=f"{data['main']['temp']:.1f}°C", inline=True)
        embed.add_field(name="💧 Umidade", value=f"{data['main']['humidity']}%", inline=True)
        embed.add_field(name="📝 Descrição", value=data['weather'][0]['description'].capitalize(), inline=False)
        embed.set_footer(text="Dados: Dark Moon")
        
        await message.channel.send(embed=embed)

async def cmd_traduzir(message: discord.Message, content: str):
    """Comando: Traduz texto."""
    match = re.search(r'traduzir\s+(.+)', content, re.IGNORECASE)
    if not match:
        return await message.channel.send("Uso: `traduzir <texto>`")
    
    texto = match.group(1).strip()
    async with message.channel.typing():
        traducao = await asyncio.to_thread(
            call_groq,
            f"Traduza para Português (ou para Inglês se já for PT): '{texto}'"
        )
        await message.reply(f"🔄 **Tradução:**\n{traducao}")

async def cmd_serverinfo(message: discord.Message):
    """Comando: Mostra informações do servidor."""
    guild = message.guild
    embed = discord.Embed(title=f"📊 Informações de {guild.name}", color=discord.Color.dark_teal())
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    
    await message.channel.send(embed=embed)

async def setup_clima_commands(client, message: discord.Message):
    """Setup dos comandos de clima e tradução."""
    lc = message.content.lower()
    
    palavras_chave_clima = ["temperatura", "clima", "tempo em", "previsão para", "graus em"]
    
    if any(kw in lc for kw in palavras_chave_clima):
        await cmd_climate(message, message.content)
        return True
    
    if re.match(r'^(traduzir)\b', lc):
        await cmd_traduzir(message, message.content)
        return True
    
    if lc == "serverinfo" or lc == "info servidor":
        await cmd_serverinfo(message)
        return True
    
    return False
