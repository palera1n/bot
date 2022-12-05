from data.services import guild_service, user_service
from discord.ext import commands, tasks
import discord
from discord import app_commands

from utils import (CosmoContext, cfg, get_dstatus_components,
                   get_dstatus_incidents, transform_context)
from utils.fetchers import chatgpt_request
from utils.framework import (MONTH_MAPPING, Duration, gatekeeper,
                             give_user_birthday_role, mod_and_up, whisper)


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.context = {}
        self.conversation = {}

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        if msg.channel.id != guild_service.get_guild().channel_chatgpt:
            return

        if "<@" in msg.content:
            return

        res = ""
        async with msg.channel.typing():
            context = self.context.get(
                msg.author.id) if msg.author.id in self.context else ""
            conversation = self.conversation.get(
                msg.author.id) if msg.author.id in self.conversation else None

            res = await chatgpt_request(msg.content, context=context, conversation=conversation)

            try:
                if res["status"] == "error":
                    await msg.reply(f"Whoops! An invalid response was recieved from ChatGPT!\n\n```{res['error']}```")
            except KeyError:
                pass

        self.context[msg.author.id] = res["message"]["id"]
        self.conversation[msg.author.id] = res["conversation_id"]

        try:
            try:
                await msg.reply(res["message"]["content"]["parts"][0])
            except KeyError:
                pass
        except discord.errors.HTTPException:
            await msg.reply("The response was too long!")

    chatgpt = app_commands.Group(
        name="chatgpt", description="Interact with ChatGPT", guild_ids=[cfg.guild_id])

    @chatgpt.command(description="Reset your ChatGPT context")
    @transform_context
    async def reset(self, ctx: CosmoContext):
        ctx.whisper = True
        await ctx.defer(ephemeral=True)

        self.context.pop(ctx.author.id, None)
        self.conversation.pop(ctx.author.id, None)

        await ctx.send_success("Reset your ChatGPT context!")


async def setup(bot):
    await bot.add_cog(ChatGPT(bot))
