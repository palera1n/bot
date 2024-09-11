import os
import platform
from datetime import datetime
from math import floor
import socket
import platform
import subprocess

import discord
import psutil
from datetime import datetime

from data.services import user_service
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt
from utils import GIRContext, cfg, transform_context, format_number
from utils.framework import mod_and_up, whisper

def get_cpu_model():
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output("wmic cpu get caption", shell=True).decode().strip()
            return result.split('\n')[1].strip()
        elif platform.system() == "Linux":
            result = subprocess.check_output("lscpu | grep 'Model name:'", shell=True).decode().strip()
            return result.split(':')[1].strip()
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode().strip()
            return result
        else:
            return "Unknown CPU model"
    except Exception as e:
        return f"Error: {e}"

def get_gpu_model():
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output("wmic path win32_VideoController get Caption", shell=True).decode().strip()
            return result.split('\n')[1].strip()
        elif platform.system() == "Linux":
            result = subprocess.check_output("lspci | grep -i 'vga'", shell=True).decode().strip()
            return result.split(':')[2].strip()
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.check_output("system_profiler SPDisplaysDataType | grep 'Chipset Model:'", shell=True).decode().strip()
            return result.split(':')[1].strip()
        else:
            return "Unknown GPU model"
    except Exception as e:
        return f"Error: {e}"
    
def get_os_info():
    try:
        if platform.system() == "Linux":
            result = subprocess.check_output("lsb_release -a", shell=True).decode().strip()
            lines = result.split('\n')
            os_info = {}
            for line in lines:
                key, value = line.split(':', 1)
                os_info[key.strip()] = value.strip()
            return f"{os_info.get('Distributor ID', 'Unknown')} {os_info.get('Release', 'Unknown')} {os_info.get('Codename', '')}"
        
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.check_output("sw_vers", shell=True).decode().strip()
            lines = result.split('\n')
            os_info = {}
            for line in lines:
                key, value = line.split(':', 1)
                os_info[key.strip()] = value.strip()
            return f"{os_info.get('ProductName', 'Unknown')} {os_info.get('ProductVersion', 'Unknown')} {os_info.get('BuildVersion', '')}"
        
        else:
            return "OS information not available"
    
    except Exception as e:
        return f"Error: {e}"
    

def get_current_user():
    try:
        pid = os.getpid()
        process = psutil.Process(pid)
        user = process.username()
        return user
    except psutil.NoSuchProcess:
        return "unknown"
    except psutil.AccessDenied:
        return "unknown"
    except:
        return "unknown"

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()

    # @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Test server latency by measuring how long it takes to edit a message")
    @transform_context
    # @whisper
    async def ping(self, ctx: GIRContext) -> None:
        embed = discord.Embed(
            title="Pong!", color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.description = "Latency: testing..."

        # measure time between sending a message and time it is posted
        b = datetime.utcnow()

        await ctx.respond_or_edit(embed=embed, ephemeral=ctx.whisper)

        ping = floor((datetime.utcnow() - b).total_seconds() * 1000)
        embed.description = ""
        embed.add_field(name="Message Latency", value=f"`{format_number(ping)}ms`")
        embed.add_field(name="API Latency",
                        value=f"`{format_number(floor(self.bot.latency*1000))}ms`")

        await ctx.respond_or_edit(embed=embed)

    # @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Get number of users of a role")
    @app_commands.describe(role="The role's ID")
    @transform_context
    @whisper
    async def roleinfo(self, ctx: GIRContext, role: discord.Role) -> None:
        embed = discord.Embed(title="Role Statistics")
        embed.description = f"{len(role.members)} members have role {role.mention}"
        embed.color = role.color

        await ctx.respond(embed=embed, ephemeral=ctx.whisper)

    # @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Statistics about the bot")
    @transform_context
    # @whisper
    async def stats(self, ctx: GIRContext) -> None:
        process = psutil.Process(os.getpid())

        embed = discord.Embed(
            title=f"{self.bot.user.name} Statistics", color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Bot started", value=format_dt(
            self.start_time, style='R'))
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="Memory Usage",
                        value=f"{floor(process.memory_info().rss/1000/1000)} MiB")
        embed.add_field(name="Python Version", value=platform.python_version())

        await ctx.respond(embed=embed, ephemeral=ctx.whisper)


    

    # @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Statistics about OS")
    @transform_context
    # @whisper
    async def neofetch(self, ctx: GIRContext) -> None:
        now = datetime.utcnow()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = now - boot_time
        past_date = now - uptime

        embed = discord.Embed(
            title=f"{get_current_user()}@{socket.gethostname()}", color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar)

        embed.add_field(name="OS", value=get_os_info())

        embed.add_field(name="Kernel", value=f"{platform.system()} {platform.release()}")

        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{int(days)} day(s), {int(hours)} hour(s), {int(minutes)} min(s)"
        uptime_str = format_dt(past_date, style='R')

        embed.add_field(name="Uptime", value=uptime_str)
        # embed.add_field(name="CPU Model", value=get_cpu_model())
        embed.add_field(name="GPU Model", value=get_gpu_model())

        # Memory Usage
        total_memory = psutil.virtual_memory().total
        available_memory = psutil.virtual_memory().available
        used_memory = total_memory - available_memory
    
        memory_usage_total = f"{floor(used_memory / 1024 / 1024)} MiB / {floor(total_memory / 1024 / 1024)} MiB"
        embed.add_field(name="Memory", value=f"{memory_usage_total}")

        cpu_usage = psutil.cpu_percent(interval=1)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%")

        await ctx.respond(embed=embed, ephemeral=ctx.whisper)

    # @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Displays info about the server")
    @transform_context
    @whisper
    async def serverinfo(self, ctx: GIRContext):
        guild = ctx.guild
        embed = discord.Embed(title="Server Information",
                              color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon)

        if guild.banner is not None:
            embed.set_image(url=guild.banner.url)

        embed.add_field(name="Users", value=format_number(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=len(
            guild.channels) + len(guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Bans", value=len(
            self.bot.ban_cache.cache), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Tier",
                        value=guild.premium_tier, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(
            name="Created", value=f"{format_dt(guild.created_at, style='F')} ({format_dt(guild.created_at, style='R')})", inline=True)

        await ctx.respond_or_edit(embed=embed, ephemeral=ctx.whisper)

    @app_commands.guilds(cfg.guild_id)
    @app_commands.command(description="Present statistics on who has been banned for raids.")
    @transform_context
    @whisper
    async def raidstats(self, ctx: GIRContext) -> None:
        embed = discord.Embed(title="Raid Statistics",
                              color=discord.Color.blurple())
        raids = user_service.fetch_raids()

        total = 0
        for raid_type, cases in raids.items():
            total += cases
            embed.add_field(name=raid_type, value=f"{cases} cases.")

        embed.add_field(name="Total antiraid cases",
                        value=f"{total}", inline=False)
        await ctx.respond_or_edit(embed=embed, ephemeral=ctx.whisper)

    casestats = app_commands.Group(
        name="casestats", description="Interact with casestats", guild_ids=[cfg.guild_id])

    @mod_and_up()
    @casestats.command(description="Present statistics on cases by each mod.")
    @app_commands.describe(mod="Moderator to view statistics of")
    @app_commands.describe(keyword="Keyword to search for")
    @transform_context
    @whisper
    async def mod(self, ctx: GIRContext, mod: discord.Member = None, keyword: str = None) -> None:
        if mod is None:
            mod = ctx.author

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{mod}'s case statistics",
                         icon_url=mod.display_avatar)

        cases = user_service.fetch_cases_by_mod(mod.id)
        if keyword is None:
            string = ""
            for reason, count in cases.get("counts")[:5]:
                string += f"**{reason}**: {count}\n"

            if string:
                embed.add_field(name="Top reasons", value=string, inline=False)
        else:
            keyword = keyword.lower()
            total_count = 0
            string = ""
            for reason, count in cases.get("counts"):
                if keyword in reason:
                    total_count += count
                    string += f"**{reason}**: {count}\n"

            embed.add_field(name="Cases found by keyword", value=f"**{keyword}** was found in **{total_count}** of {mod.mention}'s cases", inline=False)
            embed.add_field(name="Case reasons", value=string[:1000] or "No cases", inline=False)
        
        embed.set_footer(text=f"{cases.get('total')} total cases")
        await ctx.respond_or_edit(embed=embed)

    @mod_and_up()
    @casestats.command(description="Present statistics of cases for all mods.")
    @app_commands.describe(keyword="Keyword to search for")
    @transform_context
    @whisper
    async def keyword(self, ctx: GIRContext, keyword: str) -> None:
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"Case keyword statistics",
                         icon_url=ctx.guild.icon.url)

        cases = user_service.fetch_cases_by_keyword(keyword)

        keyword = keyword.lower()

        embed.add_field(name="Keyword", value=keyword, inline=False)
        string = ""
        for reason, count in cases.get("counts")[:10]:
            string += f"**{reason}**: {count}\n"

        embed.add_field(name="Moderators", value=string[:1000] if string else "No cases", inline=False)

        embed.set_footer(text=f"{cases.get('total')} total cases")
        await ctx.respond_or_edit(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
