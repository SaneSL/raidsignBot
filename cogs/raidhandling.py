import discord
import asyncio
import asyncpg

from discord.ext import commands


class Raid(commands.Cog):

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
    async def addevent(self, ctx, raidname, note):

        raidname = raidname.upper()

        await self.bot.db.execute('''
        INSERT INTO raid (name) VALUES ($1)
        ON CONFLICT DO NOTHING''', raidname)

        title = raidname + " - " + note

        embed = discord.Embed(
            title=title,
            colour=discord.Colour.blue()
        )

        msg = await ctx.channel.send(embed=embed)

        await msg.add_reaction('\U0000267f')

    @commands.command()
    @commands.is_owner()
    async def clearevent(self, ctx, raidname):

        raidname = raidname.upper()
        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidname = $1''', raidname)

    @commands.command()
    async def raids(self, ctx):
        raidlist = {}
        async with self.bot.db.transaction():
            async for record in self.bot.db.cursor('''
            SELECT name
            FROM raid'''):
                raidlist[record['name']] = 0

        if len(raidlist) is 0:
            await ctx.send("No raids")
            return

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
                raidlist[record['raidname']] = record['amount']

        for key in raidlist:
            header = key + " (" + str(raidlist[key]) + ")"
            embed.add_field(name=header, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def comp(self, ctx, raidname):

        complist = {"Warrior": set(), "Rogue": set(), "Hunter": set(), "Warlock": set(), "Mage": set(), "Priest": set(),
                    "Shaman": set(), "Druid": set(), "Declined": set()}

        raidname = raidname.upper()

        row = await self.bot.db.fetchrow('''
        SELECT name
        FROM raid
        WHERE name = $1''', raidname)

        if row is None:
            await ctx.send("Raid doesn't exist")
            return

        async with self.bot.db.transaction():

            async for record in self.bot.db.cursor('''
            SELECT player.name, sign.raidname, sign.playerclass
            FROM sign
            LEFT OUTER JOIN player ON sign.playerid = player.id
            WHERE sign.raidname = $1''', raidname):
                complist[record['playerclass']].add(record['name'])

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
    bot.add_cog(Raid(bot))
