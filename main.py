import os
import discord # type: ignore
from discord.ext import commands # type: ignore
from dotenv import load_dotenv # type: ignore
import json
import asyncio
from typing import Any, Dict, Optional

DATA_FILE = "data.json"

def get_prefix(bot, message):
    if not os.path.exists(DATA_FILE):
        return "!"
    try:    
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        guild_id = str(message.guild.id) if message.guild else None
        if guild_id and guild_id in data.get("prefixes", {}):
            return data["prefixes"][guild_id]
    except:
        pass
    return "!"

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class HamsBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix, # type: ignore
            intents=intents, # type: ignore
            help_command=commands.DefaultHelpCommand() # type: ignore
        )

    async def setup_hook(self):
        print("Bot modülleri yükleniyor...")
        extensions = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.fun", "cogs.protection", "cogs.systems"]
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"Modül yüklendi: {ext}")
            except Exception as e:
                print(f"Hata: {ext} yüklenemedi: {e}")
        
        await self.tree.sync()
        print("Slash komutları senkronize edildi.")

    async def on_ready(self):
        print(f'Giriş yapıldı: {self.user} (ID: {self.user.id})')
        print('Bot tamamen hazır!')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok!", delete_after=5)
            return
        raise error

async def main():
    bot = HamsBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Hata: DISCORD_TOKEN bulunamadı!")
        return
    
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot kapatılıyor...")
