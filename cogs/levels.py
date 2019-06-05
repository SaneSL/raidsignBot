import discord
import asyncio
import asyncpg

from discord.ext import commands
from globalfunctions import getuserid


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addlevel(self, ctx, name, lvl):
        guild_id = ctx.guild.id
        members = ctx.guild.members

        player_id = await getuserid(members, name)

        if player_id == -1:
            await ctx.send("No player found")
            return

        lvl = int(lvl)

        await self.bot.db.execute('''
        UPDATE membership
        SET level = $1
        WHERE membership.guildid = $2 AND membership.playerid = $3''', lvl, guild_id, player_id)

    @commands.command()
    async def addlevelbyrole(self, ctx, rolename, lvl):
        guild = ctx.guild
        guild_id = guild.id
        lvl = int(lvl)

        for member in guild.members:
            for role in member.roles:
                if rolename.lower() == role.name.lower():
                    player_id = member.id
                    await self.bot.db.execute('''
                            UPDATE membership
                            SET level = $1
                            WHERE membership.guildid = $2 AND membership.playerid = $3''', lvl, guild_id, player_id)

    @commands.command()
    async def getmemberlevels(self, ctx):

        levellist = {1: [], 2: [], 3: []}

        guild = ctx.guild
        guild_id = guild.id

        embed = discord.Embed(
            title="Levels for all members",
            colour=discord.Colour.blue()
        )

        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT playerid, level 
            FROM membership
            WHERE guildid = $1''', guild_id):
                member = guild.get_member(record['playerid'])
                name = member.display_name
                levellist[record['level']].append(name)

        print(levellist)

        for key in levellist:

            header = "Level " + str(key)

            class_string = ""
            for member in levellist[key]:
                class_string += member + "\n"

            if not class_string:
                class_string = "-"

            embed.add_field(name=header, value=class_string, inline=False)

        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Level(bot))
