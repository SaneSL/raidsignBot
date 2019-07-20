import discord
import asyncio
import asyncpg

from discord.ext import commands, tasks
from utils.globalfunctions import get_main, get_comp_channel_id
from raidhandling import Raid


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raid(bot)
        #self.print_comps.start()
        #self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        #self.autosign_add.start()


    #@tasks.loop(seconds=20.0)
    #@commands.command()
    async def autosign_add(self, ctx):
        for guild in self.bot.guilds:
            mainevents = []
            placeholdertuples = []
            guild_id = guild.id

            role_id = await self.bot.pool.fetchval('''
            SELECT autosignrole
            FROM guild
            WHERE id = $1''', guild_id)

            if role_id is None:
                return

            role = guild.get_role(role_id)

            if role is None:
                return

            raids = await self.bot.pool.fetch('''
                    SELECT id, name
                    FROM raid
                    WHERE guildid = $1 AND main = TRUE''', guild_id)

            if raids is None:
                continue

            for record in raids:
                mainevents.append(record['id'])

            members = role.members
            for member in members:

                player_id = member.id

                playerclass = await get_main(self.bot.pool, guild_id, player_id)

                if playerclass is None:
                    continue

                for raid_id in mainevents:
                    new_tuple = (player_id, raid_id, playerclass)
                    placeholdertuples.append(new_tuple)

            await self.bot.pool.executemany('''
                                        INSERT INTO sign (playerid, raidid, playerclass)
                                        VALUES ($1, $2, $3)
                                        ON CONFLICT (playerid, raidid) DO UPDATE
                                        SET playerclass = $3
                                        WHERE sign.playerclass != 'Declined' ''', placeholdertuples)

    #@commands.command()
    #@tasks.loop(seconds=10.0)
    async def print_comps(self, ctx):
        print("JOO")
        guild_id = ctx.guild.id

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
                WHERE guildid = $1 AND main = TRUE''', guild_id)

        if raids is None:
            return

        await comp_channel.purge()

        for raid in raids:
            embed = await raid_cog.embedcomp(ctx, raid['name'])

            await asyncio.sleep(1.5)

            await comp_channel.send(embed=embed)

    #@autosign_add.before_loop
    #@print_comps.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Background(bot))
