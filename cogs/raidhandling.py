import discord
import asyncio
import asyncpg

from discord.ext import commands


class Raids(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def delevent(self, ctx, raidname):
        raidname = raidname.upper()
        await ctx.invoke(self.clearevent, raidname)

        await self.bot.db.execute('''
        DELETE FROM raid
        WHERE name = $1''', raidname)

    @commands.command()
    async def addevent(self, ctx, raidname):
        raidname = raidname.upper()

        await self.bot.db.execute('''
        INSERT INTO raid (name) VALUES ($1)
        ON CONFLICT DO NOTHING''', raidname)

    @commands.command()
    @commands.is_owner()
    async def clearevent(self, ctx, raidname):

        raidname = raidname.upper()
        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidname = $1''', raidname)

    # Query raid table instead, since if all raids are empty. Doesn't show anything
    @commands.command()
    async def raids(self, ctx):
        value = "---------"

        embed = discord.Embed(
            title="Attendances",
            colour=discord.Colour.blue()
        )
        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT sign.raidname, COUNT(sign.playerid) as amount
            FROM sign
            GROUP BY sign.raidname'''):
                header = record['raidname'] + " (" + str(record['amount']) + ")"
                embed.add_field(name=header, value=value, inline=False)

        await ctx.send(embed=embed)

    # Inform user if given raid doesn't exist instead of printing empty comp, look into embed
    # @decline.after_invoke
    # @sign.after_invoke
    @commands.command()
    async def comp(self, ctx, raidname):

        complist = {"Warrior": set(), "Rogue": set(), "Hunter": set(), "Warlock": set(), "Mage": set(), "Priest": set(),
                    "Shaman": set(), "Druid": set(), "Declined": set()}

        raidname = raidname.upper()

        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT player.name, sign.raidname, sign.playerclass
            FROM sign
            LEFT OUTER JOIN player ON sign.playerid = player.id
            WHERE sign.raidname = $1''', raidname):
                complist[record['playerclass']].add(record['name'])
        print(len(complist))

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

        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Raids(bot))
