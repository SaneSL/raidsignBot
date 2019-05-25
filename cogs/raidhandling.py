import discord
import asyncio
import asyncpg

from discord.ext import commands


class Raids(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def clearevent(self, ctx, raidname):

        raidname = raidname.upper()

        await self.bot.db.execute('''
        DELETE FROM signs
        WHERE raid = $1''', raidname)

    @commands.command()
    # @decline.after_invoke
    # @sign.after_invoke
    async def comp(self, ctx, raidname):

        complist = {"Warrior": set(), "Rogue": set(), "Hunter": set(), "Warlock": set(), "Mage": set(), "Priest": set(),
                    "Shaman": set(), "Druid": set()}

        raidname = raidname.upper()

        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT * 
            FROM signs
            WHERE raid = $1''', raidname):
                print(record)
                complist[record['class']].add(record['name'])

        total_signs = 0
        
        for key in complist:
            total_signs += len(complist[key])

        embed = discord.Embed(
            title="Attending -- " + raidname + " (" + str(total_signs) + ")",
            colour=discord.Colour.blue()
        )

        for key in complist:
            header = key + " (" + str(len(complist[key])) + ")"

            class_string = ""
            for nickname in complist[key]:
                class_string += nickname + "\n"

            if not class_string:
                class_string = "-"

            embed.add_field(name=header, value=class_string, inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Raids(bot))
