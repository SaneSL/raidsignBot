import discord

from utils.globalfunctions import get_raidid, get_raid_channel_id
from discord.ext import commands


class Raid(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def clearsigns(self, raid_id):
        await self.bot.pool.execute('''
        DELETE FROM sign
        WHERE raidid = $1''', raid_id)

    @staticmethod
    async def removereacts(msg):
        await msg.clear_reactions()

        await msg.add_reaction('\U0001f1fe')
        await msg.add_reaction('\U0001f1f3')
        await msg.add_reaction('\U0001f1e6')

    @commands.command(aliases=['delraid', 'rmraid'])
    async def delevent(self, ctx, raidname):
        guild = ctx.guild
        guild_id = guild.id

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Specify raid channel")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        raidname = raidname.upper()

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)
        if raid_id is None:
            await ctx.send('Raid not found')
            return

        msg = await raid_channel.fetch_message(raid_id)

        await msg.delete()

        await self.clearsigns(raid_id)

        await self.bot.pool.execute('''
        DELETE FROM raid
        WHERE name = $1 AND guildid = $2''', raidname, guild_id)

    @commands.command(aliases=['addraid'])
    async def addevent(self, ctx, raidname, note=None, mainraid=None):
        guild_id = ctx.guild.id
        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Specify raid channel")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await ctx.send("Create a raid channel")

        raidname = raidname.upper()

        raid_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE guildid = $1 AND name = $2 LIMIT 1)''', guild_id, raidname)

        if raid_exists is True:
            ctx.send("Raid already exists")
            return

        if note is None:
            title = raidname
        else:
            if note.title() == 'Main':
                title = raidname
                mainraid = True
            else:
                title = raidname + " - " + note

        if mainraid is None:
            mainraid = False
        else:
            mainraid = True

        if mainraid is True:
            title = title + " - (Main)"

        embed = discord.Embed(
            title=title,
            colour=discord.Colour.dark_orange()
        )

        msg = await raid_channel.send(embed=embed)
        msg_id = msg.id

        await self.bot.pool.execute('''
        INSERT INTO raid VALUES ($1, $2, $3, $4)
        ON CONFLICT DO NOTHING''', msg_id, guild_id, raidname, mainraid)

        await msg.add_reaction('\U0001f1fe')
        await msg.add_reaction('\U0001f1f3')
        await msg.add_reaction('\U0001f1e6')

    @commands.command(aliases=['clearraid'])
    async def clearevent(self, ctx, raidname):
        guild_id = ctx.guild.id

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Specify raid channel")
            return

        raidname = raidname.upper()

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        msg = await raid_channel.fetch_message(raid_id)

        await self.clearsigns(raid_id)
        await self.removereacts(msg)

    @commands.command(aliases=['raids'])
    async def events(self, ctx):
        raidlist = {}
        guild_id = ctx.guild.id

        async with self.bot.pool.acquire() as con:
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
            colour=discord.Colour.green()
        )

        for key in raidlist:
            header = key + " (" + str(raidlist[key]) + ")"
            embed.add_field(name=header, value=value, inline=False)

        await self.bot.pool.release(con)
        await ctx.send(embed=embed)

    async def embedcomp(self, ctx, raidname):

        complist = {"Warrior": [], "Rogue": [], "Hunter": [], "Warlock": [], "Mage": [], "Priest": [],
                    "Shaman/Paladin": [], "Druid": [], "Declined": []}

        raidname = raidname.upper()
        guild = ctx.guild
        guild_id = guild.id

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            ctx.channel.send("Raid not found")
            return

        raid_id = raid_id

        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT player.id, sign.playerclass
                FROM sign
                LEFT OUTER JOIN player ON sign.playerid = player.id
                WHERE sign.raidid = $1''', raid_id):
                    member = guild.get_member(record['id'])
                    name = member.display_name

                    if record['playerclass'] is None:
                        continue

                    if record['playerclass'] in {"Shaman", "Paladin"}:
                        complist["Shaman/Paladin"].append(name)
                        continue

                    complist[record['playerclass']].append(name)

        total_signs = 0
        
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

            embed.add_field(name=header, value=class_string, inline=False)

        await self.bot.pool.release(con)
        return embed

    @commands.command()
    async def comp(self, ctx, raidname):
        embed = await self.embedcomp(ctx, raidname)

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=['editraid'])
    async def editevent(self, ctx, raidname, note=None, mainraid=None):
        guild_id = ctx.guild.id

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Specify raid channel")
            return

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        msg = await raid_channel.fetch_message(raid_id)

        embed = msg.embeds[0]

        if note is None:
            title = raidname
        else:
            if note.title() == 'Main':
                title = raidname
                mainraid = True
            else:
                title = raidname + " - " + note

        if mainraid is None:
            mainraid = False
        else:
            mainraid = True

        if mainraid is True:
            title = title + " - (Main)"
            await self.bot.pool.execute('''
            UPDATE raid
            SET main = TRUE
            WHERE id = $1''', raid_id)
        else:
            await self.bot.pool.execute('''
            UPDATE raid
            SET main = FALSE
            WHERE id = $1''', raid_id)

        embed.title = title

        await msg.edit(embed=embed)

    @commands.command(aliases=['readdraid'])
    async def readdevent(self, ctx, raidname):
        guild_id = ctx.guild.id
        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Specify raid channel")

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raidname is None:
            return

        raidname = raidname.upper()

        raid_info = await self.bot.pool.fetchrow('''
        SELECT id, main
        FROM raid
        WHERE guildid = $1 AND name = $2''', guild_id, raidname)

        if raid_info is None:
            return

        if raid_info['main'] is True:
            title = raidname + " - (Main)"
        else:
            title = raidname

        embed = discord.Embed(
            title=title,
            colour=discord.Colour.dark_orange()
        )

        msg = await raid_channel.send(embed=embed)
        msg_id = msg.id

        await msg.add_reaction('\U0001f1fe')
        await msg.add_reaction('\U0001f1f3')
        await msg.add_reaction('\U0001f1e6')

        await self.bot.pool.execute('''
        UPDATE raid
        SET id = $1
        WHERE guildid = $2 AND name = $3''', msg_id, guild_id, raidname)

    """
    @delevent.error
    @editevent.error
    @clearevent.error
    async def delevent_error(self, ctx, error):
        if isinstance(error.__cause__, (discord.NotFound, discord.Forbidden, discord.HTTPException)):
            return
    """

def setup(bot):
    bot.add_cog(Raid(bot))
