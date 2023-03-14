from discord.ext import commands
from data.services import guild_service
from utils.framework import find_triggered_filters
import discord
from utils import cfg

import pytesseract
import cv2
import aiohttp
import numpy as np


class OCR(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """When an image file is posted, run OCR on it"""

        try:
            if msg.guild.id != cfg.guild_id:
                return
        except:
            return

        if msg.author.bot:
            return

        if not msg.attachments:
            return

        att = msg.attachments[0]
        if att.filename.lower().endswith(".png") or att.filename.lower().endswith(".jpg"):
            image = await self.url_to_image(att.url)

            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(
                grey, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            text = pytesseract.image_to_string(thresh)

            # commonissues
            # TODO: make this not hard coded (e.g. add /commonissues link)
            if "usb handle" in text.lower() and "occurred" in text.lower():
                await self.post_issue("Found the USB handle followed by an error occurred", msg)
            elif "for network" in text.lower():
                await self.post_issue("Stuck at waiting for network", msg)
            elif "no space left" in text.lower():
                await self.post_issue("No space left on device", msg)
            elif "lockdownd" in text.lower():
                await self.post_issue("Could not connect to lockdownd", msg)
            elif "legacy" in text.lower() and "install" in text.lower():
                await self.post_issue("pip error: legacy-install-failure", msg)
            elif "killed" in text.lower() and "pyimg4" in text.lower():
                await self.post_issue('"Killed" issue (not "Killed: 9")', msg)
            elif "furry" in text.lower():
                await msg.reply("meow :3 🥺")
            elif "i hate flowercat" in text.lower():
                await msg.reply("i hate YOU.")

    async def post_issue(self, title, msg: discord.Message):
        message: discord.Message = self.bot.issue_cache.cache[title]
        embed = message.embeds[0]
        view = discord.ui.View()
        components = message.components
        if components:
            for component in components:
                if isinstance(component, discord.ActionRow):
                    for child in component.children:
                        b = discord.ui.Button(
                            style=child.style, emoji=child.emoji, label=child.label, url=child.url)
                        view.add_item(b)

        embed.set_footer(
            text="This action was performed automatically. Please disregard if incorrect.")
        await msg.reply(embed=embed, view=view)

    async def url_to_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as res:
                image = np.asarray(bytearray(await res.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)

                return image


async def setup(bot):
    await bot.add_cog(OCR(bot))
