# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Kullanıcının profil resmini gösterir.")
    async def avatar(self, interaction: discord.Interaction, uye: discord.Member = None):
        user = uye or interaction.user
        embed = discord.Embed(title=f"{user.display_name} adlı kişinin avatarı:", color=discord.Color.blue())
        if user.avatar:
            embed.set_image(url=user.avatar.url)
        else:
            embed.description = "Bu kullanıcının özel bir avatarı yok."
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kullanici_bilgi", description="Bir kullanıcı hakkında detaylı bilgi verir.")
    async def userinfo(self, interaction: discord.Interaction, uye: discord.Member = None):
        user = uye or interaction.user
        roles = [role.name for role in user.roles if role.name != "@everyone"]
        
        embed = discord.Embed(title=f"Kullanıcı Bilgileri: {user}", color=discord.Color.green())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        embed.add_field(name="ID", value=user.id, inline=False)
        embed.add_field(name="Sunucuya Katılma", value=user.joined_at.strftime("%d/%m/%Y, %H:%M:%S") if user.joined_at else "Bilinmiyor", inline=False)
        embed.add_field(name="Hesap Oluşturulma", value=user.created_at.strftime("%d/%m/%Y, %H:%M:%S"), inline=False)
        embed.add_field(name=f"Roller ({len(roles)})", value=", ".join(roles) if roles else "Yok", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sunucu_bilgi", description="Sunucu hakkında istatistikleri gösterir.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"{guild.name} Sunucu Bilgileri", color=discord.Color.gold())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Sunucu ID", value=guild.id, inline=False)
        embed.add_field(name="Kurucu", value=guild.owner.mention if guild.owner else "Bilinmiyor", inline=False)
        embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
        embed.add_field(name="Kanal Sayısı", value=len(guild.channels), inline=True)
        embed.add_field(name="Rol Sayısı", value=len(guild.roles), inline=True)
        embed.add_field(name="Oluşturulma", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="zar_at", description="1 ile 6 arasında rastgele bir zar atar.")
    async def roll_dice(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Zar atıldı, sonuç: **{result}**")

    @app_commands.command(name="yazi_tura", description="Yazı mı tura mı atar.")
    async def coin_flip(self, interaction: discord.Interaction):
        result = random.choice(["Yazı", "Tura"])
        await interaction.response.send_message(f"🪙 Para atıldı, sonuç: **{result}**")

    @app_commands.command(name="anket", description="Sunucuda soru sormanızı sağlayan bir anket oluşturur.")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll(self, interaction: discord.Interaction, soru: str):
        embed = discord.Embed(title="📊 Anket", description=soru, color=discord.Color.purple())
        embed.set_footer(text=f"{interaction.user.display_name} tarafından oluşturuldu.")
        
        await interaction.response.send_message("Anket oluşturuluyor...", ephemeral=True)
        poll_msg = await interaction.channel.send(embed=embed)
        await poll_msg.add_reaction("✅")
        await poll_msg.add_reaction("❌")


    # =============== YETKİ HATASI HANDLER ===============
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için yeterli yetkiniz yok!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Bir hata oluştu: {error}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Fun(bot))
