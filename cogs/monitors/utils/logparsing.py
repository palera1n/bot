from discord.ext import commands
from data.services import guild_service
from utils.fetchers import fetch_remote_json, fetch_remote_file
import discord
from utils import cfg


class LogParsing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """When an .ips file is posted, check if its valid JSON and a panic log"""

        if msg.guild.id != cfg.guild_id:
            return

        if msg.author.bot:
            return

        if not msg.attachments:
            return

        att = msg.attachments[0]
        if att.filename.endswith(".ips"):
            await self.do_panic_log(msg, att)
        elif att.filename.endswith(".log") and att.filename.startswith("FAIL"):
            await self.do_log_file(msg, att)

    async def do_panic_log(self, msg: discord.Message, att):
        json = await fetch_remote_json(att.url)
        if json is not None:
            if "panicString" in json:
                string = json['panicString'].split("\n")[0]
                await msg.reply(f"Hey, it looks like this is a panic log!\n\nHere is the panic string:```{string}```")

    async def do_log_file(self, msg: discord.Message, att):
        text = await fetch_remote_file(att.url)
        if text is not None:
            if not "```" in text or "@everyone" in text:
                string = '\n'.join(text.splitlines()[-10:])
                await msg.reply(f"Hey, it looks like this is a palera1n failure log!\n\nHere is the last 10 lines to help debuggers:```{string}```")


async def setup(bot):
    await bot.add_cog(LogParsing(bot))
