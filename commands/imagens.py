"""
🎨 COMANDOS DE IMAGENS
imaginar, desenhar
"""

import discord
import re

async def cmd_imaginar(message: discord.Message, content: str):
    """Gera imagens com IA."""
    match = re.search(r'(?:imaginar|desenhar)\s+(.+)', content, re.IGNORECASE)
    if not match:
        return await message.channel.send("Uso: `imaginar <descrição>`")
    
    prompt_img = match.group(1).strip()
    await message.channel.send(f"🎨 **Dark Moon** está criando: **{prompt_img}**...")
    
    image_url = f"https://image.pollinations.ai/prompt/{prompt_img.replace(' ', '%20')}"
    embed = discord.Embed(title="Imagem Gerada", color=discord.Color.dark_purple())
    embed.set_image(url=image_url)
    embed.set_footer(text="Gerado por Dark Moon")
    
    await message.channel.send(embed=embed)

async def setup_imagens_commands(client, message: discord.Message):
    """Setup dos comandos de imagem."""
    lc = message.content.lower()
    
    if re.match(r'^(imaginar|desenhar)\b', lc):
        await cmd_imaginar(message, message.content)
        return True
    
    return False
