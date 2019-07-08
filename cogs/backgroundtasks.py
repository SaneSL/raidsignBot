import discord

from discord.ext import commands
from utils.globalfunctions import get_main, get_comp_channel_id
from raidhandling import Raid


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raid(bot)
        # self.autosign_add.add_exception_type(asyncpg.PostgresConnectionError)
        # self.autosign_add.start()

    #@tasks.loop(seconds=60.0)

    @commands.command()
    async def autosign_add(self, ctx):
        for guild in self.bot.guilds:
            mainevents = []
            placeholdertuples = []

            role = discord.utils.get(guild.roles, name='AutoSign')
            guild_id = guild.id

            raids = await self.bot.db.fetch('''
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

                playerclass = await get_main(self.bot.db, guild_id, player_id)

                if playerclass is None:
                    continue

                for raid_id in mainevents:
                    new_tuple = (player_id, raid_id, playerclass)
                    placeholdertuples.append(new_tuple)

            await self.bot.db.executemany('''
                                        INSERT INTO sign (playerid, raidid, playerclass)
                                        VALUES ($1, $2, $3)
                                        ON CONFLICT (playerid, raidid) DO UPDATE
                                        SET playerclass = $3
                                        WHERE sign.playerclass != 'Declined' ''', placeholdertuples)

    @commands.command()
    async def print_comps(self, ctx):
        guild_id = ctx.guild.id

        raid_cog = self.bot.get_cog('Raid')

        raids = await self.bot.db.fetch('''
                SELECT id, name
                FROM raid
                WHERE guildid = $1 AND main = TRUE''', guild_id)

        if raids is None:
            return

        comp_channel_id = await get_comp_channel_id(self.bot.db, guild_id)

        if comp_channel_id is None:
            return

        comp_channel = self.bot.get_channel(comp_channel_id)
        for raid in raids:
            embed = await raid_cog.embedcomp(ctx, raid['name'])
            await comp_channel.send(embed=embed)

    # @autosign_add.before_loop
    async def before_autosign(self):
        await self.bot.wait_until_ready()

    # Testing, change_interval introduced in next versio, which is not out yet.
    @commands.command()
    async def change_timer(self, ctx):
        self.autosign_add.cancel()
        # self.autosign_add.change_interval(seconds=5)


def setup(bot):
    bot.add_cog(Background(bot))
