import os
import random
from datetime import datetime, timedelta

import discord
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data.model import Case
from data.services import guild_service, user_service

from pytz import utc

from utils import cfg

executors = {
    'default': ThreadPoolExecutor(20)
}

job_defaults = {
    # 'coalesce': True
}

BOT_GLOBAL = None


class Tasks():
    """Job scheduler for unmute, using APScheduler"""

    def __init__(self, bot: discord.Client):
        """Initialize scheduler

        Parameters
        ----------
        bot : discord.Client
            instance of Discord client

        """

        global BOT_GLOBAL
        BOT_GLOBAL = bot

        # logging.basicConfig()
        # logging.getLogger('apscheduler').setLevel(logging.DEBUG)

        if os.environ.get("DB_CONNECTION_STRING") is None:
            jobstores = {
                'default': MongoDBJobStore(database="botty", collection="jobs", host=os.environ.get("DB_HOST"), port=int(os.environ.get("DB_PORT"))),
            }
        else:
            jobstores = {
                'default': MongoDBJobStore(database="botty", collection="jobs", host=os.environ.get("DB_CONNECTION_STRING")),
            }

        self.tasks = AsyncIOScheduler(
            jobstores=jobstores, executors=executors, job_defaults=job_defaults, event_loop=bot.loop, timezone=utc)
        self.tasks.start()

    def schedule_untimeout(self, _id: int, date: datetime) -> None:
        """Create a task to unmute user given by ID `_id`, at time `date`

        Parameters
        ----------
        _id : int
            User to unmute
        date : datetime.datetime
            When to unmute

        """

        self.tasks.add_job(untimeout_callback, 'date', id=str(
            _id), next_run_time=date, args=[_id], misfire_grace_time=3600)

    def schedule_remove_bday(self, _id: int, date: datetime) -> None:
        """Create a task to remove birthday role from user given by ID `_id`, at time `date`

        Parameters
        ----------
        _id : int
            User to remove role
        date : datetime.datetime
            When to remove role

        """

        self.tasks.add_job(remove_bday_callback, 'date', id=str(
            _id+1), next_run_time=date, args=[_id], misfire_grace_time=3600)

    def cancel_unmute(self, _id: int) -> None:
        """When we manually unmute a user given by ID `_id`, stop the task to unmute them.

        Parameters
        ----------
        _id : int
            User whose unmute task we want to cancel

        """

        self.tasks.remove_job(str(_id), 'default')

    def cancel_unmute(self, id: int) -> None:
        """When we manually unmute a user given by ID `_id`, stop the task to unmute them.

        Parameters
        ----------
        _id : int
            User whose unmute task we want to cancel

        """

        self.tasks.remove_job(str(id), 'default')

    def cancel_unbirthday(self, _id: int) -> None:
        """When we manually unset the birthday of a user given by ID `_id`, stop the task to remove the role.

        Parameters
        ----------
        _id : int
            User whose task we want to cancel

        """
        self.tasks.remove_job(str(_id+1), 'default')

    def schedule_end_giveaway(self, channel_id: int, message_id: int, date: datetime, winners: int) -> None:
        """
        Create a task to end a giveaway with message ID `_id`, at date `date`

        Parameters
        ----------
        channel_id : int
            ID of the channel that the giveaway is in
        message_id : int
            Giveaway message ID
        date : datetime.datetime
            When to end the giveaway

        """

        self.tasks.add_job(end_giveaway_callback, 'date', id=str(
            message_id+2), next_run_time=date, args=[channel_id, message_id, winners], misfire_grace_time=3600)

    def schedule_reminder(self, _id: int, guild: int, channel: int, reminder: str, date: datetime) -> None:
        """Create a task to remind someone of id `_id` of something `reminder` at time `date`

        Parameters
        ----------
        _id : int
            User to remind
        reminder : str
            What to remind them of
        date : datetime.datetime
            When to remind

        """

        self.tasks.add_job(reminder_callback, 'date', id=str(
            _id+random.randint(5, 100)), next_run_time=date, args=[_id, guild, channel, reminder], misfire_grace_time=3600)

    def schedule_remove_new_member_role(self, member_id: int) -> None:
        """Create a task to remove new member role from user given by ID `_id`, at time `date`

        Parameters
        ----------
        _id : int
            User to remove role
        date : datetime.datetime
            When to remove role

        """

        day_from_now = datetime.now() + timedelta(days=1)
        self.tasks.add_job(remove_new_member_role_callback, 'date', id=str(
            member_id+random.randint(100, 200)), next_run_time=day_from_now, args=[member_id], misfire_grace_time=3600)


def untimeout_callback(_id: int) -> None:
    """Callback function for actually unmuting. Creates asyncio task
    to do the actual unmute.

    Parameters
    ----------
    _id : int
        User who we want to unmute

    """

    BOT_GLOBAL.loop.create_task(remove_timeout(_id))


async def remove_timeout(_id: int) -> None:
    """Remove the mute role of the user given by ID `_id`

    Parameters
    ----------
    _id : int
        User to unmute

    """

    db_guild = guild_service.get_guild()

    case = Case(
        _id=db_guild.case_id,
        _type="UNMUTE",
        mod_id=BOT_GLOBAL.user.id,
        mod_tag=str(BOT_GLOBAL.user),
        reason="Temporary mute expired.",
    )
    guild_service.inc_caseid()
    user_service.add_case(_id, case)

    guild = BOT_GLOBAL.get_guild(cfg.guild_id)
    user: discord.Member = guild.get_member(_id)
    if user is None:
        return

    await user.edit(timed_out_until=None)

    # i know. this sucks.
    from utils.mod import prepare_unmute_log
    log = prepare_unmute_log(BOT_GLOBAL.user, user, case)
    log.remove_author()
    log.set_thumbnail(url=user.display_avatar)

    public_chan = guild.get_channel(cfg.channels.public_logs)

    dmed = True
    try:
        await user.send(embed=log)
    except Exception:
        dmed = False

    await public_chan.send(user.mention if not dmed else "", embed=log)


def reminder_callback(id: int, guild: int, channel: int, reminder: str):
    BOT_GLOBAL.loop.create_task(remind(id, guild, channel, reminder))


async def remind(_id, guild_id, channel_id, reminder):
    """Remind the user callback

    Parameters
    ----------
    _id : int
        ID of user to remind
    channel_id : int
        ID of the channel to fall back to if DM fails
    reminder : str
        body of reminder

    """

    guild = BOT_GLOBAL.get_guild(guild_id)
    if guild is None:
        return
    
    member = guild.get_member(_id)
    if member is None:
        return

    embed = discord.Embed(
        title="Reminder!",
        description=f"*You wanted me to remind you something... What was it... Oh right*:\n\n{reminder}",
        color=discord.Color.random()
    )
    
    try:
        await member.send(embed=embed)
    except Exception:
        try:
            channel = await guild.fetch_channel(channel_id)
            await channel.send(f"{member.mention}", embed=embed)
        except discord.NotFound:
            print("Channel not found.")
        except discord.Forbidden:
            print("Bot doesn't have permission to access the channel.")
        except discord.HTTPException as e:
            print(f"HTTP exception occurred: {e}")



def remove_bday_callback(_id: int) -> None:
    """Callback function for actually unmuting. Creates asyncio task
    to do the actual unmute.

    Parameters
    ----------
    _id : int
        User who we want to unmute

    """

    BOT_GLOBAL.loop.create_task(remove_bday(_id))


async def remove_bday(_id: int) -> None:
    """Remove the bday role of the user given by ID `_id`

    Parameters
    ----------
    _id : int
        User to remove role of

    """

    guild = BOT_GLOBAL.get_guild(cfg.guild_id)
    if guild is None:
        return

    bday_role = cfg.roles.birthday
    bday_role = guild.get_role(bday_role)
    if bday_role is None:
        return

    user = guild.get_member(_id)
    await user.remove_roles(bday_role)


def end_giveaway_callback(channel_id: int, message_id: int, winners: int) -> None:
    """
    Callback function for ending a giveaway

    Parameters
    ----------
    channel_id : int
        ID of the channel that the giveaway is in
    message_id : int
        Message ID of the giveaway

    """

    BOT_GLOBAL.loop.create_task(end_giveaway(channel_id, message_id, winners))


async def end_giveaway(channel_id: int, message_id: int, winners: int) -> None:
    """
    End a giveaway.

    Parameters
    ----------
    channel_id : int
        ID of the channel that the giveaway is in
    message_id : int
        Message ID of the giveaway

    """

    guild = BOT_GLOBAL.get_guild(cfg.guild_id)
    channel = guild.get_channel(channel_id)

    if channel is None:
        return
    try:
        message = await channel.fetch_message(message_id)
    except Exception:
        return

    embed = message.embeds[0]
    embed.set_footer(text="Ended")
    embed.set_field_at(0, name="Time remaining",
                       value="This giveaway has ended.")
    embed.timestamp = datetime.now()
    embed.color = discord.Color.default()

    reaction = message.reactions[0]
    reacted_ids = [user.id async for user in reaction.users()]
    reacted_ids.remove(BOT_GLOBAL.user.id)

    if len(reacted_ids) < winners:
        winners = len(reacted_ids)

    rand_ids = random.sample(reacted_ids, winners)
    winner_ids = []
    mentions = []
    tries = 0
    for user_id in rand_ids:
        tries += 1
        member = guild.get_member(user_id)
        # ensure that member hasn't left the server while simultaneously ensuring that we don't add duplicate members if we select a new random one
        while member is None or member.mention in mentions:
            tries += 1
            if tries > winners + 20:
                member = None
                break
            member = guild.get_member(random.choice(reacted_ids))
        if member is not None:
            mentions.append(member.mention)
            winner_ids.append(member.id)

    g = guild_service.get_giveaway(_id=message.id)
    g.entries = reacted_ids
    g.is_ended = True
    g.previous_winners = winner_ids
    g.save()

    await message.edit(embed=embed)
    await message.clear_reactions()

    if not mentions:
        await channel.send(f"No winner was selected for the giveaway of **{g.name}** because nobody entered.")
        return

    if winners == 1:
        await channel.send(f"Congratulations {mentions[0]}! You won the giveaway of **{g.name}**! Please DM or contact <@{g.sponsor}> to collect.")
    else:
        await channel.send(f"Congratulations {', '.join(mentions)}! You won the giveaway of **{g.name}**! Please DM or contact <@{g.sponsor}> to collect.")

def remove_new_member_role_callback(member_id: int) -> None:
    """Callback function for actually removing new member role. Creates asyncio task
    to do the actual removal.

    Parameters
    ----------
    _id : int
        User who we want to remove the role from

    """

    BOT_GLOBAL.loop.create_task(remove_new_member_role(member_id))

async def remove_new_member_role(member_id: int) -> None:
    """Remove the new member role of the user given by ID `_id`

    Parameters
    ----------
    role : int
        Role to remove
    member_id : int
        User to remove role of

    """

    guild = BOT_GLOBAL.get_guild(cfg.guild_id)
    if guild is None:
        return

    new_member_role = cfg.roles.new_member
    new_member_role = guild.get_role(new_member_role)
    if new_member_role is None:
        return

    user = guild.get_member(member_id)
    await user.remove_roles(new_member_role)
