import discord

from utils.globalfunctions import is_valid_class
from discord.ext import commands


class Membership(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def addself(self, player_id):
        await self.bot.pool.execute('''
        INSERT INTO player (id)
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @commands.command()
    async def addautosign(self, ctx):
        guild_id = ctx.guild.id

        autosign_id = await self.bot.pool.fetchval('''
        SELECT autosignrole
        FROM guild
        WHERE id = $1''', guild_id)

        if autosign_id is not None:
            guild_role = ctx.guild.get_role(autosign_id)
            if guild_role is not None:
                await ctx.guild.send("Role already exists")
                return

        role = await ctx.guild.create_role(name='AutoSign', reason="Bot created AutoSign role")

        await self.bot.pool.execute('''
        UPDATE guild
        SET autosignrole = $1
        WHERE id = $2''', role.id, guild_id)

    @commands.command()
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

    @commands.command()
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

    @commands.command()
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        autosign_id = await self.bot.pool.fetchval('''
        SELECT guild.autosignrole
        FROM guild
        WHERE id = $1''', guild.id)

        if autosign_id is None:
            await ctx.send("Role doesn't exist, create it with `addautosign`")
            return

        role = ctx.guild.get_role(autosign_id)

        if role is None:
            await ctx.send("Role has been deleted from server, create it with `addautosign`")
            return

        if role in member.roles:
            await member.remove_roles(role, reason="Remove AutoSign role")
        else:
            await member.add_roles(role, reason='AutoSign role')
        await ctx.send(f"{ctx.author.mention} you got it!")

    '''
    @autosign.error
    async def autosign_error(self, ctx, error):
        if isinstance(error.__cause__, (discord.Forbidden, discord.HTTPException)):
            # Role hierarchy is wrong aka role is higher than the bots role
            return
    '''

def setup(bot):
    bot.add_cog(Membership(bot))
