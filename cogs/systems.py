# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import json
import os
import requests
import asyncio

DATA_FILE = "data.json"

class Systems(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Data load error: {e}")
            return {}

    def is_enabled(self, guild_id, category, feature):
        self.data = self.load_data() # Reload for fresh settings
        guild_id = str(guild_id)
        settings = self.data.get("guild_settings", {})
        guild_config = settings.get(guild_id, settings.get("default", {}))
        feature_data = guild_config.get(category, {}).get(feature)
        if isinstance(feature_data, dict):
            return feature_data.get("enabled", False)
        return bool(feature_data)

    def get_config(self, guild_id, category, feature):
        self.data = self.load_data() # Reload for fresh settings
        guild_id = str(guild_id)
        settings = self.data.get("guild_settings", {})
        return settings.get(guild_id, settings.get("default", {})).get(category, {}).get(feature, {})

    # 1. Karşılama Sistemi (Hoşgeldin Mesajı + Fotoğraf)
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Auto Role
        if self.is_enabled(member.guild.id, "moderation", "autorole"):
            role = discord.utils.get(member.guild.roles, name="Member")
            if role:
                try: await member.add_roles(role)
                except: pass

        # Welcome System
        if self.is_enabled(member.guild.id, "moderation", "welcome"):
            config = self.get_config(member.guild.id, "moderation", "welcome")
            channel_id = config.get("channel_id")
            if channel_id:
                channel = member.guild.get_channel(int(channel_id))
                if channel:
                    img_data = await self.create_welcome_image(member)
                    file = discord.File(fp=img_data, filename="welcome.png")
                    msg = config.get("message", "Hoş geldin {user}!").replace("{user}", member.mention)
                    await channel.send(msg, file=file)

    # 2. Reaction Role (Tam Uygulama)
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.is_enabled(payload.guild_id, "moderation", "reactionrole"):
            return
        
        config_data = self.get_config(payload.guild_id, "moderation", "reactionrole")
        configs = config_data.get("configs", [])
        
        for cfg in configs:
            emoji_str = str(payload.emoji.name) if not payload.emoji.id else str(payload.emoji)
            if str(payload.message_id) == str(cfg.get("message_id")) and (emoji_str == cfg.get("emoji") or str(payload.emoji) == cfg.get("emoji")):
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role = guild.get_role(int(cfg.get("role_id")))
                if role and member and not member.bot:
                    try: await member.add_roles(role)
                    except: pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not self.is_enabled(payload.guild_id, "moderation", "reactionrole"):
            return
        
        config_data = self.get_config(payload.guild_id, "moderation", "reactionrole")
        configs = config_data.get("configs", [])
        
        for cfg in configs:
            emoji_str = str(payload.emoji.name) if not payload.emoji.id else str(payload.emoji)
            if str(payload.message_id) == str(cfg.get("message_id")) and (emoji_str == cfg.get("emoji") or str(payload.emoji) == cfg.get("emoji")):
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role = guild.get_role(int(cfg.get("role_id")))
                if role and member:
                    try: await member.remove_roles(role)
                    except: pass

    # 3. Geçici Oda Sistemi (Temp VC)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.is_enabled(member.guild.id, "moderation", "tempvc"):
            return
        
        config = self.get_config(member.guild.id, "moderation", "tempvc")
        trigger_id = config.get("trigger_channel_id")
        
        if after.channel and str(after.channel.id) == str(trigger_id):
            category_id = config.get("category_id")
            category = member.guild.get_channel(int(category_id)) if category_id else after.channel.category
            
            new_channel = await member.guild.create_voice_channel(
                name=f"🔊 {member.name}'s Room",
                category=category
            )
            await member.move_to(new_channel)
            
            # Kanalı takip listesine eklemek gerekebilir, şimdilik silme mantığı:
            def check(m, b, a):
                return b.channel == new_channel and len(new_channel.members) == 0
            
            while len(new_channel.members) > 0:
                await asyncio.sleep(5)
            await new_channel.delete()

    async def create_welcome_image(self, member):
        # Arka plan oluştur (Modern koyu tema)
        width, height = 800, 300
        background = Image.new('RGB', (width, height), color=(35, 39, 42))
        draw = ImageDraw.Draw(background)

        # Profil resmini indir
        avatar_url = member.display_avatar.url
        try:
            response = requests.get(avatar_url)
            avatar_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            avatar_img = avatar_img.resize((150, 150))

            # Profil resmini yuvarlak yap
            mask = Image.new('L', (150, 150), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 150, 150), fill=255)
            avatar_img.putalpha(mask)

            # Profil resmini yapıştır
            background.paste(avatar_img, (50, 75), avatar_img)
        except:
            pass

        # Yazıları ekle
        try:
            # Farklı font yollarını dene (Windows, Linux vb. için)
            font_paths = ["arial.ttf", "C:\\Windows\\Fonts\\arial.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
            font_title = None
            font_subtitle = None
            for path in font_paths:
                try:
                    font_title = ImageFont.truetype(path, 50)
                    font_subtitle = ImageFont.truetype(path, 30)
                    break
                except:
                    continue
            
            if not font_title:
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
        except:
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()

        draw.text((250, 100), "HOŞ GELDİN", font=font_title, fill=(255, 255, 255))
        name_text = f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name
        draw.text((250, 160), name_text, font=font_subtitle, fill=(114, 137, 218))

        # Görseli bayt akışına çevir
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

async def setup(bot):
    await bot.add_cog(Systems(bot))
