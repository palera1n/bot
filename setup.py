import asyncio
import os

import mongoengine
from dotenv import find_dotenv, load_dotenv

from data.model.guild import Guild

load_dotenv(find_dotenv())


async def setup():
    print("STARTING SETUP...")
    guild = Guild()

    # you should have this setup in the .env file beforehand
    guild._id = int(os.environ.get("MAIN_GUILD_ID"))

    # If you're re-running this script to update a value, set case_id
    # to the last unused case ID or else it will start over from 1!
    guild.case_id = 20

    # required for permissions framework!
    # put in the role IDs for your server here
    guild.role_administrator = 1028399096005939291
    # put in the role IDs for your server here
    guild.role_moderator = 1028708867225423882
    # put in the role IDs for your server here
    guild.role_birthday = 1028693847976452146
    guild.role_genius = 123  # put in the role IDs for your server here
    guild.role_dev = 1028725253712662680  # put in the role IDs for your server here
    # put in the role IDs for your server here
    guild.role_memberone = 1028693923008364586
    # put in the role IDs for your server here
    guild.role_memberedition = 1028693929958326293
    # put in the role IDs for your server here
    guild.role_memberpro = 1028693987751624804
    # put in the role IDs for your server here
    guild.role_memberplus = 1028693990641508473
    guild.role_memberultra = 123  # put in the role IDs for your server here

    # put in the channel IDs for your server here
    guild.channel_reports = 1028693758910414998
    # channel where geniuses can report to
    # put in the channel IDs for your server here
    guild.channel_mempro_reports = 123
    # channel where reactions will be logged
    # put in the channel IDs for your server here
    guild.channel_emoji_log = 1028693728589787156
    # channel for private mod logs
    # put in the channel IDs for your server here
    guild.channel_private = 1028692082132529172
    # channel where self-assignable roles will be posted
    # put in the channel IDs for your server here
    guild.channel_reaction_roles = 1028693665050263612
    # rules-and-info channel
    # put in the channel IDs for your server here
    guild.channel_rules = 1028691704284450877
    # channel for public mod logs
    # put in the channel IDs for your server here
    guild.channel_public = 1028693426050433064
    # optional, required for /issue command
    # put in the channel IDs for your server here
    guild.channel_common_issues = 1028693596469207191
    # #general, required for permissions
    # put in the channel IDs for your server here
    guild.channel_general = 1028398976640229380
    # required for filter
    # put in the channel IDs for your server here
    guild.channel_development = 1028692204778160249
    # required, #bot-commands channel
    # put in the channel IDs for your server here
    guild.channel_botspam = 1028692189066317834
    # optional, needed for booster #emote-suggestions channel
    guild.channel_booster_emoji = 123  # put in the channel IDs for your server here

    # you can fill these in if you want with IDs, or you ca use commands later
    # put in a channel if you want (ignored in logging)
    guild.logging_excluded_channels = []
    # put in a channel if you want (ignored in filter)
    guild.filter_excluded_channels = []
    # put guild ID to whitelist in invite filter if you want
    guild.filter_excluded_guilds = []

    # you can leave this as is if you don't want Blootooth (message mirroring system)
    guild.nsa_guild_id = 1028692393312133252

    guild.save()
    print("DONE")

if __name__ == "__main__":
    if os.environ.get("DB_CONNECTION_STRING") is None:
        mongoengine.register_connection(
            host=os.environ.get("DB_HOST"), port=int(os.environ.get("DB_PORT")), alias="default", name="botty")
    else:
        mongoengine.register_connection(
            host=os.environ.get("DB_CONNECTION_STRING"), alias="default", name="botty")
    res = asyncio.get_event_loop().run_until_complete(setup())
