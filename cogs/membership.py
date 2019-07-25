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

    async def addautosign(self, guild, con=None):
        guild_id = guild.id

        role = await guild.create_role(name='AutoSign', reason="Bot created AutoSign role")

        # Also used with connection
        if con is None:
            await self.bot.pool.execute('''
            UPDATE guild
            SET autosignrole = $1
            WHERE id = $2''', role.id, guild_id)
            return role
        else:
            await con.execute('''
            UPDATE guild
            SET autosignrole = $1
            WHERE id = $2''', role.id, guild_id)

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

    @commands.command(description="Gives the user AutoSign role, which makes the user sign automatically to all 'main'"
                                  "raids.")
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        autosign_id = await self.bot.pool.fetchval('''
        SELECT guild.autosignrole
        FROM guild
        WHERE id = $1''', guild.id)

        if autosign_id is None:
            role = await self.addautosign(ctx.guild)
        else:
            role = ctx.guild.get_role(autosign_id)

        if role is None:
            role = await self.addautosign(ctx.guild)

        if role in member.roles:
            await member.remove_roles(role, reason="Remove AutoSign role")
            await ctx.send(f"{ctx.author.mention} removed role!")
        else:
            await member.add_roles(role, reason='AutoSign role')
            await ctx.send(f"{ctx.author.mention} added role!")

    '''
    @autosign.error
    async def autosign_error(self, ctx, error):
        if isinstance(error.__cause__, (discord.Forbidden, discord.HTTPException)):
            # Role hierarchy is wrong aka role is higher than the bots role
            return
    '''

def setup(bot):
    bot.add_cog(Membership(bot))
