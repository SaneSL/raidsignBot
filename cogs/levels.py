import discord
import asyncio
import asyncpg

from discord.ext import commands


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addlevel(self, ctx, playerid, lvl):
        playerid = int(playerid)
        lvl = int(lvl)

        await self.bot.db.execute('''
        UPDATE player
        SET level = $1
        WHERE player.id = $2''', lvl, playerid)

    @commands.command()
    async def addlevelbyrole(self, ctx, rolename, level):
        guild = ctx.guild

        for member in guild.members:
            for role in member.roles:
                if rolename == role.name:
                    member_id = member.id
                    await ctx.invoke(self.addlevel, member_id, level)

    @commands.command()
    async def getmemberlevels(self, ctx):

        levellist = {1: set(), 2: set(), 3: set()}

        guild = ctx.guild
        guild_id = guild.id

        embed = discord.Embed(
            title="Levels for all members",
            colour=discord.Colour.blue()
        )

        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT playerid, level 
            FROM guild
            WHERE guildid = $1''', guild_id):
                levellist[record['level']].add(record['playerid'])

        for key in levellist:

            header = "Level " + str(key)

            class_string = ""
            for member_id in levellist[key]:
                member = guild.get_member(member_id)
                nickname = member.display_name
                class_string += nickname + "\n"

            if not class_string:
                class_string = "-"

            embed.add_field(name=header, value=class_string, inline=False)

        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Level(bot))
