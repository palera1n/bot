import traceback
import discord
from discord import app_commands
from discord.ext import commands
from data.services import guild_service
from utils import GIRContext, cfg, transform_context, logger
from utils.framework import admin_and_up, guild_owner_and_up
from utils.framework.transformers import ImageAttachment


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @admin_and_up()
    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Change the bot's profile picture")
    @app_commands.describe(image="Image to use as profile picture")
    @transform_context
    async def setpfp(self, ctx: GIRContext, image: ImageAttachment):
        await self.bot.user.edit(avatar=await image.read())
        await ctx.send_success("Done!", delete_after=5)

    @guild_owner_and_up()
    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Show message when Aaron is pinged on Sabbath")
    @app_commands.describe(mode="Set mode on or off")
    @transform_context
    async def sabbath(self, ctx: GIRContext, mode: bool = None):
        g = guild_service.get_guild()
        g.sabbath_mode = mode if mode is not None else not g.sabbath_mode
        g.save()

        await ctx.send_success(f"Set sabbath mode to {'on' if g.sabbath_mode else 'off'}!")

    @commands.command()
    @commands.is_owner()
    async def carchive(self, ctx: commands.Context):
        channel = ctx.channel
        guild = ctx.guild
        bot_member = guild.get_member(self.bot.user.id)

        if ctx.author.id != cfg.owner_id:
            return

        if guild is None:
            await ctx.send("This command can only be used in a guild.")
            return

        if not bot_member.guild_permissions.administrator:
            await ctx.send("Bot does not have administrator permissions.")
            return

        await ctx.send("Attempting..")
        
        try:
            await self.archive_channel(channel)
            await ctx.send(f"Channel {channel.name} has been archived!")
        except discord.Forbidden:
            await ctx.send(f"Bot does not have permission to modify {channel.name}.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to modify {channel.name}: {e}")

    @commands.command()
    @commands.is_owner()
    async def archive(self, ctx: commands.Context):
        guild = ctx.guild
        bot_member = guild.get_member(self.bot.user.id)

        if ctx.author.id != cfg.owner_id:
            return

        if guild is None:
            await ctx.send("This command can only be used in a guild.")
            return

        if not bot_member.guild_permissions.administrator:
            await ctx.send("Bot does not have administrator permissions.")
            return

        await ctx.send("Attempting..")

        for channel in guild.channels:
            try:
                await self.archive_channel(channel)
            except discord.Forbidden:
                await ctx.send(f"Bot does not have permission to modify {channel.name}.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to modify {channel.name}: {e}")

        await ctx.send("All channels have been archived!")

    async def archive_channel(self, channel: discord.TextChannel):
        for role, overwrite in channel.overwrites.items():
            if (isinstance(role, discord.Role) or isinstance(role, discord.Member)):
                overwrite.send_messages = False
                overwrite.send_messages_in_threads = False
                overwrite.create_public_threads = False
                overwrite.create_private_threads = False
                overwrite.add_reactions = False
                await channel.set_permissions(role, overwrite=overwrite, reason="Archiving channel")

        default_overwrite = channel.overwrites_for(channel.guild.default_role)
        default_overwrite.send_messages = False
        default_overwrite.send_messages_in_threads = False
        default_overwrite.create_public_threads = False
        default_overwrite.create_private_threads = False
        default_overwrite.add_reactions = False
        await channel.set_permissions(channel.guild.default_role, overwrite=default_overwrite, reason="Archiving channel")

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guild_id: int = None):
        if ctx.author.id != cfg.owner_id:
            return

        try:
            async with ctx.typing():
                if guild_id:
                    guild = self.bot.get_guild(guild_id)
                    await self.bot.tree.sync(guild=guild)
                else:
                    await self.bot.tree.sync()
        except Exception as e:
            await ctx.send(f"An error occurred:\n```{e}```")
            logger.error(traceback.format_exc())
        else:
            await ctx.send("Synced commands!")

    @commands.command()
    @commands.is_owner()
    async def clear_guild_commands(self, ctx: commands.Context, guild_id: int):
        """Remove all commands from a specific guild."""
        if ctx.author.id != cfg.owner_id:
            return

        try:
            async with ctx.typing():

                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    await ctx.send(f"Guild with ID {guild_id} not found or not cached.")
                    return
                

                self.bot.tree.clear_commands(guild=guild)

            await ctx.send(f"Removed all commands from guild with ID {guild_id}.")
        except Exception as e:
            await ctx.send(f"An error occurred\n```{e}```")
            logger.error(traceback.format_exc())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.lower().strip() == "fr this user":
            if message.reference and isinstance(message.reference.resolved, discord.Message):
                ref_message = message.reference.resolved
                try:
                    await ref_message.add_reaction("<:fr:1024751426750132284>")
                except discord.Forbidden:
                    await print("Bot does not have permission to add reactions")
                except discord.HTTPException as e:
                    await print("Failed to add")
        if message.content.lower().strip() == "husk this user":
            if message.reference and isinstance(message.reference.resolved, discord.Message):
                ref_message = message.reference.resolved
                try:
                    await ref_message.add_reaction("<:husk:1026532993923293184>")
                except discord.Forbidden:
                    await print("Bot does not have permission to add reactions")
                except discord.HTTPException as e:
                    await print("Failed to add")

        if message.content.lower().strip() == "blobcatcozy this user":
            if message.reference and isinstance(message.reference.resolved, discord.Message):
                ref_message = message.reference.resolved
                try:
                    await ref_message.add_reaction("<:blobcatcozy:1026533070955872337>")
                except discord.Forbidden:
                    await print("Bot does not have permission to add reactions")
                except discord.HTTPException as e:
                    await print("Failed to add")
        
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Admin(bot))
