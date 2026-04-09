# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bilgi", description="H.A.M.S.24 botu hakkında bilgi verir.")
    async def bilgi(self, interaction: discord.Interaction):
        await interaction.response.send_message("Merhaba! Ben H.A.M.S.24. Güçlü bir reklam engelleyici ve anti-spam sistemine sahip sunucu koruma botuyum!")

    @app_commands.command(name="ping", description="Botun gecikme süresini gösterir.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Gecikme sürem: {latency}ms")

async def setup(bot):
    await bot.add_cog(Utility(bot))
