import discord
import asyncio
import asyncpg

from discord.ext import tasks, commands
from globalfunctions import getplayerclass


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        self.autosign_add.start()

    @tasks.loop(seconds=10.0)
    async def autosign_add(self):

        mainraids = ["MC", "BWL", "AQ40", "NAXX"]

        print("LETS GO")

        for guild in self.bot.guilds:
            role = discord.utils.get(guild.roles, name='AutoSign')
            guild_id = guild.id
            members = role.members
            for member in members:
                player_id = member.id

                playerclass = getplayerclass(self.bot.db, guild_id, player_id)
                if playerclass is None:
                    continue

                await self.bot.db.execute('''
                INSERT INTO sign
                VALUES ($1, $2, $3)
                ON CONFLICT (playerid, raidid) DO UPDATE
                SET playerclass = $3
                WHERE playerclass != 'Declined'
                ''', guild_id, player_id, playerclass)
        print("DONE")

    @autosign_add.before_loop
    async def before_autosign(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Background(bot))
