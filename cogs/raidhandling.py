import discord
import asyncio
import asyncpg

from globalfunctions import get_raidid

from discord.ext import commands


class Raid(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def delevent(self, ctx, raidname):
        raidname = raidname.upper()
        guild = ctx.guild
        guild_id = guild.id

        raid_id = await get_raidid(self.bot.db, guild_id, raidname)

        if raid_id is None:
            await ctx.send('No such raid exists')
            return

        msg = await ctx.fetch_message(raid_id)
        await msg.delete()

        await ctx.invoke(self.clearevent, raidname)

        await self.bot.db.execute('''
        DELETE FROM raid
        WHERE name = $1 AND guildid = $2''', raidname, guild_id)

    @commands.command()
    async def addevent(self, ctx, raidname, note=None):
        raidname = raidname.upper()
        guild = ctx.guild
        guild_id = guild.id

        if note is None:
            title = raidname
        else:
            title = raidname + " - " + note

        embed = discord.Embed(
            title=title,
            colour=discord.Colour.blue()
        )

        msg = await ctx.channel.send(embed=embed)
        msg_id = msg.id

        await self.bot.db.execute('''
        INSERT INTO raid VALUES ($1, $2, $3)
        ON CONFLICT DO NOTHING''', msg_id, guild_id, raidname)

        await msg.add_reaction('\U0001f1fe')
        await msg.add_reaction('\U0001f1f3')
        await msg.add_reaction('\U0001f1e6')

    @commands.command()
    @commands.is_owner()
    async def clearevent(self, ctx, raidname):

        raidname = raidname.upper()

        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.db, guild_id, raidname)

        if raid_id is None:
            await ctx.send("No such raid exists")
            return

        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidid = $1''', raid_id)

    @commands.command()
    async def raids(self, ctx):
        raidlist = {}
        guild_id = ctx.guild.id

        async with self.bot.db.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
            SELECT raid.name, COUNT(sign.playerid) as amount
            FROM raid
            LEFT OUTER JOIN sign ON raid.id = sign.raidid
            WHERE guildid = $1
            GROUP BY raid.name''', guild_id):
                    raidlist[record['name']] = record['amount']

        if len(raidlist) is 0:
            await ctx.send("No raids")
            return

        value = "---------"

        embed = discord.Embed(
            title="Attendances",
            colour=discord.Colour.blue()
        )

        for key in raidlist:
            header = key + " (" + str(raidlist[key]) + ")"
            embed.add_field(name=header, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def comp(self, ctx, raidname):

        complist = {"Warrior": [], "Rogue": [], "Hunter": [], "Warlock": [], "Mage": [], "Priest": [],
                    "Shaman": [], "Druid": [], "Declined": []}

        raidname = raidname.upper()
        guild = ctx.guild
        guild_id = guild.id

        raid_id = await get_raidid(self.bot.db, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid doesn't exist")
            return

        raid_id = raid_id

        async with self.bot.db.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT player.id, sign.playerclass
                FROM sign
                LEFT OUTER JOIN player ON sign.playerid = player.id
                WHERE sign.raidid = $1''', raid_id):
                    member = guild.get_member(record['id'])
                    name = member.display_name
                    complist[record['playerclass']].append(name)

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

    @commands.command()
    async def editevent(self, ctx, raidname, note=None):
        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.db, guild_id, raidname)

        if raid_id is None:
            return

        if note is None:
            title = note
        else:
            title = raidname + " - " + note

        msg = await ctx.fetch_message(raid_id)

        embed = msg.embeds[0]
        embed.title = title

        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(Raid(bot))
