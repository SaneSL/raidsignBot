import discord
import asyncio
import asyncpg

from discord.ext import tasks, commands
from globalfunctions import getplayerclass


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        # self.autosign_add.start()

    @tasks.loop(seconds=60.0)
    async def autosign_add(self):
        mainraids = ["MC", "BWL", "AQ40", "NAXX"]

        for guild in self.bot.guilds:
            mainevents = []
            placeholdertuples = []

            role = discord.utils.get(guild.roles, name='AutoSign')
            guild_id = guild.id

            raids = await self.bot.db.fetch('''
                    SELECT id, name
                    FROM raid
                    WHERE guildid = $1''', guild_id)

            if raids is None:
                continue

            for record in raids:
                if record['name'] in mainraids:
                    mainevents.append(record['id'])

            members = role.members
            for member in members:

                player_id = member.id

                playerclass = await getplayerclass(self.bot.db, guild_id, player_id)

                if playerclass is None:
                    continue

                for raid_id in mainevents:
                    new_tuple = (player_id, raid_id, playerclass)
                    placeholdertuples.append(new_tuple)

            print(placeholdertuples)
            await self.bot.db.executemany('''
                                        INSERT INTO sign (playerid, raidid, playerclass)
                                        VALUES ($1, $2, $3)
                                        ON CONFLICT (playerid, raidid) DO UPDATE
                                        SET playerclass = $3''', placeholdertuples)

    @autosign_add.before_loop
    async def before_autosign(self):
        await self.bot.wait_until_ready()

    # Testing, change_interval introduced in next versio, which is not out yet.
    @commands.command()
    async def change_timer(self, ctx):
        self.autosign_add.cancel()
        # self.autosign_add.change_interval(seconds=5)


def setup(bot):
    bot.add_cog(Background(bot))
