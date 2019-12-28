import asyncio
import asyncpg
import datetime

from discord.ext import commands, tasks
from .utils.globalfunctions import get_comp_channel_id


class Background(commands.Cog):
    """
    This class impelements tasks that are run periodically on the background

    Attributes
    ----------
    bot
    last_clear
        The last time when events were autocleared.
    """
    def __init__(self, bot):
        self.bot = bot
        self.last_clear = self.get_time()
        self.autosign_add.start()
        self.print_comps.start()
        self.schedule_tasks.start()
        self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        self.print_comps.add_exception_type(asyncpg.PostgresConnectionError)
        self.schedule_tasks.add_exception_type(asyncpg.PostgresConnectionError)


    @tasks.loop(minutes=15.0)
    async def autosign_add(self):
        """
        Adds users with autosign enabled to 'main' raids every 15 minutes
        """
        await self.bot.pool.execute('''
        INSERT INTO sign (playerid, raidid, playerclass, spec)
            SELECT membership.playerid, raid.id, membership.main, membership.mainspec
            FROM membership
            INNER JOIN raid ON membership.guildid = raid.guildid
            WHERE membership.autosign = TRUE AND raid.main = TRUE
        ON CONFLICT (playerid, raidid) DO UPDATE
        SET playerclass = excluded.playerclass, spec = excluded.spec
        WHERE sign.playerclass != 'Declined' ''')

    async def print_comps_helper(self, guild):
        """
        Helps print_comps to send embeds

        Parameters
        ----------
        guild
            Instance of Guild

        Returns
        -------
        None if guild doesn't have any raids
        """

        guild_id = guild.id
        comp_channel_id = await get_comp_channel_id(self.bot.pool, guild_id)

        if comp_channel_id is None:
            return

        comp_channel = self.bot.get_channel(comp_channel_id)

        if comp_channel is None:
            return

        raid_cog = self.bot.get_cog('Raid')

        raids = await self.bot.pool.fetch('''
                SELECT id, name
                FROM raid
                WHERE guildid = $1''', guild_id)

        if raids is None:
            return

        await comp_channel.purge()

        for raid in raids:
            embed = await raid_cog.embedcomp(guild, raid['name'])
            await comp_channel.send(embed=embed)
            await asyncio.sleep(11.0)

    @tasks.loop(minutes=20.0)
    async def print_comps(self):
        """
        Sends updated raidcomps to all guilds every 20 minutes
        """

        gather_list = []
        for guild in self.bot.guilds:
            gather_list.append(self.print_comps_helper(guild))

        await asyncio.gather(*gather_list)

    @tasks.loop(hours=1.0)
    async def schedule_tasks(self):
        """
        Schedules run_clear for raids if it has been setup for raid by user
        """
        time_hours = self.get_time()

        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                for guild in self.bot.guilds:
                    async for record in con.cursor('''
                    SELECT id, cleartime
                    FROM raid
                    WHERE guildid = $1''', guild.id):
                        if record['cleartime'] is None:
                            continue
                        if self.last_clear <= record['cleartime'] <= time_hours:
                            await self.run_clear(guild, record['id'])

        self.last_clear = time_hours

    @autosign_add.before_loop
    @print_comps.before_loop
    @schedule_tasks.before_loop
    async def before_tasks(self):
        """
        Waits decorated tasks to from starting before bot is ready
        """

        await self.bot.wait_until_ready()

    async def run_clear(self, guild, raid_id):
        """
        Clears signs from raid

        Parameters
        ----------
        guild
            Discord server's ID
        raid_id
        """

        raid_cog = self.bot.get_cog('Raid')
        await raid_cog.clearsigns(raid_id)
        await raid_cog.removereacts(guild, raid_id)

    @staticmethod
    def get_time():
        """
        Gets current week day and hour in hours

        Returns
        -------
        Time in hours
        """

        weekday = datetime.datetime.utcnow().weekday()
        hour = datetime.datetime.utcnow().hour

        time_hours = weekday*24 + hour

        return time_hours


def setup(bot):
    bot.add_cog(Background(bot))
