import discord
import asyncio
import asyncpg
import datetime

from discord.ext import commands, tasks
from utils.globalfunctions import get_main, get_comp_channel_id


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.print_comps.start()
        #self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        #self.autosign_add.start()

    #@tasks.loop(seconds=30.0)
    @commands.command()
    async def autosign_add(self, ctx):
        await self.bot.pool.execute('''
        INSERT INTO sign (playerid, raidid, playerclass)
            SELECT membershio.playerid, raid.id, membership.main
            FROM membership
            INNER JOIN raid ON membership.guildid = raid.guildid
            WHERE membership.autosign = TRUE AND raid.main = TRUE
        ON CONFLICT (playerid, raidid) DO UPDATE
        SET playerclass = excluded.playerclass
        WHERE sign.playerclass != 'Declined' ''')

    #@commands.command()
    #@tasks.loop(seconds=10.0)
    async def print_comps(self, ctx):
        guild_id = ctx.guild.id

        comp_channel_id = await get_comp_channel_id(self.bot.pool, guild_id)

        if comp_channel_id is None:
            return

        comp_channel = self.bot.get_channel(comp_channel_id)

        if comp_channel is None:
            return

        raid_cog = self.bot.get_cog('Raiding')

        raids = await self.bot.pool.fetch('''
                SELECT id, name
                FROM raid
                WHERE guildid = $1 AND main = TRUE''', guild_id)

        if raids is None:
            return

        await comp_channel.purge()

        for raid in raids:
            embed = await raid_cog.embedcomp(ctx, raid['name'])

            await asyncio.sleep(3.0)

            await comp_channel.send(embed=embed)

    #@commands.command()
    async def test_s(self, ctx):
        self.schedule_tasks.start()

    @tasks.loop(seconds=30.0)
    async def schedule_tasks(self):
        print(datetime.datetime.minute)
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
                        #if time_hours == record['cleartime']:
                        await self.run_clear(guild.id, record['id'])


    #@autosign_add.before_loop
    #@print_comps.before_loop
    #@schedule_tasks.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()

    async def run_clear(self, guild_id, raid_id):
        raid_cog = self.bot.get_cog('Raiding')
        await raid_cog.clearsigns(raid_id)
        await raid_cog.removereacts(guild_id, raid_id)

    @staticmethod
    def get_time():
        weekday = datetime.datetime.utcnow().weekday()
        hour = datetime.datetime.utcnow().hour

        time_hours = weekday*24 + hour

        return time_hours


def setup(bot):
    bot.add_cog(Background(bot))
