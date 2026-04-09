# -*- coding: utf-8 -*-
import discord # type: ignore
from discord.ext import commands # type: ignore
from discord import app_commands # type: ignore
import json
import os
import asyncio
from datetime import timedelta
from typing import Dict, Any, List

DATA_FILE = "data.json"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data: Dict[str, Any] = self.load_data() # type: ignore

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"prefixes": {}, "warnings": {}, "jails": {}}
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    # =============== SOHBET TEMİZLEME ===============
    @app_commands.command(name="sohbet_temizle", description="Belirtilen miktarda mesajı siler.")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_chat(self, interaction: discord.Interaction, miktar: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=miktar)
        await interaction.followup.send(f"Bölge temizlendi! {len(deleted)} mesaj silindi.", ephemeral=True)

    # =============== BAN ===============
    @app_commands.command(name="ban", description="Belirtilen kullanıcıyı sunucudan yasaklar.")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_user(self, interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi"):
        await interaction.guild.ban(uye, reason=sebep)
        await interaction.response.send_message(f"🔨 {uye.mention} sunucudan yasaklandı. Sebep: {sebep}")

    # =============== MUTE (TIMEOUT) ===============
    @app_commands.command(name="mute", description="Kullanıcıyı belirli bir süre susturur (dakika cinsinden).")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute_user(self, interaction: discord.Interaction, uye: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
        süre = timedelta(minutes=dakika)
        await uye.timeout(süre, reason=sebep)
        await interaction.response.send_message(f"🔇 {uye.mention} {dakika} dakika boyunca susturuldu. Sebep: {sebep}")

    # =============== JAIL ===============
    @app_commands.command(name="jail", description="Kullanıcıyı karantinaya alır (jail rolü).")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def jail_user(self, interaction: discord.Interaction, uye: discord.Member, sebep: str = "Kurallara uymamak"):
        # Varsayılan Jail Rolünü Bul veya Oluştur
        jail_role = discord.utils.get(interaction.guild.roles, name="Jailed")
        if not jail_role:
            jail_role = await interaction.guild.create_role(name="Jailed", color=discord.Color.dark_grey(), reason="Jail sistemi kurulumu")
            # Kanallarda izinleri ayarla
            for channel in interaction.guild.channels:
                await channel.set_permissions(jail_role, view_channel=False, send_messages=False)
                
        # Mevcut rolleri kaydet ve Jail ver
        roller = [role.id for role in uye.roles if role.name != "@everyone"]
        
        guild_id = str(interaction.guild.id)
        user_id = str(uye.id)
        
        if guild_id not in self.data["jails"]: # type: ignore
            self.data["jails"][guild_id] = {} # type: ignore
            
        self.data["jails"][guild_id][user_id] = roller # type: ignore
        self.save_data()
        
        # Tüm rolleri çıkar ve sadece Jail ver
        try:
            await uye.edit(roles=[jail_role])
            await interaction.response.send_message(f"🚓 {uye.mention} hapse atıldı! Sebep: {sebep}")
        except discord.Forbidden:
            await interaction.response.send_message("Bunu yapmak için yetkim yok (Rolüm, hapse atacağınız kişinin rollerinden altta olabilir)!", ephemeral=True)

    # =============== DİNAMİK PREFIX ===============
    @app_commands.command(name="prefix", description="Sunucu için özel bot prefix'ini (ön ekini) değiştirir.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, yeni_prefix: str):
        guild_id = str(interaction.guild.id)
        self.data["prefixes"][guild_id] = yeni_prefix # type: ignore
        self.save_data()
        await interaction.response.send_message(f"✅ Sunucu için prefix başarıyla `{yeni_prefix}` olarak değiştirildi!")

    # =============== UYARI (WARN) SİSTEMİ ===============
    @app_commands.command(name="warn", description="Kullanıcıya uyarı verir.")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn_user(self, interaction: discord.Interaction, uye: discord.Member, sebep: str):
        await self.add_warning(interaction.guild, uye, sebep)
        await interaction.response.send_message(f"⚠️ {uye.mention} uyarıldı! Sebep: {sebep}")

    async def add_warning(self, guild, member, reason):
        """Kullanıcıya uyarı ekler ve 5 kere uyarıldıysa yetkililere haber verir."""
        guild_id = str(guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.data["warnings"]: # type: ignore
            self.data["warnings"][guild_id] = {} # type: ignore
        if user_id not in self.data["warnings"][guild_id]: # type: ignore
            self.data["warnings"][guild_id][user_id] = [] # type: ignore
            
        self.data["warnings"][guild_id][user_id].append(reason) # type: ignore
        self.save_data()
        
        warn_count = len(self.data["warnings"][guild_id][user_id]) # type: ignore
        
        # 5 uyarı sınırına ulaşıldı mı?
        if warn_count >= 5:
            # Yetkili kanalını bul (Önce hamsterwarns, sonra moderator-only, sonra diğerleri)
            mod_channel = discord.utils.find(lambda c: c.name.lower() == "hamsterwarns", guild.text_channels)
            if not mod_channel:
                mod_channel = discord.utils.get(guild.text_channels, name="moderator-only")
            if not mod_channel:
                mod_channel = discord.utils.find(lambda c: 'mod' in c.name or 'yönetici' in c.name or 'log' in c.name, guild.text_channels)
            
            if not mod_channel:
                mod_channel = guild.system_channel
                
            if mod_channel:
                # Mod rolleri etiketle (Yönetici veya Mesaj Yönet yetkisi olanlar)
                mod_roles = [role for role in guild.roles if role.permissions.administrator or role.permissions.manage_messages]
                # Sadece etiketlenebilir/önemli mod rollerini filtreleyebiliriz ama şimdilik hepsini alıyoruz
                mentions = " ".join([role.mention for role in mod_roles if role.name != "@everyone"])
                
                report_msg = f"🚨 {mentions}\n**{member.mention}** adlı kullanıcı kurallara uymadı! (5. İhlal)\n**Sebep:** {reason}"
                await mod_channel.send(report_msg)
                
            # Uyarıları sıfırla ki spama bağlamasın ve yeniden saymaya başlasın
            self.data["warnings"][guild_id][user_id] = []
            self.save_data()
        
        return warn_count

    # =============== ROL YÖNETİMİ ===============
    @app_commands.command(name="rol_ver", description="Bir kullanıcıya belirtilen rolü verir.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def give_role(self, interaction: discord.Interaction, uye: discord.Member, rol: discord.Role):
        try:
            await uye.add_roles(rol)
            await interaction.response.send_message(f"✅ {uye.mention} kullanıcısına {rol.mention} rolü başarıyla verildi!")
        except discord.Forbidden:
            await interaction.response.send_message("Bunu yapmak için yetkim yok (Rolüm, vermek istediğiniz rolden altta kalıyor olabilir).", ephemeral=True)

    @app_commands.command(name="rol_al", description="Bir kullanıcıdan belirtilen rolü alır.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, uye: discord.Member, rol: discord.Role):
        try:
            await uye.remove_roles(rol)
            await interaction.response.send_message(f"✅ {uye.mention} kullanıcısından {rol.mention} rolü başarıyla alındı!")
        except discord.Forbidden:
            await interaction.response.send_message("Bunu yapmak için yetkim yok.", ephemeral=True)

    # =============== KANAL YÖNETİMİ ===============
    @app_commands.command(name="yavas_mod", description="Kanalda yavaş modu aktif eder.")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, saniye: int):
        await interaction.channel.edit(slowmode_delay=saniye)
        if saniye == 0:
            await interaction.response.send_message("✅ Yavaş mod kapatıldı.")
        else:
            await interaction.response.send_message(f"✅ Yavaş mod aktifleştirildi: Herkes {saniye} saniyede bir mesaj yazabilir.")

    @app_commands.command(name="kanal_kilit", description="Kanalı everyone rolüne mesaj yazmaya kapatır.")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock_channel(self, interaction: discord.Interaction):
        everyone_role = interaction.guild.default_role
        await interaction.channel.set_permissions(everyone_role, send_messages=False)
        await interaction.response.send_message("🔒 Bu kanal kilitlendi ve mesaj yazmaya kapatıldı!")

    @app_commands.command(name="kilit_ac", description="Kanalı everyone rolüne mesaj yazmaya tekrar açar.")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock_channel(self, interaction: discord.Interaction):
        everyone_role = interaction.guild.default_role
        await interaction.channel.set_permissions(everyone_role, send_messages=True)
        await interaction.response.send_message("🔓 Bu kanalın kilidi açıldı!")

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
    await bot.add_cog(Admin(bot))
