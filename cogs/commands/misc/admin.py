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
    async def sync(self, ctx: commands.Context, guild_id: int = None):
        if ctx.author.id != cfg.owner_id:
            return

        try:
            async with ctx.typing():
                await self.bot.tree.sync()
        except Exception as e:
            await ctx.send(f"An error occured\n```{e}```")
            logger.error(traceback.format_exc())
        else:
            await ctx.send("Done!")


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

async def setup(bot):
    await bot.add_cog(Admin(bot))
