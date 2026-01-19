import discord
from middleware.base import BaseMiddleware

# Middleware para logar comandos usados
class LoggerMiddleware(BaseMiddleware):
    async def before(self, interaction: discord.Interaction) -> bool:
        print(f"[CMD] /{interaction.command.name} - {interaction.user}")
        return True

# Middleware para bloquear comandos em DMs
class BlockDMMiddleware(BaseMiddleware):
    async def before(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Comando não permitido em DM",
                    ephemeral=True
                )
            return False
        return True

# Middleware para verificar permissão de administrador
class AdminRoleMiddleware(BaseMiddleware):
    async def before(self, interaction: discord.Interaction) -> bool:
        # Bloqueia se não for em guild (DM)
        if interaction.guild is None:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Comando administrativo não pode ser usado em DM",
                    ephemeral=True
                )
            return False

        # Só Member tem guild_permissions
        member: discord.Member = interaction.user
        if not member.guild_permissions.administrator:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "🚫 Você não tem permissão para usar este comando.",
                    ephemeral=True
                )
            return False

        return True

