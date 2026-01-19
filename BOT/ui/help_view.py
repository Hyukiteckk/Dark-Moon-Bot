import discord
from services.command_registry import get_commands_by_category


# UI que o bot retorna ao marcar o bot
class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        categories = get_commands_by_category(bot.tree)

        options = [
            discord.SelectOption(
                label=cat.capitalize(),
                description=f"{len(cmds)} comandos",
                value=cat
            )
            for cat, cmds in categories.items()
            if cmds  # 🔒 garante que não cria vazio
        ]

        # 🔴 PROTEÇÃO CRÍTICA
        if not options:
            options = [
                discord.SelectOption(
                    label="Nenhum comando disponível",
                    value="empty",
                    description="Os comandos ainda não foram carregados"
                )
            ]

        super().__init__(
            placeholder="Selecione uma categoria",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        if category == "empty":
            await interaction.response.send_message(
                "⏳ Os comandos ainda não estão disponíveis. Tente novamente.",
                ephemeral=True
            )
            return

        commands = get_commands_by_category(self.bot.tree)[category]

        embed = discord.Embed(
            title=f"📂 {category.capitalize()}",
            color=discord.Color.blurple()
        )

        for cmd in commands:
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "Sem descrição",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(bot))

