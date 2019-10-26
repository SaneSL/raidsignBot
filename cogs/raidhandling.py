import discord
import asyncio
import datetime

from .utils.globalfunctions import get_raidid, get_raid_channel_id
from .utils import checks
from discord.ext import commands


class Raid(commands.Cog):
    """
    This category includes adding, deleting, editing, clearing raids and etc.
    All raid comps are updated every 20 minutes and posted on the proper channel.
    Server can have maximum of 6 raids.
    """
    def __init__(self, bot):
        self.bot = bot
        self.raid_cap = 6
        self.event_footer = "M = sign to raid with main, A = sign to raid with alt, D = decline. \n" \
                            "If you wish to change your decision, just react with other emoji."

    @staticmethod
    async def add_emojis(msg):
        await msg.add_reaction('\U0001f1f2')
        await msg.add_reaction('\U0001f1e6')
        await msg.add_reaction('\U0001f1e9')

    async def run_add_bot_channels(self, guild):
        guild_cog = self.bot.get_cog('Server')
        await guild_cog.add_bot_channels(guild)

    async def clearsigns(self, raid_id):
        await self.bot.pool.execute('''
        DELETE FROM sign
        WHERE raidid = $1''', raid_id)

    async def removereacts(self, guild, raid_id):
        guild_id = guild.id
        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await self.run_add_bot_channels(guild)
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await self.run_add_bot_channels(guild)
            return

        msg = await raid_channel.fetch_message(raid_id)

        await msg.clear_reactions()
        await self.add_emojis(msg)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['delevent', 'rmraid'], description="Deletes raid with given name.",
                      help="Administrator, manage server",
                      brief='{"examples":["delraid MC"], "cd":""}')
    async def delraid(self, ctx, raidname):
        guild = ctx.guild
        guild_id = guild.id
        raidname = raidname.upper()

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            return

        await self.bot.pool.execute('''
                DELETE FROM raid
                WHERE name = $1 AND guildid = $2''', raidname, guild_id)

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await self.run_add_bot_channels(guild)
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await self.run_add_bot_channels(guild)
            return

        msg = await raid_channel.fetch_message(raid_id)

        await msg.delete()

    @commands.cooldown(2, 30, commands.BucketType.guild)
    @commands.command(aliases=['addevent'], description="Creates a new raid with given name.",
                      brief='{"examples":["addraid MC `some note` main","addraid MC main","addraid MC `some note`"],'
                            ' "cd":"30"}')
    async def addraid(self, ctx, raidname, note=None, mainraid=None):
        guild = ctx.guild
        guild_id = ctx.guild.id

        raid_amount = await self.bot.pool.fetchval('''
        SELECT COUNT(id) AS raid_amount
        FROM raid
        WHERE raid.guildid = $1''', guild_id)

        if raid_amount >= self.raid_cap:
            await ctx.send(f"Your server has reached the maximum raid amount of {self.raid_cap}")
            return

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await self.run_add_bot_channels(guild)
            await ctx.send("Seems like your server is missing a raidchannel. I added it back. \n"
                           "Try using this command again. Also if you want to add possible missing raids use\n"
                           "!readdraids")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await self.run_add_bot_channels(guild)
            await ctx.send("Seems like your server is missing a raidchannel. I added it back. \n"
                           "Try using this command again. Also if you want to add possible missing raids use\n"
                           "!readdraids")
            return

        raidname = raidname.upper()

        raid_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE guildid = $1 AND name = $2 LIMIT 1)''', guild_id, raidname)

        if raid_exists is True:
            await ctx.send("Raid already exists.")
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

        await self.add_emojis(msg)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(aliases=['clearevent'], description="Clears all signs from the given raid.",
                      help="Administrator, manage server",
                      brief='{"examples":["clearraid MC"], "cd":"60"}')
    async def clearraid(self, ctx, raidname):
        guild = ctx.guild
        guild_id = guild.id

        raidname = raidname.upper()

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        await self.clearsigns(raid_id)
        await self.removereacts(guild, raid_id)

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.command(aliases=['events'], description="Displays all raids and the amount of signs. Empty raids "
                                                      "not shown.",
                      brief='{"examples":[], "cd":"60"}')
    async def raids(self, ctx):
        raidlist = {}
        guild_id = ctx.guild.id

        records = await self.bot.pool.fetch('''
        SELECT raid.name, COUNT(sign.playerid) as amount, main
        FROM raid
        LEFT OUTER JOIN sign ON raid.id = sign.raidid
        WHERE guildid = $1 AND sign.playerclass != 'Declined'
        GROUP BY raid.name, raid.main''', guild_id)

        if not len(records):
            await ctx.send("No raids - this might also mean that none of the raids have any signs.")
            return

        for record in records:
            raidlist[record['name']] = (record['amount'], record['main'])

        value = "---------"

        embed = discord.Embed(
            title="Attendances",
            colour=discord.Colour.green()
        )

        for key in raidlist:
            if raidlist[key][1] is True:
                header = f"{key} - (Main) - ({raidlist[key][0]})"
            else:
                header = f"{key} - ({raidlist[key][0]})"
            embed.add_field(name=header, value=value, inline=False)

        await ctx.send(embed=embed)

    async def embedcomp(self, guild, raidname):

        complist = {"Warrior": [], "Rogue": [], "Hunter": [], "Warlock": [], "Mage": [], "Priest": [],
                    "Shaman/Paladin": [], "Druid": [], "Declined": []}

        raidname = raidname.upper()
        guild_id = guild.id

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            return

        raid_id = raid_id
        sign_order = 1

        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT player.id, sign.playerclass
                FROM sign
                LEFT OUTER JOIN player ON sign.playerid = player.id
                WHERE sign.raidid = $1''', raid_id):
                    # Replaced for testing
                    # member = guild.get_member(record['id'])
                    # name = member.display_name

                    # For testing
                    member = guild.get_member(record['id'])
                    if member is None:
                        name = str(record['id'])
                    else:
                        name = member.display_name

                    # This if should never be triggered
                    if record['playerclass'] is None:
                        continue

                    elif record['playerclass'] == 'Declined':
                        complist[record['playerclass']].append((name, 0))

                    elif record['playerclass'] in {"Shaman", "Paladin"}:
                        complist["Shaman/Paladin"].append((name, sign_order))
                        sign_order += 1

                    else:
                        complist[record['playerclass']].append((name, sign_order))
                        sign_order += 1

        total_signs = 0

        for key in complist:
            if key == 'Declined':
                continue
            total_signs += len(complist[key])

        embed = discord.Embed(
            title="Attending -- " + raidname + " (" + str(total_signs) + ")",
            colour=discord.Colour.dark_magenta(),
            timestamp=datetime.datetime.utcnow()
        )

        for key in complist:
            header = key + " (" + str(len(complist[key])) + ")"

            class_string = ""
            for value_tuple in complist[key]:
                nickname = value_tuple[0]
                order = str(value_tuple[1])

                # Testing to add emoji
                emoji = '<:ProtWar:635207677722624000>'

                if order == '0':
                    class_string += nickname + "\n"

                else:
                    class_string += order + ". " + nickname + " " + emoji + "\n"

            if not class_string:
                class_string = "-"

            embed.add_field(name=header, value=class_string, inline=True)

        await self.bot.pool.release(con)
        return embed

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.command(description="Displays given raid's comp.", brief='{"examples":["comp MC"], "cd":"60"}')
    async def comp(self, ctx, raidname):
        guild = ctx.guild
        embed = await self.embedcomp(guild, raidname)

        await ctx.send(embed=embed)

    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['editevent'], description="Allows the user to edit raid's note and change the raid"
                                                         "to 'main' raid. If no main argument is given the raid is"
                                                         " no longer a 'main' raid.",
                      help="Administrator, manage server",
                      brief='{"examples":["editraid MC `some note` main","editraid MC main","editraid MC `some note`"],'
                            ' "cd":"60"}')
    async def editraid(self, ctx, raidname, note=None, mainraid=None):
        guild = ctx.guild
        guild_id = ctx.guild.id

        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await self.run_add_bot_channels(guild)
            return

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await self.run_add_bot_channels(guild)
            return

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

    @commands.cooldown(2, 600, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['readdevent'], description="Readds all raids (messages), if raid channel/messages are "
                                                          "accidentally deleted by the user.",
                      help="Administrator, manage server",
                      brief='{"examples":[], "cd":"600"}')
    async def readdraids(self, ctx):
        guild = ctx.guild
        guild_id = ctx.guild.id
        raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        if raid_channel_id is None:
            await self.run_add_bot_channels(guild)
            # Not very optimal to get channel_id again
            raid_channel_id = await get_raid_channel_id(self.bot.pool, guild_id)

        raid_channel = self.bot.get_channel(raid_channel_id)

        if raid_channel is None:
            await self.run_add_bot_channels(guild)
            await ctx.send("Seems like your server is missing a raidchannel. I added it back. \n"
                           "Try using this command again.")
            return

        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT id, name, main
                FROM raid
                WHERE guildid = $1''', guild_id):

                    if record is None:
                        return

                    if record['main'] is True:
                        title = record['name'] + " - (Main)"
                    else:
                        title = record['name']

                    embed = discord.Embed(
                        title=title,
                        colour=discord.Colour.dark_orange()
                    )

                    embed.set_footer(text=self.event_footer)

                    msg = await raid_channel.send(embed=embed)
                    msg_id = msg.id

                    await self.add_emojis(msg)

                    await con.execute('''
                    UPDATE raid
                    SET id = $1
                    WHERE guildid = $2 AND name = $3''', msg_id, guild_id, record['name'])

                    await asyncio.sleep(3.0)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.cooldown(2, 60, commands.BucketType.guild)
    @commands.command(description="Makes raid automatically clear signs at specified time. \n"
                                  "This may happen 1 hour later than specified so a good time to set this to is 1 "
                                  "hour after your raid starts. \n"
                                  "Time must be given in in "
                                  "24-hour clock format and in UTC. \nYou can always disable this with "
                                  "!autoclearoff <raidname>.",
                      help="Administrator, manage server",
                      brief='{"examples":["autoclear MC monday 19 ","autoclear MC wednesday 8"],'
                            '"cd":"60"}')
    async def autoclear(self, ctx, raidname, weekday, hour: int):
        day_values = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
                      'saturday': 5, 'sunday': 6}

        weekday = weekday.lower()

        if weekday not in day_values:
            return

        guild_id = ctx.guild.id
        raidname = raidname.upper()

        raid_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE guildid = $1 AND name = $2 LIMIT 1)''', guild_id, raidname)

        if raid_exists is False:
            await ctx.send("Raid doesn't exists")
            return

        clear_time = day_values[weekday] * 24 + hour

        await self.bot.pool.execute('''
        UPDATE raid
        SET cleartime = $1
        WHERE name = $2 AND guildid = $3''', clear_time, raidname, guild_id)

        await ctx.send(f"{raidname} is set to clear every {weekday} at {hour} UTC.\n"
                       f"You can disable this with !autoclearoff <raidname>")

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(description="Disables the autoclear feature for the raid.",
                      help="Administrator, manage server",
                      brief='{"examples":["autoclearoff MC"], "cd":""}')
    async def autoclearoff(self, ctx, raidname):
        guild_id = ctx.guild.id
        raidname = raidname.upper()

        await self.bot.pool.execute('''
        UPDATE raid
        SET cleartime = NULL
        WHERE guildid = $1 AND name = $2''', guild_id, raidname)

        await ctx.send(f"Disabled autoclear for {raidname}.")


def setup(bot):
    bot.add_cog(Raid(bot))
