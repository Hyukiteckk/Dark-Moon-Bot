from abc import ABC, abstractmethod
import discord

# Middleware base para interceptar interações
class BaseMiddleware(ABC):

    @abstractmethod
    async def before(self, interaction: discord.Interaction) -> bool:
        ...
