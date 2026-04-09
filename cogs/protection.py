# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import json
import os
import time
from collections import defaultdict

DATA_FILE = "data.json"

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.join_logs = defaultdict(list)  # "guild_id-user_id" -> [timestamps]

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def is_enabled(self, guild_id, category, feature):
        self.data = self.load_data()
        guild_id = str(guild_id)
        settings = self.data.get("guild_settings", {})
        guild_config = settings.get(guild_id, settings.get("default", {}))
        return guild_config.get(category, {}).get(feature, False)

    # 1. Kanal Koruması
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if self.is_enabled(channel.guild.id, "protection", "channel"):
            # Eğer kanal silindiyse tekrar açmayı deneyebiliriz veya loglayabiliriz.
            # Şimdilik sadece denetim kaydından kimin yaptığına bakıp bir log kanalına atabiliriz.
            await self.log_action(channel.guild, f"Kanal Silindi: {channel.name}. Kanal Koruması Aktif!")

    # 2. Rol Koruması
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if self.is_enabled(role.guild.id, "protection", "role"):
            await self.log_action(role.guild, f"Rol Silindi: {role.name}. Rol Koruması Aktif!")

    # 3. Ban Koruması
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if self.is_enabled(guild.id, "protection", "ban"):
            await self.log_action(guild, f"Üye Yasaklandı: {user.name}. Ban Koruması Aktif!")

    # 4. Anti-Raid & Spam Koruması
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        now = time.time()
        
        # Spam Koruması Kontrolü
        if self.is_enabled(guild.id, "protection", "spam"):
            user_id = member.id
            guild_id = guild.id
            key = f"{guild_id}-{user_id}"
            
            # 5 dakika (300 saniye) öncesini temizle ve yeni girişi ekle
            self.join_logs[key] = [t for t in self.join_logs[key] if now - t < 300]
            self.join_logs[key].append(now)
            
            # 5 veya daha fazla giriş yapıldıysa banla
            if len(self.join_logs[key]) >= 5:
                try:
                    await member.ban(reason="Spam Koruması: 5 dakika içinde çok fazla giriş-çıkış (5+ kez).")
                    
                    # Kayıtları temizle (tekrar gelirse sıfırdan başlasın)
                    self.join_logs.pop(key, None)
                        
                    # hamsterwarns kanalını bul ve bilgilendir
                    warn_channel = discord.utils.get(guild.text_channels, name="hamsterwarns")
                    if warn_channel:
                        await warn_channel.send(
                            f"🛡️ **Spam Koruması Devreye Girdi!**\n"
                            f"Kullanıcı: {member.mention}\n"
                            f"Sebep: 5 dakika içerisinde 5 veya daha fazla kez sunucuya gir-çık yapıldı.\n"
                            f"Eylem: Kalıcı Yasaklama (Ban)"
                        )
                except Exception as e:
                    print(f"Spam ban hatası: {e}")
                return # Banlandıysa anti-raid kontrolüne gerek yok

        # Anti-Raid Kontrolü (Hızlı Üye Girişi)
        if self.is_enabled(guild.id, "protection", "raid"):
            import datetime
            account_age = (discord.utils.utcnow() - member.created_at).days
            if account_age < 3: # 3 günden yeni hesaplar
                 try:
                     await member.kick(reason="Anti-Raid: Yeni hesap koruması.")
                     await self.log_action(guild, f"Anti-Raid: {member.name} (Yeni hesap) sunucudan atıldı.")
                 except:
                     pass

    async def log_action(self, guild, message):
        log_channel_id = 0 # Burası dinamik olmalı
        # Log kanalı ayarlıysa oraya at, yoksa sistem kanalına
        channel = guild.system_channel
        if channel:
            await channel.send(f"🛡️ **[KORUMA SİSTEMİ]** {message}")

async def setup(bot):
    await bot.add_cog(Protection(bot))
