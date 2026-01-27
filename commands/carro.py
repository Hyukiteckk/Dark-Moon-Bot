"""
🚗 SISTEMA DO CARRO DA DARK MOON
Carro com pontos, botão e loop automático
"""

import discord
import logging
import asyncio
from datetime import datetime
from utils import add_user_points

class CarroView(discord.ui.View):
    """View com botão para pegar o carro."""
    def __init__(self):
        super().__init__(timeout=None)
        self.winners = []

    @discord.ui.button(label="PEGAR 🚗", style=discord.ButtonStyle.success, custom_id="carro_dark_moon_pegar")
    async def pegar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para pegar o carro e ganhar pontos."""
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        if user_id in self.winners:
            return await interaction.response.send_message(
                "❌ Você já pegou sua recompensa neste carro!",
                ephemeral=True
            )

        self.winners.append(user_id)
        position = len(self.winners)
        points_to_give = self._calculate_points(position)

        if points_to_give == 0:
            return await interaction.response.send_message(
                "🏁 O carro já lotou! Mais sorte na próxima.",
                ephemeral=True
            )

        add_user_points(user_id, points_to_give)
        await self._update_message(interaction, position, user_name, points_to_give, button)

    @staticmethod
    def _calculate_points(position: int) -> int:
        """Calcula pontos baseado na posição."""
        if position == 1:
            return 50
        elif 2 <= position <= 4:
            return 25
        elif 5 <= position <= 6:
            return 15
        return 0

    async def _update_message(self, interaction: discord.Interaction, position: int, user_name: str, points: int, button):
        """Atualiza a mensagem do carro com a nova entrada."""
        embed = interaction.message.embeds[0]
        new_entry = f"**{position}.** {user_name} — **{points} pts**"
        
        found_field = False
        for i, field in enumerate(embed.fields):
            if field.name == "🏆 Quem já pegou:":
                new_value = field.value + "\n" + new_entry
                embed.set_field_at(i, name="🏆 Quem já pegou:", value=new_value, inline=False)
                found_field = True
                break
        
        if not found_field:
            embed.add_field(name="🏆 Quem já pegou:", value=new_entry, inline=False)

        if len(self.winners) >= 6:
            button.label = "CARRO CHEIO 🚫"
            button.style = discord.ButtonStyle.secondary
            button.disabled = True
            embed.set_footer(text="Dark Moon System • CARRO LOTADO")
            self.stop()
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(
            f"🚗 **VRUM!** {interaction.user.mention} pegou a vaga **#{position}** e ganhou **{points}** pontos!",
            ephemeral=False
        )

async def spawn_carro_func(channel, id_canal_carro: int):
    """Gera mensagem do carro no canal."""
    hora_atual = datetime.now().strftime("%H:%M")
    embed = discord.Embed(
        title="🚗 O CARRO DA DARK MOON PASSOU!",
        description=(
            f"**Horário:** {hora_atual}\n\n"
            "Clique rápido em **PEGAR** para ganhar pontos!\n\n"
            "🥇 **1º Lugar:** 50 Pontos\n"
            "🥈 **2º ao 4º:** 25 Pontos\n"
            "🥉 **5º ao 6º:** 15 Pontos"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Dark Moon System • Próximo em 4h")
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3097/3097180.png")
    
    view = CarroView()
    await channel.send(embed=embed, view=view)

async def carro_background_loop(client, id_canal_carro: int):
    """Loop automático que spawna carro a cada 4 horas."""
    await client.wait_until_ready()
    channel = client.get_channel(id_canal_carro)
    
    if not channel:
        logging.warning(f"⚠️ Canal do carro ({id_canal_carro}) não encontrado.")
        return

    while not client.is_closed():
        await spawn_carro_func(channel, id_canal_carro)
        await asyncio.sleep(14400)  # 4 horas

async def carro_loop_with_delay(client, id_canal_carro: int):
    """Helper para esperar 4h antes do próximo carro (usado no force)."""
    await asyncio.sleep(14400)
    await carro_background_loop(client, id_canal_carro)

async def setup_carro_commands(client, message: discord.Message):
    """Setup dos comandos do carro (vazio - carro é automático)."""
    return False
