import discord

from utils.globalfunctions import get_raidid, get_raid_channel_id
from utils import checks
from discord.ext import commands


class Raiding(commands.Cog):
    """
    This category includes adding, deleting, editing and clearing raids.
    All raid comps are updated every 20 minutes and posted on the proper channel.
    """
    def __init__(self, bot):
        self.bot = bot
        self.event_footer = "Y = sign to raid with main, N = decline, A = sign to raid with alt.\n" \
                            "If you wish to change your decision, just react with the other emoji."

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

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['delraid', 'rmraid'], description="Deletes raid with given name.")
    async def delevent(self, ctx, raidname):
        guild = ctx.guild
        guild_id = guild.id
        raidname = raidname.upper()

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            return

        await self.clearsigns(raid_id)

        await self.bot.pool.execute('''
                DELETE FROM raid
                WHERE name = $1 AND guildid = $2''', raidname, guild_id)

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Raid channel doesn't exist. Run `!addchannels`")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        msg = await raid_channel.fetch_message(raid_id)

        await msg.delete()

    @commands.command(aliases=['addraid'], description="Creates a new raid with given name.")
    async def addevent(self, ctx, raidname, note=None, mainraid=None):
        guild_id = ctx.guild.id
        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await ctx.send("Raid channel doesn't exist. Run `!addchannels` and readd all raids with"
                           "`!readdraid if necessary.")
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

        embed.set_footer(text=self.event_footer)

        msg = await raid_channel.send(embed=embed)
        msg_id = msg.id

        await self.bot.pool.execute('''
        INSERT INTO raid VALUES ($1, $2, $3, $4)
        ON CONFLICT DO NOTHING''', msg_id, guild_id, raidname, mainraid)

        await msg.add_reaction('\U0001f1fe')
        await msg.add_reaction('\U0001f1f3')
        await msg.add_reaction('\U0001f1e6')

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['clearraid'], description="Clears all signs from the given raid.")
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

    @commands.command(aliases=['raids'], description="Displays given raids and the amount of signs.")
    @commands.cooldown(5, 60, commands.BucketType.guild)
    async def events(self, ctx):
        raidlist = {}
        guild_id = ctx.guild.id

        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
            SELECT raid.name, COUNT(sign.playerid) as amount, main
            FROM raid
            LEFT OUTER JOIN sign ON raid.id = sign.raidid
            WHERE guildid = $1
            GROUP BY raid.name, raid.main''', guild_id):
                    raidlist[record['name']] = (record['amount'], record['main'])

        if len(raidlist) is 0:
            await ctx.send("No raids")
            return

        value = "---------"

        embed = discord.Embed(
            title="Attendances",
            colour=discord.Colour.green()
        )

        for key in raidlist:
            if raidlist[key][1] is True:
                header = f"{key} - main - ({raidlist[key][0]})"
            else:
                header = f"{key} - ({raidlist[key][0]})"
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

    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.command(description="Displays given raids comp.")
    async def comp(self, ctx, raidname):
        embed = await self.embedcomp(ctx, raidname)

        await ctx.channel.send(embed=embed)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['editraid'], description="Allows the user to edit given raids note and change the raid"
                                                        "to main raid. If no main argument is given the raid is"
                                                        " no longer a main raid.")
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

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['readdraid'], description="Readds the raid message, if it's accidentally deleted"
                                                         " by the user.")
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

        embed.set_footer(text=self.event_footer)

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
    bot.add_cog(Raiding(bot))
