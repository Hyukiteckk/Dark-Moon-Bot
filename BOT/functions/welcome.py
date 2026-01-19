import discord
from repo.welcome_repo import WelcomeRepository


class WelcomeService:

    @staticmethod
    async def send_welcome(member: discord.Member) -> bool:
        # Busca a configuração do servidor
        config = await WelcomeRepository.get(member.guild.id)
        if not config:
            return False

        channel_id = config.get("channel_id")
        message = config.get("message")

        if not channel_id or not message:
            return False

        # Obtém o canal
        channel = member.guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return False

        # Substituições disponíveis na mensagem

        "Bem-vindo {user} ao {guild}! Agora somos {member_count} membros :tada:"

        description = (
            message
            .replace("{user}", member.mention)
            .replace("{guild}", member.guild.name)
            .replace("{member_count}", str(member.guild.member_count))
        )


        # Cria o embed
        embed = discord.Embed(
            title="Boas-vindas!",
            description=description,
            color=discord.Color.purple()
        )

        # Thumbnail (avatar do usuário)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        # Imagem opcional configurada
        image_url = config.get("image")
        if image_url:
            embed.set_image(url=image_url)

        # Envia a mensagem garantindo a menção
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True)
        )

        return True

