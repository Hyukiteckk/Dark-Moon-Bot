import time
import discord
from controllers.base import BaseController
from functions.call_time import CallTimeService
from repo.call_time_repo import CallTimeRepository
from functions.welcome import WelcomeService
from repo.message_repo import MessageRepository


class EventsController(BaseController):

    def register(self):

        @self.bot.client.event
        async def on_ready():
            await self.bot.tree.sync()
            print(f"🤖 [READY] Conectado como {self.bot.client.user}")

        @self.bot.client.event
        async def on_message(message):
            if message.author.bot or not message.guild:
                return
            await MessageRepository.add(message.guild.id, message.author.id)

        @self.bot.client.event
        async def on_member_join(member):
            await WelcomeService.send_welcome(member)

        @self.bot.client.event
        async def on_voice_state_update(member, before, after):
            if member.bot:
                return

            guild_id = member.guild.id
            user_id = member.id

            was_active = CallTimeService.is_active_state(before)
            is_active = CallTimeService.is_active_state(after)

            # Ficou ativo
            if not was_active and is_active:
                await CallTimeService.join_call(guild_id, user_id)

            # Deixou de ser ativo
            elif was_active and not is_active:
                await CallTimeService.leave_call(guild_id, user_id)
