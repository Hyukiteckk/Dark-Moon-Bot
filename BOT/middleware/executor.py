import discord
from typing import Iterable

# Função auxiliar para executar middlewares
async def run_middlewares(
    interaction: discord.Interaction,
    middlewares: Iterable
) -> bool:
    for middleware in middlewares:
        ok = await middleware.before(interaction)
        if not ok:
            return False
    return True

