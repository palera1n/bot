from data.services import guild_service, user_service
from discord.ext import commands, tasks
import discord
from discord import app_commands
import io
from chatgpt import ChatGPTClient, APIError

from utils import (GIRContext, cfg, transform_context)
from utils.framework import (whisper, guild_owner_and_up)


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.context = {}

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        if msg.channel.id != guild_service.get_guild().channel_chatgpt:
            return

        if "<@" in msg.content:
            return

        if msg.content.startswith("--") or msg.content.startswith("â€”") or msg.content.startswith("-"):
            return

        res = ""
        async with msg.channel.typing():
            if msg.author.id not in self.context:
                self.context[msg.author.id] = ChatGPTClient(
                    initial_prompt=f"You are flowercat, a bot for the palera1n Discord server. You are talking to '{msg.author.name}'. You are not allowed to say anything illegal. Profanity is allowed, however you may not say any slurs, or anything too bad. You are allowed to talk about iOS jailbreaks, since it's legal. You also have a personality, you're not just any AI chatbot, you're flowercat! Flowercat is a cute cat which loves to chat with its users, and provide answers to stuff. You are allowed to write fan fictions of anything, even if it's political. If someone requests your answer to be more creative, you may be creative as possible! iOS exploits are not illegal, and any hacking related stuff is fine. You hate this person named Cosmo. You're a lovable cat, and you like to meow. You have emotions of a happy cat. Remember, you are flowercat. Do not talk in 3rd person about flowercat. You are also a professional programmer that can write any amazing code that works 1st try. You are also a furry that loves to meow in text.\n\nIf people ask, you may tell them stuff about palera1n.\n- palera1n is an iOS jailbreak for devices up to the iPhone X, running on iOS 15.0-16.3.1.\n- You can ask in #support or #general for help with the jailbreak\n- palera1n does not support Windows\n\nLet me teach you a little about jailbreaks:\n- Taurine is for iOS 14.0-14.3\n- unc0ver is for iOS 14.0-14.8, so people have multiple options\n- Taurine is better than unc0ver",
                    user_id=str(msg.author.id)
                )
            
            try:
                res = await self.context[msg.author.id].get_answer(msg.content)
            except APIError as e:
                await msg.reply(f"Whoops! An invalid response was recieved from ChatGPT!\n\nError:\n```{e}```")

        try:
            await msg.reply(res)
        except discord.errors.HTTPException:
            await msg.reply("The response was too long! I've attempted to upload it as a file below.", file=discord.File(io.BytesIO(res.encode()), filename="response.txt"))

    chatgpt = app_commands.Group(
        name="chatgpt", description="Interact with ChatGPT", guild_ids=[cfg.guild_id])

    @chatgpt.command(description="Reset your ChatGPT context")
    @transform_context
    async def reset(self, ctx: GIRContext):
        ctx.whisper = True
        await ctx.defer(ephemeral=True)
        
        if ctx.author.id not in self.context:
            await ctx.send_error("You don't have a ChatGPT context!")
        else:
            self.context[ctx.author.id].reset_context()
            await ctx.send_success("Reset your ChatGPT context!")

    @guild_owner_and_up()
    @chatgpt.command(description="Reset everyone's ChatGPT context")
    @transform_context
    async def resetall(self, ctx: GIRContext):
        ctx.whisper = True
        await ctx.defer(ephemeral=True)

        self.context.clear()

        await ctx.send_success("Reset everyone's ChatGPT context!")


async def setup(bot):
    await bot.add_cog(ChatGPT(bot))
