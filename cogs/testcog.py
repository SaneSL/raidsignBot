import discord
import asyncio
import asyncpg
import re
import datetime

from discord.ext import commands
from utils.globalfunctions import get_main
from utils import checks
from utils.permissions import default_role_perms_comp_raid, bot_perms, bot_join_permissions
from utils.checks import has_any_permission


class Testcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):

        embed = discord.Embed()
        embed.title = "Raidsign bot"
        embed.description = "Discord bot to replace calendar system/signing for classic wow."

        embed.add_field(name="Help", value="To get a detailed description of a command type"
                                           " `! or ?help <command name>`. For more general help type `!help`")

        embed.add_field(name="Prefixes", value="xd")

        embed.add_field(name='Links', value="[Discord](https://discord.gg/Y7hrmDD) \n"
                                            "[Github](https://github.com/SaneSL/raidsignBot)")
        embed.set_footer(text="Made by Sane#4042")

        await ctx.send(embed=embed)

    async def testi(self, ctx):
        messages = await ctx.channel.history(limit=3).flatten()

        content = messages[0].content
        print(content)


    @commands.command(aliases=['yolo'])
    async def yolotest(self, ctx):
        total_signs = 0
        raidname = "MC"

        complist = {"Warrior": [], "Rogue": [], "Hunter": [], "Warlock": [], "Mage": [], "Priest": [],
                    "Shaman/Paladin": [], "Druid": [], "Declined": []}

        test = "Testristring"

        for x in complist:
            for i in range(7):
                complist[x].append(test)

        for key in complist:
            total_signs += len(complist[key])

        embed = discord.Embed(
            title="Attending -- " + raidname + " (" + str(total_signs) + ")",
            colour=discord.Colour.dark_magenta()
        )

        for key in complist:
            header = key + " (" + str(len(complist[key])) + ")"

            class_string = ""
            for nickname in complist[key]:
                class_string += nickname + "\n"

            if not class_string:
                class_string = "-"

            embed.add_field(name=header, value=class_string, inline=True)

        await ctx.send(embed=embed)

    @commands.command(Help="JA NÄINNNNN")
    async def supatest(self, ctx, var):
        cmd = self.bot.get_command(var)

        for check in cmd.checks:
            print(check.__name__)
            return
            check = str(check)
            print(check)
            result = re.search(r'\s(.*)\.<', check)
            result = result.group(1)
            print(result)

        if cmd is None:
            print("OOO")
        else:
            print("JOO")

    @commands.command()
    async def testembed(self, ctx):

        print("D")

        embed = discord.Embed()
        test_one = "TESTI_YKSI"
        test_two = "Testi_KAKSI"

        value_one = "hnifoawfw ofwaoifawo"
        value_two = "djkwadjwaj ajwdjwaj"
        embed.title = "TESTIIII"
        embed.colour = discord.Colour.orange()
        embed.add_field(name=test_one, value=value_one)
        embed.add_field(name=test_two, value=value_two)

        print("X")

        await ctx.release()

        await ctx.send(embed=embed)

    @commands.command()
    async def testp(self, ctx):
        perms = discord.Permissions(permissions=0)

        perms.update(**bot_join_permissions)

        bot_id = self.bot.user.id
        bot_member = ctx.guild.get_member(bot_id)
        guild_perms = bot_member.guild_permissions

        print(perms.value)

        if guild_perms >= perms:
            print("ON")

    # Not done/testing
    @commands.is_owner()
    @commands.command()
    async def clearm(self, ctx):
        await self.bot.pool.execute('''
        DELETE FROM membership
        WHERE playerid = $1''', ctx.message.author.id)

    @commands.command()
    async def clearp(self, ctx):
        await self.bot.pool.execute('''
        DELETE FROM player
        WHERE id = $1''', ctx.message.author.id)

    @commands.command()
    async def clears(self, ctx):
        await self.bot.pool.execute('''
        DELETE FROM sign
        WHERE playerid = $1''', ctx.message.author.id)

    @commands.command()
    async def clearr(self, ctx):
        await self.bot.pool.execute('''
        DELETE FROM raid
        WHERE guildid = $1''', ctx.guild.id)

    @commands.command()
    async def clearg(self, ctx):
        await self.bot.pool.execute('''
        DELETE FROM guild
        WHERE id = $1''', ctx.guild.id)

    @commands.command()
    async def cleara(self, ctx):
        await ctx.invoke(self.clearm)
        await ctx.invoke(self.clears)
        await ctx.invoke(self.clearp)
        await ctx.invoke(self.clearr)
        await ctx.invoke(self.clearg)

    async def testasync(self, i):
        print("loop->" + str(i))
        await asyncio.sleep(2)
        print("loop->" + str(i))
        await asyncio.sleep(2)
        print("loop->" + str(i))

    @commands.command()
    async def testpos(self, ctx):
        name = self.testasync

        list_t = []

        for i in range(3):
            list_t.append(self.testasync(i))

        print(list_t)

        await asyncio.gather(*list_t)


    @commands.command()
    async def komento(self, ctx):
        cog = self.bot.get_cog('Misc')
        await ctx.invoke(cog.botinfo)

    @commands.command()
    async def delc(self, ctx):
        for channel in ctx.guild.channels:
            if channel.name == 'd':
                continue
            await channel.delete()
            ctx.release()

    @commands.command()
    async def testblack(self, user_id):
        date = datetime.datetime.utcnow().date()

        await self.bot.pool.execute('''
        INSERT INTO blacklist
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', user_id, date)

    @commands.command()
    async def qbl(self, ctx):
        row = await self.bot.pool.fetchrow('''
        SELECT *
        FROM blacklist''')

        print(row)


def setup(bot):
    bot.add_cog(Testcog(bot))