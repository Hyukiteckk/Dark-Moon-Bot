import discord
from discord import Interaction, app_commands

from controllers.base import BaseController
from models.welcome import WelcomeModel
from repo.welcome_repo import WelcomeRepository
from functions.welcome import WelcomeService

from functions.call_time import CallTimeService
from repo.call_time_repo import CallTimeRepository

from utils.image import is_valid_image_url

from functions.points import PointsService

from datetime import timedelta

# ────────────────
# Commands Controller   
# ────────────────

# Controller para comandos gerais
class CommandsController(BaseController):
    def register(self):

        @self.bot.tree.command(
            name="ping",
            description="Comando de ping para testar o bot",
            extras={"category": "general"}
        )
        async def ping(interaction: Interaction):
            await interaction.response.send_message("Pong!")

        @self.bot.tree.command(
            name="rank",
            description="Mostra o ranking de call com pontos",
            extras={"category": "general"}
        )
        async def rank(interaction: Interaction):
            await self._send_rank(interaction)

    async def _send_rank(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)  # Apenas para quem executou

        # Pega o ranking completo
        all_data = await CallTimeRepository.top(interaction.guild.id, 1000)

        if not all_data:
            await interaction.followup.send(
                "❌ Ainda não há dados de ranking de voz (ninguém pontuou ainda).",
                ephemeral=True
            )
            return

        # Top 10
        top_data = all_data[:10]

        # ───────────────
        # Criar embed
        # ───────────────
        embed = discord.Embed(
            title="🏆 Membros em Destaque",
            description=(
                "--------------------------------\n"
                "Regra: 1 DarkPoint a cada 15 minutos de interação.\n"
                "O tempo é acumulativo. O bot preserva seu progresso ao mutar.\n"
                "--------------------------------"
            ),
            color=0x9B59B6
        )

        # Top 10 todos juntos em um campo
        medals = ["🥇", "🥈", "🥉"]
        top_text = ""
        for i, item in enumerate(top_data, start=1):
            user = interaction.guild.get_member(item["user_id"])
            name = user.display_name if user else "Usuário desconhecido"
            points = PointsService.seconds_to_points(item["total_seconds"])
            medal = medals[i-1] if i <= 3 else "⭐"
            top_text += f"{medal} {name} - {points}\n"

        embed.add_field(name="🏅 Top 10", value=top_text.strip(), inline=False)

        # Status atual do usuário que executou (mesmo que não esteja no top 10)
        me_data = next((x for x in all_data if x["user_id"] == interaction.user.id), None)
        if me_data:
            me_points = PointsService.seconds_to_points(me_data["total_seconds"])
            me_time = CallTimeService.format_time(me_data["total_seconds"])
            me_position = all_data.index(me_data) + 1
            status = (
                f"📊 **Status Atual**\n"
                f"Posição: {me_position}º | 🪙 DarkPoints: {me_points} | ⏱ Acumulado: {me_time}"
            )
        else:
            status = "📊 **Status Atual**\nVocê ainda não pontuou."

        embed.add_field(name="--------------------------------", value=status, inline=False)
        embed.set_footer(text="The DarkMoon System")

        await interaction.followup.send(embed=embed, ephemeral=True)

# ────────────────
# CommandsAdmin Controller
# ────────────────

# Controller para comandos administrativos
class CommandsAdmin(BaseController):
    def register(self):

        @self.bot.tree.command(
            name="setwelcome",
            description="Define mensagem de boas-vindas",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            channel="Canal onde a mensagem será enviada",
            message="Texto da mensagem (use {user})",
            image="Imagem anexada (opcional)",
            image_url="URL da imagem (opcional)"
        )
        async def setwelcome(
            interaction: Interaction,
            channel: app_commands.AppCommandChannel,
            message: str,
            image: discord.Attachment | None = None,
            image_url: str | None = None
        ):
            # ACK rápido
            await interaction.response.defer(ephemeral=True)

            final_image_url: str | None = None

            # ───────────────
            # IMAGEM (prioridade: attachment > url)
            # ───────────────
            if image:
                if image.content_type and image.content_type.startswith("image/"):
                    final_image_url = image.url
                else:
                    await interaction.followup.send(
                        "❌ O arquivo enviado não é uma imagem válida.",
                        ephemeral=True
                    )
                    return

            elif image_url:
                if is_valid_image_url(image_url):
                    final_image_url = image_url
                else:
                    await interaction.followup.send(
                        "❌ A URL da imagem não é pública ou não tem extensão válida.",
                        ephemeral=True
                    )
                    return

            model = WelcomeModel(
                guild_id=interaction.guild.id,
                channel_id=channel.id,
                message=message,
                image=final_image_url
            )

            await WelcomeRepository.save(model)

            await interaction.followup.send(
                f"✅ Boas-vindas configuradas em {channel.mention}",
                ephemeral=True
            )


        @self.bot.tree.command(
            name="testwelcome",
            description="Testa a mensagem de boas-vindas",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        async def testwelcome(interaction: Interaction):

            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ Este comando só pode ser usado em servidores",
                    ephemeral=True
                )
                return

            # interaction.user é User, precisamos de Member
            member = interaction.guild.get_member(interaction.user.id)

            if not member:
                await interaction.response.send_message(
                    "❌ Não foi possível identificar o membro",
                    ephemeral=True
                )
                return

            ok = await WelcomeService.send_welcome(member)

            if not ok:
                await interaction.response.send_message(
                    "❌ Nenhuma configuração de boas-vindas encontrada",
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                "✅ Mensagem de boas-vindas enviada com sucesso",
                ephemeral=True
                    )

        @self.bot.tree.command(
            name="sayembed",
            description="Envia uma mensagem organizada em embed",
            extras={"category": "admin"}
        )
        @app_commands.describe(
            title="Título do embed",
            description="Descrição do embed",
            color="Cor HEX do embed (ex: #ff0000) opcional",
            image="Imagem anexada (opcional)",
            image_url="URL da imagem grande (opcional)",
            thumbnail="Thumbnail anexada (opcional)",
            thumbnail_url="URL da thumbnail (opcional)"
        )
        @self.bot.middleware(admin=True)
        async def sayembed(
            interaction: Interaction,
            title: str,
            description: str,
            color: str | None = None,
            image: discord.Attachment | None = None,
            image_url: str | None = None,
            thumbnail: discord.Attachment | None = None,
            thumbnail_url: str | None = None
        ):
            # ACK imediato
            await interaction.response.defer()  # resposta pública

            # Cor
            try:
                color_int = int(color.replace("#", ""), 16) if color else 0x9b59b6
            except Exception:
                color_int = 0x9b59b6

            embed = discord.Embed(
                title=title,
                description=description,
                color=color_int
            )

            # ───────────────
            # IMAGEM PRINCIPAL
            # Prioridade: attachment > URL
            # ───────────────
            final_image_url = None
            if image and image.content_type and image.content_type.startswith("image/"):
                final_image_url = image.url
            elif image_url and is_valid_image_url(image_url):
                final_image_url = image_url

            if final_image_url:
                embed.set_image(url=final_image_url)

            # ───────────────
            # THUMBNAIL
            # Prioridade: attachment > URL
            # ───────────────
            final_thumbnail_url = None
            if thumbnail and thumbnail.content_type and thumbnail.content_type.startswith("image/"):
                final_thumbnail_url = thumbnail.url
            elif thumbnail_url and is_valid_image_url(thumbnail_url):
                final_thumbnail_url = thumbnail_url

            if final_thumbnail_url:
                embed.set_thumbnail(url=final_thumbnail_url)

            # FOOTER
            icon_url = (
                interaction.user.avatar.url
                if interaction.user.avatar
                else interaction.user.default_avatar.url
            )
            embed.set_footer(
                text=f"Enviado por {interaction.user}",
                icon_url=icon_url
            )

            # ENVIO FINAL PARA TODOS VEREM
            await interaction.followup.send(embed=embed)


        @self.bot.tree.command(
            name="kick",
            description="Expulsa um usuário do servidor",
            extras={"category": "admin"}

        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser expulso",
            reason="Motivo (opcional)"
        )
        async def kick(
            interaction: Interaction,
            user: discord.Member,
            reason: str | None = None
        ):
            await interaction.response.defer(ephemeral=True)

            try:
                await user.kick(reason=reason)
                print(f"👢 [KICK] {user} por {interaction.user}")
                await interaction.followup.send(
                    f"👢 **{user}** foi expulso.\n📄 Motivo: {reason or 'Não informado'}",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao expulsar usuário.\n`{e}`",
                    ephemeral=True
                )


        @self.bot.tree.command(
            name="ban",
            description="Bane um usuário do servidor",
            extras={"category": "admin"}

        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser banido",
            reason="Motivo (opcional)"
        )
        async def ban(
            interaction: Interaction,
            user: discord.Member,
            reason: str | None = None
        ):
            await interaction.response.defer(ephemeral=True)

            try:
                await user.ban(reason=reason)
                print(f"🔨 [BAN] {user} por {interaction.user}")
                await interaction.followup.send(
                    f"🔨 **{user}** foi banido.\n📄 Motivo: {reason or 'Não informado'}",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao banir usuário.\n`{e}`",
                    ephemeral=True
                )

        @self.bot.tree.command(
            name="castigo",
            description="Castiga um usuário temporariamente",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser mutado",
            minutes="Duração em minutos",
            reason="Motivo (opcional)"
        )
        async def castigo(
            interaction: Interaction,
            user: discord.Member,
            minutes: int,
            reason: str | None = None
        ):
            await interaction.response.defer(ephemeral=True)

            try:
                duration = timedelta(minutes=minutes)
                await user.timeout(duration, reason=reason)

                print(f"🔇 [MUTE] {user} por {interaction.user} ({minutes}m)")

                await interaction.followup.send(
                    f"🔇 **{user}** mutado por `{minutes}` minutos.\n📄 Motivo: {reason or 'Não informado'}",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao mutar usuário.\n`{e}`",
                    ephemeral=True
                )


        @self.bot.tree.command(
            name="tirarcastigo",
            description="Remove o castigo de um usuário",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser desmutado"
        )
        async def tirarcastigo(
            interaction: Interaction,
            user: discord.Member
        ):
            await interaction.response.defer(ephemeral=True)

            try:
                # Remove o timeout do usuário
                await user.timeout(None)

                print(f"🔊 [UNMUTE] {user} desmutado por {interaction.user}")

                await interaction.followup.send(
                    f"🔊 **{user}** foi desmutado com sucesso.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao desmutar usuário.\n`{e}`",
                    ephemeral=True
                )

        @self.bot.tree.command(
            name="mute",
            description="Muta um usuário no canal de voz",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser mutado",
            reason="Motivo opcional"
        )
        async def mute(interaction: Interaction, user: discord.Member, reason: str | None = None):
            await interaction.response.defer(ephemeral=True)
            
            try:
                if not user.voice or not user.voice.channel:
                    await interaction.followup.send(
                        f"❌ {user} não está em um canal de voz.",
                        ephemeral=True
                    )
                    return

                # Mutar no canal de voz
                await user.edit(mute=True, reason=reason)
                print(f"🔇 [VOICE MUTE] {user} por {interaction.user} | Motivo: {reason}")
                
                await interaction.followup.send(
                    f"🔇 {user} foi mutado no canal de voz.\n📄 Motivo: {reason or 'Não informado'}",
                    ephemeral=True
                )

            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao mutar {user} no canal de voz.\n`{e}`",
                    ephemeral=True
                )

        # ───────────────
        # DESMUTAÇÃO EM CALL
        # ───────────────
        @self.bot.tree.command(
            name="unmute",
            description="Desmuta um usuário no canal de voz",
            extras={"category": "admin"}
        )
        @self.bot.middleware(admin=True)
        @app_commands.describe(
            user="Usuário a ser desmutado"
        )
        async def unmute(interaction: Interaction, user: discord.Member):
            await interaction.response.defer(ephemeral=True)

            try:
                if not user.voice or not user.voice.channel:
                    await interaction.followup.send(
                        f"❌ {user} não está em um canal de voz.",
                        ephemeral=True
                    )
                    return

                # Desmutar no canal de voz
                await user.edit(mute=False)
                print(f"🔊 [VOICE UNMUTE] {user} desmutado por {interaction.user}")

                await interaction.followup.send(
                    f"🔊 {user} foi desmutado no canal de voz.",
                    ephemeral=True
                )

            except Exception as e:
                await interaction.followup.send(
                    f"❌ Erro ao desmutar {user} no canal de voz.\n`{e}`",
                    ephemeral=True
                )