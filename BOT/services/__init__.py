import discord
from discord import app_commands
from functools import wraps
from middleware.base import BaseMiddleware
from database.mongo import MongoDB



# Serviço principal do bot
class Bot:
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True

        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)

        self._middlewares: list[BaseMiddleware] = []
        self._admin_middlewares: list[BaseMiddleware] = []

        self.client.setup_hook = self._setup_hook


    # Conexão com o banco de dados
    async def _setup_hook(self):
        await MongoDB.connect()

    # Registro de middlewares
    def use(self, middleware: BaseMiddleware, admin: bool = False):
        if admin:
            self._admin_middlewares.append(middleware)
        else:
            self._middlewares.append(middleware)

    def middleware(self, admin: bool = False):
        middlewares = self._admin_middlewares if admin else self._middlewares

        def decorator(func):
            @wraps(func)
            async def wrapper(interaction: discord.Interaction, *args, **kwargs):
                for mw in middlewares:
                    ok = await mw.before(interaction)
                    if not ok:
                        return
                return await func(interaction, *args, **kwargs)
            return wrapper
        return decorator
    
    # Inicia o bot
    def run(self, token: str):
        self.client.run(token)


