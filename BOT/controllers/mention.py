import discord
from controllers.base import BaseController
from ui.help_view import HelpView

# Controller para menções ao bot
class MentionController(BaseController):

    def register(self):

        @self.bot.client.event
        async def on_message(message):
            if message.author.bot:
                return

            if self.bot.client.user in message.mentions:
                await message.channel.send(
                    content="📖 **Menu de comandos**",
                    view=HelpView(self.bot)
                )

