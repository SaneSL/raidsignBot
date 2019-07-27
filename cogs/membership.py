import discord

from utils.globalfunctions import is_valid_class
from discord.ext import commands


class Membership(commands.Cog, name='Player'):
    """
    These commands allow user to store their preferred main/alt class and add get autosign role.
    """
    def __init__(self, bot):
        self.bot = bot

    async def addself(self, player_id):
        await self.bot.pool.execute('''
        INSERT INTO player (id)
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @staticmethod
    async def addautosign(guild):
        role = await guild.create_role(name='autosign', reason="Bot created AutoSign role")

    @commands.command(description="Adds user's main class to db.", brief='{"examples":["addmain rogue"], "cd":""}')
    async def addmain(self, ctx, playerclass):
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("Invalid class")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, main)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET main = $3
        ''', guild_id, player_id, playerclass)

    @commands.command(description="Adds user's alt class to db.", brief='{"examples":["addalt rogue"], "cd":""}')
    async def addalt(self, ctx, playerclass):
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("Invalid class")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, alt)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET alt = $3
        ''', guild_id, player_id, playerclass)

    @commands.command(description="Gives the user autosign role, which makes the user sign automatically to all 'main'"
                                  "raids.")
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        playerclass_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT main FROM membership
        WHERE guildid = $1 AND playerid = $2 LIMIT 1)''', guild.id, member.id)

        if playerclass_exists is False:
            await ctx.send(f"{ctx.author.mention} add your main with `!addmain <classname>`")
            return

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = TRUE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        await ctx.send(f"Failed! {ctx.author.mention} added autosign!")

        role = discord.utils.get(guild.roles, name='autosign')

        if role is None:
            return
        else:
            await member.add_roles(role, reason='Added autosign role')

    @commands.command(description="Removes autosign.")
    async def autosignoff(self, ctx):
        guild = ctx.guild
        member = ctx.author

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = FALSE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        await ctx.send(f"{ctx.author.mention} removed autosign!")

        role = discord.utils.get(guild.roles, name='autosign')

        if role is None:
            return
        else:
            await member.remove_roles(role, reason='Removed autosign role')


    '''
    @autosign.error
    async def autosign_error(self, ctx, error):
        if isinstance(error.__cause__, (discord.Forbidden, discord.HTTPException)):
            # Role hierarchy is wrong aka role is higher than the bots role
            return
    '''

def setup(bot):
    bot.add_cog(Membership(bot))
