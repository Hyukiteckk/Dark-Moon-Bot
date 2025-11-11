from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")  # garante que o nome bate com o .env

if TOKEN is None:
    raise ValueError("Token não encontrado no arquivo .env")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/dm", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")


@bot.tree.command(name="cl", description="Apaga mensagens do chat")
async def cl(interaction: discord.Interaction, quantidade: int = 10000):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Você não tem permissão.", ephemeral=True)
        return

    if quantidade < 1 or quantidade > 10000:
        await interaction.response.send_message("⚠️ Use um valor entre 1 e 10000.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade)
    msg = await interaction.followup.send(f"🧹 Foram apagadas {len(deleted)} mensagens.", ephemeral=True)
    await asyncio.sleep(5)
    await msg.delete()


@bot.command()
async def cl(ctx, quantidade: int = 10000):
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ Você não tem permissão para apagar mensagens.")
        return

    if quantidade < 1 or quantidade > 10000:
        await ctx.send("⚠️ Use um valor entre 1 e 100.")
        return

    deleted = await ctx.channel.purge(limit=quantidade)
    await ctx.send(f"🧹 Foram apagadas {len(deleted)} mensagens.", delete_after=5)


bot.run(TOKEN)