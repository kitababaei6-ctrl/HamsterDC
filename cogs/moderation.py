# -*- coding: utf-8 -*-
import discord # type: ignore
from discord.ext import commands # type: ignore
import re
import time
import os
import json
from collections import defaultdict
from typing import Dict, List, Any

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Anti-spam için cache
        self.user_message_times: Any = defaultdict(list)
        self.spam_limit = 5      # 5 mesaj
        self.spam_timeframe = 5  # 5 saniye içinde
        
        # Ad-Block için çok kapsamlı regex (tüm linkleri ve domainleri yakalar, http olmasa dahi .com, .net bulur)
        self.link_regex = re.compile(
            r"(?:(?:https?|ftp)://)?[\w/\-?=%.]+\.[a-zA-Z]{2,}",
            re.IGNORECASE
        )
        
        # Kesinlikle engellenecek küfür kökleri (normal halleri)
        self.bad_words = [
            "amk", "aq", "amq", "oc", "oç", "orospu", "cocugu", "çocuğu", "covuku", "ovopku", "ovospu",
            "salak", "slk", "mal", "gerizekali", "gerizekalı", "aptal", "pic", "piç",
            "sikerim", "sik", "siktir", "sg", "yarak", "yarrak", "yaram", "yarram",
            "amcik", "amcık", "gavat", "pezevenk", "kahpe", "kasar", "kaşar", "kurva",
            "ibne", "ipne", "got", "göt", "memeler", "nah", "penis", "skerim", "amın", "amına",
            "aptal", "şerefsiz", "yavşak", "köpek", "bok", "pipi", "meme", "dalyarak", "nigger", "nigga", "s*ktrgt", "ovompsu", "piçoz"
            "sikim", "sucker", "kappe", "yarramıyala", "amımıyala", "omospu copkuku", "amcıkk", "am", "amımayasla", "götünüsikim", "porno", "sex", "porn", "hentai", "blowjob", "handjob", "doggy", "gangbang", "rape",
            "ospu", "orspununçocughu", "orospu", "orospuluk", "orospu çocuğu", "orospucocuk", "oç", "oc", "piç", "pic", "piç kurusu",
            "şerefsiz", "serefsiz", "şerefsizlik", "serefsizlik", "adi", "adi herif", "kahpe", "kahpelik",
            "alçak", "alcak", "alçaklık", "alcaklik", "namussuz", "namussuzluk", "karaktersiz",
            "karaktersizlik", "onursuz", "onursuzluk", "haysiyetsiz", "haysiyetsizlik",
            "pislik", "pis herif", "rezil", "rezillik", "iğrenç", "igrenc", "iğrenç herif",
            "salak", "aptal", "gerizekalı", "gerizekali", "zekasız", "zekasiz", "akılsız", "akilsiz", "beyinsiz",
            "mal", "dangalak", "hıyar", "hiyar", "eşek", "esek", "öküz", "okuz", "ayı", "ayi",
            "o*ospu", "or*spu", "oros*u", "oç*", "piç*", "ş*rfsiz", "n*mussuz",
            "or0spu", "0rospu", "orosp0", "p1ç", "p!c", "ş3refsiz", "s3r3fsiz",
            "mal herif", "aptal herif", "salak herif", "gerizekalı herif",
            "şerefsiz herif", "pislik adam", "rezil herif", "iğrenç insan",
            "insan müsveddesi", "yaratık", "ucube", "tipini", "suratını",
            "lanet olası", "lanet herif", "defol", "siktir", "siktir git", "sg",
            "amk", "aq", "mk", "amq", "s*k", "s*ktir", "s!ktir",
            "yarrak", "yarak", "y@rak", "yarra", "yarrağım",
            "göt", "got", "g0t", "g*t", "götoş", "gotos", "götlek",
            "ibne", "ibne", "ibn", "i*ne", "ibn3",
            "salak mısın", "aptal mısın", "mal mısın", "gerizekalı mısın",
            "ananı", "anan", "ananı sikeyim", "ananı s", "ana s", "ana skm",
            "babanı", "baban", "babanı sikeyim", "baba s", "baba skm",
            "sg git", "şirifsiz", "şeref yoksunu", "kaybol", "goon", "göon", "goom", "goor", "goön", "goom", "epstein", "epsteini", "epsteinst", "epsteinstin",
            "jeffrey epstein", "jeffrey epsteini", "jeffrey epsteinst", "jeffrey epsteinstin", "goğon", "goğon", "goğon", "ddy", "diddy",
            # ── English Profanity ──────────────────────────────────────────────
            # F-words
            "fuck", "fucked", "fucker", "fuckers", "fucking", "fucks", "fuckup",
            "fuckface", "fuckhead", "fuckwit", "fuckboy", "fuckgirl", "fuckboi",
            "motherfuck", "motherfucker", "motherfucking", "motherfucked",
            "clusterfuck", "mindfuck", "assfuck", "facefuck", "ratfuck",
            "fuckstick", "fucknut", "fuckwad", "fuckass", "fuckoff",
            "go fuck yourself", "gfy", "f you", "f off", "eff off",
            # S-words
            "shit", "shits", "shitted", "shitting", "shitty", "shitter",
            "bullshit", "horseshit", "dogshit", "chickenshit", "apeshit", "batshit",
            "dipshit", "dumbshit", "shithead", "shithole", "shitstorm", "shithouse",
            "shitlist", "shitshow", "shitbag", "shitface", "shitbrained",
            "eat shit", "eat shit and die", "pile of shit",
            # B-words
            "bitch", "bitches", "bitching", "bitchy", "bitchass",
            "son of a bitch", "sonofabitch", "sonofa bitch", "son of bitch",
            "bastard", "bastards", "bastardly",
            "basic bitch", "dumb bitch", "stupid bitch", "hoe ass bitch",
            "punk ass bitch", "pussy ass bitch", "raggedy bitch",
            # A-words
            "ass", "asses", "asshole", "assholes", "asshat", "asswipe",
            "assclown", "assbag", "assface", "asshead", "assbrain", "assbutt",
            "jackass", "dumbass", "smartass", "fatass", "lardass", "wiseass",
            "halfass", "halfassed", "candyass", "crackass", "raggedy ass",
            "trifling ass", "dusty ass", "crusty ass", "nasty ass",
            "smelly ass", "broke ass", "punk ass",
            "kiss my ass", "kma", "up your ass",
            # D-words
            "dick", "dicks", "dickhead", "dickface", "dickweed", "dickwit",
            "dickish", "dickery", "dickwad", "dickbag", "dickbrain",
            "suck my dick", "smd", "eat a dick",
            # C-words
            "cock", "cocks", "cockhead", "cockface", "cocksucker", "cocksucking",
            "cunt", "cunts", "cunty", "cuntface", "cunting",
            # W-words (sexual insults)
            "whore", "whores", "whorish", "man whore", "manwhore",
            "slut", "sluts", "slutty", "slutface", "slutbag",
            "skank", "skanky", "skanks", "hoe", "hoes",
            "hooker", "prostitute", "harlot", "strumpet", "trollop", "floozy",
            "thot", "thots", "tramp", "tart",
            # P-words
            "piss", "pissed", "pissing", "pisser", "pissant", "pisshead",
            "prick", "pricks",
            "pussy", "pussies", "pussyass",
            # British profanity
            "wanker", "wankers", "wanking", "wank",
            "tosser", "tossers", "tossing",
            "bollocks", "absolute bollocks",
            "bugger", "buggers", "buggered", "buggering", "bugger off",
            "arse", "arsehole", "arseholes", "arseface",
            "shite", "shites",
            "feck", "fecker", "fecking",
            "gobshite", "gobshites",
            "bellend", "bellends",
            "knob", "knobs", "knobhead", "knobheads", "knobber",
            "plonker", "plonkers",
            "numpty", "numpties",
            "minger", "mingers", "minging",
            "muppet", "muppets",
            "berk", "berks",
            "pillock", "pillocks",
            "twat", "twats", "twatface", "twathead",
            "git", "gits",
            "tosspot", "toerag", "toe rag",
            "sod", "sod off", "sods",
            "prat", "prats",
            "daft", "daft cow",
            "thick", "thicko",
            "divvy", "melt", "wasteman",
            "piss off", "bugger off", "sod off",
            # Racial slurs
            "chink", "chinks", "chinky",
            "spic", "spics", "spick", "spicks",
            "kike", "kikes",
            "gook", "gooks",
            "wetback", "wetbacks",
            "beaner", "beaners",
            "cracker", "crackers",
            "honky", "honkies", "honkeys",
            "redneck", "rednecks",
            "injun", "injuns",
            "redskin", "redskins",
            "coon", "coons",
            "jigaboo", "jigaboos",
            "sambo", "sambos",
            "spade", "spades",
            "darky", "darkies",
            "towelhead", "towelheads",
            "raghead", "ragheads",
            "sandnigger", "sand nigger",
            "camel jockey", "cameljockey",
            "zipperhead",
            "slope", "slopes",
            "cholo", "cholos",
            "gringo", "gringos",
            "half breed", "halfbreed",
            "mulatto", "pickaninny",
            # Homophobic/transphobic slurs
            "fag", "fags", "faggot", "faggots", "faggotry",
            "dyke", "dykes",
            "homo", "homos",
            "pansy", "pansies",
            "sissy", "sissies",
            "poof", "poofs", "poofter", "poofters",
            "tranny", "trannies",
            "shemale", "she male",
            "ladyboy",
            "pillow biter",
            # Mental/intelligence insults
            "retard", "retarded", "retards", "tard", "tards",
            "idiot", "idiots", "idiotic",
            "moron", "morons", "moronic",
            "imbecile", "imbeciles",
            "dimwit", "dimwits",
            "nitwit", "nitwits",
            "halfwit", "halfwits",
            "dingbat", "dingbats",
            "airhead", "airheads",
            "birdbrain", "birdbrains",
            "blockhead", "blockheads",
            "bonehead", "boneheads",
            "numbskull", "numbskulls",
            "pinhead", "pinheads",
            "lamebrain", "lamebrains",
            "dork", "dorks",
            "dweeb", "dweebs",
            "doofus", "goofus",
            "dunce", "dunces",
            "clod", "clods",
            "dolt", "dolts",
            "oaf", "oafs",
            "chump", "chumps",
            "twit", "twits",
            "dingdong",
            "meathead", "meatheads",
            "dipstick", "dipsticks",
            "nincompoop", "nincompoops",
            "blithering idiot",
            "complete moron",
            "braindead",
            # Appearance/personal insults
            "ugly", "uggo", "fugly",
            "fat pig", "fat cow", "fat slob", "slob",
            "blob", "lard",
            "disgusting pig", "filthy pig",
            "old hag", "hag",
            "freak", "freaks",
            "weirdo", "weirdos",
            "creep", "creeps",
            "pervert", "perverts", "perv", "pervs",
            "sicko", "sickos",
            # Character insults
            "scumbag", "scumbags",
            "scum", "pond scum",
            "vermin",
            "lowlife", "low life",
            "degenerate", "degenerates",
            "miscreant", "miscreants",
            "reprobate", "reprobates",
            "deadbeat", "deadbeats",
            "freeloader", "freeloaders",
            "leech", "leeches",
            "parasite", "parasites",
            "bottom feeder",
            "skid mark",
            "piece of shit", "piece of crap", "piece of garbage",
            "white trash", "trailer trash",
            "worthless", "useless",
            "pathetic", "pathetic loser",
            "wretched",
            "vile",
            "despicable",
            "loser", "losers",
            "douchebag", "douchebags", "douche",
            "turd", "turds", "turd burglar",
            "coward", "cowards",
            "wimp", "wimps",
            "crybaby", "cry baby",
            "snitch", "snitches",
            "rat", "rats",
            "narc", "narcs",
            "psycho", "psychos",
            "maniac", "maniacs",
            "nutjob", "nutcase", "nutcases",
            "crackpot", "crackpots",
            "wacko", "whacko",
            "lunatic", "lunatics",
            "incel", "incels",
            "simp", "simps", "simping",
            "poser", "posers",
            "backstabber",
            "two faced", "two-faced",
            "fake", "faker",
            # Sexual content/acts
            "cum", "cums", "cumshot", "cumshots",
            "jizz", "jizzed", "jizzing",
            "anal", "anal sex",
            "vagina", "vaginas",
            "erection", "boner",
            "ejaculate", "ejaculation",
            "orgasm", "orgasms",
            "masturbate", "masturbation", "masturbating", "masturbates",
            "grope", "groped", "groping",
            "fondle", "fondled", "fondling",
            "spank", "spanked", "spanking",
            "bondage", "bdsm",
            "fetish", "fetishes",
            "threesome", "foursome", "orgy", "orgies",
            "creampie",
            "squirt", "squirting",
            "rimjob", "rimming",
            "fisting",
            "teabag", "teabagging",
            "golden shower",
            "assrape", "ass rape",
            "date rape",
            "milf", "gilf", "dilf",
            "lolicon", "shotacon",
            "ecchi", "loli", "shota",
            "send nudes", "nudes",
            "dick pic", "dickpic", "cock pic",
            "titties", "tits", "boobs",
            "balls", "ballsack", "nutsack",
            "dildo", "dildos",
            "butt plug", "buttplug",
            "vibrator", "fleshlight",
            "pornstar", "porn star",
            "blow me",
            "lick my balls",
            "deepthroat", "deep throat",
            "fingering",
            "handjob", "hand job",
            "blowjob", "blow job",
            "titfuck", "tit fuck",
            "facefuck", "face fuck",
            # Threats / self-harm encouragement
            "kill yourself", "kys", "kill urself",
            "go die", "die bitch", "die loser",
            "hang yourself",
            "rope yourself",
            "go jump off a bridge",
            "drink bleach",
            "eat glass",
            "stab yourself",
            "shoot yourself",
            "i will kill you", "ill kill you",
            "i will fuck you up", "ill fuck you up",
            "i will beat you", "ill beat you up",
            "i hope you die",
            "drop dead",
            "go kill yourself",
            # Extremism / hate ideology
            "neo-nazi", "neonazi",
            "kkk", "ku klux klan",
            "white supremacist", "white supremacy",
            "ethnic cleansing",
            "isis", "isil",
            "al-qaeda", "al qaeda", "alqaeda",
            "jihad", "jihadist",
            "bomb threat",
            "school shooting",
            "mass shooting",
            "terrorist", "terrorism",
            # Drug slang (problematic usage)
            "crackhead", "crackheads",
            "methhead", "tweaker",
            "shoot up", "shooting up",
            "overdose",
            # Misc. vulgar / offensive phrases
            "screw you", "screw off",
            "go to hell", "rot in hell",
            "burn in hell",
            "god damn", "goddamn", "goddamnit",
            "son of a whore",
            "son of a slut",
            "dirty whore", "stupid whore",
            "dirty slut", "nasty slut", "filthy slut",
            "dumb cunt", "stupid cunt", "ugly cunt",
            "nasty bitch", "filthy bitch", "dirty bitch",
            "crazy bitch",
            "dumb fuck", "stupid fuck", "ugly fuck", "fat fuck",
            "holy shit",
            "what the fuck", "wtf",
            "shut the fuck up", "stfu",
            "fuck you", "f u",
            "fuck off",
            "get fucked",
            "get bent",
            "you piece of shit",
            "you piece of garbage",
            "you are worthless",
            "you are nothing",
            "you are garbage",
            "you are trash",
            "you are scum",
            "you make me sick",
            "nobody likes you",
            "everyone hates you",
        ]

        # Karakter değişim haritası (Örn: @ -> a, 0 -> o)
        self.char_map = {
            '@': 'a', '0': 'o', '1': 'i', '!': 'i', '3': 'e', '4': 'a', '5': 's', 
            '7': 't', '$': 's', 'q': 'k', 'w': 'v'
        }

        # Şaka amaçlı veya yanlış anlaşılabilecek kalıpların küfür sanılmasını engelleyen istisna listesi (Allowlist)
        self.allowlist = [
            "devam ke", "devamke", "naber", "nbr", "tm", "tmm", "ok", "peki", "slm", "as"
        ]

        # Yasaklı harfler (özel/yabancı karakterler + Kiril alfabesi)
        self.banned_chars = set(
            "êəéÊƏÉÝýūùûúÙÚÍĮÏÎÌøóõōœôòØÓÕŌŒÔÒ"
            "äáÄÁßśšẞŚŠžŽčćČĆňñŇÑ"
            "#"
            # Kiril alfabesi (tüm harfler - küçük)
            "абвгдежзийклмнопрстуфхцчшщъыьэюя"
            "ёђѓєѕіїјљњћќўџ"
            # Kiril alfabesi (tüm harfler - büyük)
            "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
            "ЁЂЃЄЅІЇЈЉЊЋЌЎЏ"
        )

    def normalize_text(self, text: str) -> str:
        """Kullanıcının yazdığı yazıyı sembollerden arındırır, harfleri normale çevirir ve ardışık harfleri siler."""
        text = text.lower()
        
        # Karakterleri haritaya göre değiştir
        for key, value in self.char_map.items():
            text = text.replace(key, value)
            
        # Sadece harfleri ve boşlukları bırak (noktalama, sembol sil)
        text = re.sub(r'[^a-zçğıöşü\s]', '', text)
        
        # Ardışık tekrarlayan harfleri teke indir (örn: sssaaaalllaaakkk -> salak)
        text = re.sub(r'(.)\1+', r'\1', text)
        
        return text

    def has_bad_word(self, message_content: str) -> bool:
        """Mesaj içeriğinde küfür olup olmadığını gizlenmiş/sansürlenmiş halleriyle kontrol eder."""
        normalized = self.normalize_text(message_content)
        words = normalized.split()
        
        # Sadece tam kelime eşleşmesi kontrolü
        for word in words:
            if word in self.bad_words:
                # İstisna: Eğer kelime allowlist içindeyse (tam eşleşme) geç
                if word in self.allowlist:
                    continue
                return True
                
        return False

    def has_banned_char(self, message_content: str) -> bool:
        """Mesaj içeriğinde yasaklı karakter olup olmadığını kontrol eder."""
        return bool(self.banned_chars & set(message_content))

    def has_link(self, message_content: str) -> bool:
        """Mesaj içeriğinde herhangi bir link/site olup olmadığını kontrol eder."""
        return bool(self.link_regex.search(message_content))

    def is_spamming(self, user_id: int) -> bool:
        """Kullanıcının spam yapıp yapmadığını kontrol eder."""
        current_time = time.time()
        self.user_message_times[user_id].append(current_time)
        
        self.user_message_times[user_id] = [
            msg_time for msg_time in self.user_message_times[user_id] 
            if current_time - msg_time <= self.spam_timeframe
        ]
        
        if len(self.user_message_times[user_id]) >= self.spam_limit:
            return True
        return False

    async def safe_delete(self, message: discord.Message):
        """Mesaj silme işlemi sırasında NotFound (10008) çökmesini engeller."""
        try:
            await message.delete()
        except:
            pass

    def is_enabled(self, guild_id, category, feature):
        if not os.path.exists("data.json"): 
            return False
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            guild_id = str(guild_id)
            settings = data.get("guild_settings", {})
            guild_config = settings.get(guild_id, settings.get("default", {}))
            feature_data = guild_config.get(category, {}).get(feature)
            if isinstance(feature_data, dict):
                return feature_data.get("enabled", False)
            return bool(feature_data)
        except:
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Sunucu dışı mesajları (DM) atla
        if not message.guild:
            return

        # İçerik boşsa atla
        if not message.content:
            return

        # Kanal bazlı izin kontrolü - sesli sohbet kanallarında da çalışır
        try:
            perms = message.channel.permissions_for(message.author)
            if perms.administrator or perms.manage_messages:
                return
        except Exception:
            # İzin kontrolü başarısız olursa, eski yöntemi dene
            try:
                if message.author.guild_permissions.administrator or message.author.guild_permissions.manage_messages:
                    return
            except Exception:
                pass

        admin_cog = self.bot.get_cog("Admin")

        # 0. Yasaklı Harf Koruması
        if self.is_enabled(message.guild.id, "moderation", "banned_chars") and self.has_banned_char(message.content):
            await self.safe_delete(message)
            warning_msg = f"{message.author.mention}, yasaklı karakter kullanımı yasaktır!"
            if admin_cog:
                await admin_cog.add_warning(message.guild, message.author, "Otomatik Uyarı: Yasaklı Karakter Kullandı")
            warning = await message.channel.send(warning_msg)
            await warning.delete(delay=5)
            return

        # 1. Küfür & Sansür Koruması
        if self.is_enabled(message.guild.id, "moderation", "swear") and self.has_bad_word(message.content):
            await self.safe_delete(message)
            warning_msg = f"{message.author.mention}, argo/küfür kullanımı kesinlikle yasaktır!"
            if admin_cog:
                warn_count = await admin_cog.add_warning(message.guild, message.author, "Otomatik Uyarı: Küfür/Hakaret Etti")
            warning = await message.channel.send(warning_msg)
            await warning.delete(delay=5)
            return

        # 2. Ad Blocker Kontrolü (Tüm Linkler)
        if self.is_enabled(message.guild.id, "moderation", "ad") and self.has_link(message.content):
            channel_name = getattr(message.channel, "name", "")
            # Kanal isminde "görsel-içerik" geçiyorsa veya emoji varsa direkt izin ver
            is_gorsel_channel = "görsel-içerik" in channel_name or "📷" in channel_name
            
            if not is_gorsel_channel:
                await self.safe_delete(message)
                warning_msg = f"{message.author.mention}, lütfen sunucuda site bağlantısı/reklam paylaşmayınız!"
                if admin_cog:
                    await admin_cog.add_warning(message.guild, message.author, "Otomatik Uyarı: Reklam/Dış Bağlantı Paylaştı")
                warning = await message.channel.send(warning_msg)
                await warning.delete(delay=5)
                return

        # 3. Büyük Harf (Caps) Koruması
        if self.is_enabled(message.guild.id, "moderation", "caps") and len(message.content) > 5:
            upper_case_chars = sum(1 for c in message.content if c.isupper())
            if upper_case_chars / len(message.content) > 0.7: # %70 üstü büyük harfse
                await self.safe_delete(message)
                if admin_cog:
                    await admin_cog.add_warning(message.guild, message.author, "Otomatik Uyarı: Aşırı Büyük Harf Kullanımı")
                warning = await message.channel.send(f"{message.author.mention}, lütfen büyük harf kullanımını azaltın!")
                await warning.delete(delay=3)
                return

        # 4. Anti-Spam Kontrolü
        if self.is_enabled(message.guild.id, "protection", "spam") and self.is_spamming(message.author.id):
            await self.safe_delete(message)
            if admin_cog:
                await admin_cog.add_warning(message.guild, message.author, "Otomatik Uyarı: Spam Yapmak")
            warning = await message.channel.send(f"{message.author.mention}, lütfen mesajlarınızı biraz daha yavaş gönderin!")
            await warning.delete(delay=5)
            return

async def setup(bot):
    await bot.add_cog(Moderation(bot))
