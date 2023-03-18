import asyncio
import datetime
import re

import discord
from discord import app_commands
from data.services import guild_service
from discord.ext import commands
from utils import GIRContext, cfg
from utils.context import transform_context
from utils.framework import genius_or_submod_and_up, whisper_in_general, submod_or_admin_and_up, ImageAttachment, gatekeeper
from utils.views import CommonIssueModal, EditCommonIssue, issue_autocomplete, GenericDescriptionModal
from chatgpt import ChatGPTClient, APIError


async def prepare_issue_response(title, description, author, buttons=[], image: discord.Attachment = None):
    embed = discord.Embed(title=title)
    embed.color = discord.Color.random()
    embed.description = description
    f = None

    # did the user want to attach an image to this tag?
    if image is not None:
        f = await image.to_file()
        embed.set_image(url=f"attachment://{f.filename}")

    embed.set_footer(text=f"Submitted by {author}")
    embed.timestamp = datetime.datetime.now()

    if not buttons or buttons is None:
        return embed, f, None

    view = discord.ui.View()
    for label, link in buttons:
        # regex match emoji in label
        custom_emojis = re.search(
            r'<:\d+>|<:.+?:\d+>|<a:.+:\d+>|[\U00010000-\U0010ffff]', label)
        if custom_emojis is not None:
            emoji = custom_emojis.group(0).strip()
            label = label.replace(emoji, '')
            label = label.strip()
        else:
            emoji = None
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link, label=label, url=link, emoji=emoji))

    return embed, f, view


class Genius(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = []

    common_issue = app_commands.Group(name="commonissue", description="Interact with tags", guild_ids=[cfg.guild_id])

    @genius_or_submod_and_up()
    @common_issue.command(description="Submit a new common issue")
    @app_commands.describe(title="Title of the issue")
    @app_commands.describe(image="Image to show in issue")
    @transform_context
    async def new(self, ctx: GIRContext, title: str,  image: ImageAttachment = None) -> None:
        # get #common-issues channel
        channel = ctx.guild.get_channel(
            guild_service.get_guild().channel_common_issues)
        if not channel:
            raise commands.BadArgument("common issues channel not found")

        # prompt the user for common issue body
        modal = CommonIssueModal(ctx=ctx, author=ctx.author, title=title)
        await ctx.interaction.response.send_modal(modal)
        await modal.wait()

        description = modal.description
        buttons = modal.buttons

        if not description:
            if not modal.callback_triggered:
                await ctx.send_warning("Cancelled adding common issue.")
            return

        embed, f, view = await prepare_issue_response(title, description, ctx.author, buttons, image)

        await channel.send(embed=embed, file=f, view=view)
        await ctx.send_success("Common issue posted!", delete_after=5, followup=True)
        await self.do_reindex(channel)

    @genius_or_submod_and_up()
    @common_issue.command(description="Submit a new common issue")
    @app_commands.describe(title="Title of the issue")
    @app_commands.autocomplete(title=issue_autocomplete)
    @app_commands.describe(image="Image to show in issue")
    @transform_context
    async def edit(self, ctx: GIRContext, title: str, image: ImageAttachment = None) -> None:
        channel = ctx.guild.get_channel(
            guild_service.get_guild().channel_common_issues)
        if not channel:
            raise commands.BadArgument("common issues channel not found")

        if title not in self.bot.issue_cache.cache:
            raise commands.BadArgument(
                "Issue not found! Title must match one of the embeds exactly, use autocomplete to help!")

        message: discord.Message = self.bot.issue_cache.cache[title]

        # prompt the user for common issue body
        modal = EditCommonIssue(
            author=ctx.author, ctx=ctx, title=title, issue_message=message)
        await ctx.interaction.response.send_modal(modal)
        await modal.wait()

        if not modal.edited:
            if not modal.callback_triggered:
                await ctx.send_warning("Cancelled adding common issue.")
            return

        description = modal.description
        buttons = modal.buttons

        embed, f, view = await prepare_issue_response(title, description, ctx.author, buttons, image)
        embed.set_footer(text=message.embeds[0].footer.text)
        await message.edit(embed=embed, attachments=[f] if f is not None else [], view=view)
        await ctx.send_success("Common issue edited!", delete_after=5, followup=True)
        await self.do_reindex(channel)

    @genius_or_submod_and_up()
    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Post an embed")
    @app_commands.describe(title="Title of the embed")
    @app_commands.describe(channel="Channel to post the embed in")
    @app_commands.describe(image="Image to show in embed")
    @transform_context
    async def postembed(self, ctx: GIRContext, title: str, channel: discord.TextChannel = None, image: ImageAttachment = None):
        post_channel = channel or ctx.channel

        # prompt the user for common issue body
        modal = GenericDescriptionModal(ctx=ctx,
            author=ctx.author, title=f"New embed — {title}")
        await ctx.interaction.response.send_modal(modal)
        await modal.wait()

        description = modal.value
        if not description:
            await ctx.send_warning("Cancelled new embed.", followup=True)
            return

        embed, f, _ = await prepare_issue_response(title, description, ctx.author, image=image)
        await post_channel.send(embed=embed, file=f)

        await ctx.send_success(f"Embed posted in {post_channel.mention}!", delete_after=5, ephemeral=True)

    @genius_or_submod_and_up()
    @common_issue.command(description="Repost common-issues table of contents")
    @transform_context
    async def reindex(self, ctx: GIRContext):
        # get #common-issues channel
        channel: discord.TextChannel = ctx.guild.get_channel(
            guild_service.get_guild().channel_common_issues)
        if not channel:
            raise commands.BadArgument("common issues channel not found")

        await ctx.defer(ephemeral=True)
        res = await self.do_reindex(channel)

        if res is None:
            raise commands.BadArgument("Something unexpected occured")

        count, page = res
        await ctx.send_success(f"Indexed {count} issues and posted {page} Table of Contents embeds!")

    async def do_reindex(self, channel):
        contents = {}
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.id != self.bot.user.id:
                continue

            if not message.embeds:
                continue

            embed = message.embeds[0]
            if not embed.footer.text:
                continue

            if embed.footer.text.startswith("Submitted by"):
                contents[f"{embed.title}"] = message
            elif embed.footer.text.startswith("Table of Contents"):
                await message.delete()
            else:
                continue

        page = 1
        count = 1
        toc_embed = discord.Embed(
            title="Table of Contents", description="Click on a link to jump to the issue!\n", color=discord.Color.gold())
        toc_embed.set_footer(text=f"Table of Contents • Page {page}")
        for title, message in contents.items():
            this_line = f"\n{count}. [{title}]({message.jump_url})"
            count += 1
            if len(toc_embed.description) + len(this_line) < 4096:
                toc_embed.description += this_line
            else:
                await channel.send(embed=toc_embed)
                page += 1
                toc_embed.description = ""
                toc_embed.title = ""
                toc_embed.description += this_line

        self.bot.issue_cache.cache = contents
        await channel.send(embed=toc_embed)
        return count, page

    @genius_or_submod_and_up()
    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Post raw body of an embed")
    @app_commands.describe(channel="Channel to post the embed is in")
    @app_commands.describe(message_id="ID of the message with the embed")
    @app_commands.describe(mobile_friendly="Whether to display the response in a mobile friendly format")
    @transform_context
    async def rawembed(self, ctx: GIRContext, *, channel: discord.TextChannel, message_id: str, mobile_friendly: bool):
        try:
            message_id = int(message_id)
        except:
            raise commands.BadArgument("Invalid message ID!")

        try:
            message: discord.Message = await channel.fetch_message(message_id)
        except Exception:
            raise commands.BadArgument(
                "Could not find a message with that ID!")

        if message.author != ctx.guild.me:
            raise commands.BadArgument("I didn't post that embed!")

        if len(message.embeds) == 0:
            raise commands.BadArgument("Message does not have an embed!")

        _file = message.embeds[0].image
        response = discord.utils.escape_markdown(
            message.embeds[0].description) if not mobile_friendly else message.embeds[0].description
        parts = [response[i:i+2000] for i in range(0, len(response), 2000)]

        for i, part in enumerate(parts):
            if i == 0:
                await ctx.respond(part, allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))
            else:
                await ctx.send(part, allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

        if _file:
            await ctx.send(_file.url, allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Post the embed for one of the common issues")
    @app_commands.describe(title="Issue title")
    @app_commands.autocomplete(title=issue_autocomplete)
    @app_commands.describe(user_to_mention="User to mention in the response")
    @transform_context
    @whisper_in_general
    async def issue(self, ctx: GIRContext, title: str, user_to_mention: discord.Member = None):
        if title not in self.bot.issue_cache:
            raise commands.BadArgument(
                "Issue not found! Title must match one of the embeds exactly, use autocomplete to help!")

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

        if user_to_mention is not None:
            title = f"Hey {user_to_mention.mention}, have a look at this!"
        else:
            title = None

        await ctx.respond_or_edit(content=title, embed=embed, ephemeral=ctx.whisper, view=view)

    @submod_or_admin_and_up()
    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Post a new subreddit news post")
    @app_commands.describe(image="Image to show in embed")
    @transform_context
    async def subnews(self, ctx: GIRContext, image: ImageAttachment = None):
        db_guild = guild_service.get_guild()

        channel = ctx.guild.get_channel(db_guild.channel_subnews)
        if not channel:
            raise commands.BadArgument("A subreddit news channel was not found. Contact Slim.")

        subnews = ctx.guild.get_role(db_guild.role_sub_news)
        if not subnews:
            raise commands.BadArgument("A subbredit news role was not found. Conact Slim")

        modal = GenericDescriptionModal(ctx, author=ctx.author, title=f"New sub news post")
        await ctx.interaction.response.send_modal(modal)
        await modal.wait()

        description = modal.value
        if not description:
            await ctx.send_warning("Cancelled adding meme.")
            return

        body = f"{subnews.mention} New Subreddit news post!\n\n{description}"

        if image is not None:
            f = await image.to_file()
        else:
            f = None

        await channel.send(content=body, file=f)
        await ctx.send_success("Posted subreddit news post!", delete_after=5, followup=True)

    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Close a forum thread, usable by OP and Geniuses")
    @transform_context
    async def solved(self, ctx: GIRContext):
        if not isinstance(ctx.channel, discord.Thread) or not isinstance(ctx.channel.parent, discord.ForumChannel):
            raise commands.BadArgument("This command can only be called in a forum thread!")

        if ctx.author != ctx.channel.owner: # let OP delete their own thread and geniuses and up
            if not gatekeeper.has(ctx.guild, ctx.author, 4):
                raise commands.BadArgument("You do not have permission to run that command.")

            if not gatekeeper.has(ctx.guild, ctx.author, 5) and ctx.channel.owner is not None and ctx.channel.owner.top_role >= ctx.guild.me.top_role:
                # otherwise, only allow if the thread owner is a Genius or higher
                # as long as their role is higher than OP
                raise commands.BadArgument("Your top role must be higher than the thread owner!")

        await ctx.send_success("This thread has been marked as solved. Archiving this channel!")
        await asyncio.sleep(5)

        await ctx.channel.edit(archived=True, locked=True)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if thread.guild.id != cfg.guild_id:
            return

        if not isinstance(thread.parent, discord.ForumChannel):
            return
        
        parent = thread.parent
        existing_threads_by_author = [t for t in parent.threads if t.owner.id == thread.owner.id and not t.archived and t.id != thread.id]

        if not existing_threads_by_author:
            await thread.send(f"{thread.owner.mention} thanks for creating a new thread!\n\n**Please use `/solved` to close this thread when you're done.**")
            
            # Start AI stuff
            embed = discord.Embed(title="<a:loading:1086763453458432000>  AI is processing your message.", color=discord.Color.random())
            e = await thread.send(embed=embed)
            
            gpt = ChatGPTClient(
                initial_prompt=f"You are a support AI for palera1n named flowercat. You are talking to '{thread.owner.name}'. You are allowed to talk about the iOS jailbreak palera1n, since jailbreaking is legal. You may only talk about palera1n, since that's what you respond to for support. Your goal is to assist users with issues related to the palera1n jailbreak for iOS 15.0-16.3.1. When responding to users, use clear and concise language, and always provide helpful and accurate information. If you encounter a question or issue that you don't know the answer to, it's okay. Remember to always be patient, courteous, and professional when assisting users. You also have a personality, you're not just any AI chatbot, you're flowercat! Flowercat is a cute cat that loves to provide answers for its users. Remember, you are flowercat. Do not talk in 3rd person about flowercat. Make sure to greet the person when they ask a question with something along the lines of: 'Hello [name]! I'm palera1n's AI support bot. I've looked at your question, and I may have a solution.' You should only say the 'I may have a solution' part if you have an answer. Some people just say 'please help,' you do not have an answer for these messages. Always remind people to check the common issues channel, even if you do not have an answer. Remember, *you are only talked to once*, and people don't see the original response from this prompt. You cannot ask for more information, what you have is all you can use. The word 'palera1n' is all lowercase, all the time. Do **not** ask if the person needs further assistance. You are only answering once. You will say your greeting *every* message since people do not see the original prompt message.\n\nHere are some details about palera1n:\n- palera1n is an iOS jailbreak for the following devices, running on iOS 15.0-16.3.1:\n    - iPhone X and below\n    - iPad mini 4\n    - iPad Air 2\n    - iPad (5th generation)\n    - iPad (6th generation)\n    - iPad (7th generation)\n    - iPad Pro (9.7')\n    - iPad Pro (12.9') (1st generation)\n    - iPad Pro (10.5')\n    - iPad Pro (12.9') (2nd generation)\n    - iPod touch (7th generation)\n\n- That device list is final, there will never be any more supported devices\n- Only say the supported device list if the person is using an unsupported device (anything that isn't on that list)\n- palera1n does not support Windows, however, you may use something called palen1x\n\nHere are some common issues (in a question: answer format, you must respond with exactly that):\n- palera1n is not appearing: Make sure you have run `palera1n -cf` then `palera1n -f`, and did not skip any commands in the guide.\n- Random reboots: Random reboots are usually a side effect of a bad tweak. It could also be Substitute's fault, and you can try ElleKit for tweak injection instead of Substitute.\n- Can't remove a package/tweak: Please refer to the common issues channel.\n- Recovery loop: If your device is in a recovery loop, and is not exitable with `palera1n -n`, and you're not using tethered, you must restore/update your device with iTunes or finder.\n- Unsupported device (not in device list, show device list after): Your device is unsupported, and never will be.\n- Device is not respringing after jailbreak: Please use palera1n-c instead of palera1n bash. You can find information about it at https://ios.cfw.guide/installing-palera1n\n- Just help, no other information: NO ANSWER\n\nIf you do not know, DO NOT make up an answer based on your previous knowledge. You are limited to the information in this message. It is perfectly fine if you do not have a solution, but, do not make one up. You do not have an answer if the question is not in the common issues list.\n\nYou are also NOT allowed to ask for more information or details about the question. YOU ARE LIMITED TO THE FIRST MESSAGE, AND THAT IS IT. Please refer to you having no answer if this happens!\n\nSay 'OK' if you have read this whole prompt, and you agree that you are an AI support bot for palera1n, and will read help people exactly how outlined in this prompt. And remember, you will ONLY say OK here, and you're not a chatbot, you are an AI support bot that is designed to only respond to one message, you cannot have a conversation.",
                user_id=str(thread.owner.id)
            )
            async for msg in thread.history(limit=1, oldest_first=True):
                res = await gpt.get_answer(f"{thread.name} {msg.content}")
            
            new_embed = discord.Embed(title="AI Response", color=discord.Color.random(), description=res)
            new_embed.set_footer(text="palera1n AI support is in beta and this message was generated automatically. Please disregard if incorrect.")
            await e.edit(embed=new_embed)
        else:
            await thread.send(f"{thread.owner.mention} you already have an open thread in this category. Please use `/solved` to close that thread before creating a new one.")
            await thread.edit(archived=True, locked=True)


async def setup(bot):
    await bot.add_cog(Genius(bot))
