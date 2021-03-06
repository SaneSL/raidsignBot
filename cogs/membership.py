import discord

from .utils.globalfunctions import is_valid_combo
from discord.ext import commands
from .utils import customcommand


class Membership(commands.Cog, name='Player'):
    """
    These commands allow user to store their preferred main/alt class and add get autosign role.
    """
    def __init__(self, bot):
        self.bot = bot

    async def addself(self, player_id):
        """
        Adds user to db

        Parameters
        ----------
        player_id
        """

        await self.bot.pool.execute('''
        INSERT INTO player (id)
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @commands.cooldown(2, 60, commands.BucketType.user)
    @customcommand.c_command(description="Sets user's main. Use specific class and spec!",
                             examples=["addmain rogue combat"])
    async def addmain(self, ctx, playerclass, *, spec):
        """
        Adds user's main to db

        Parameters
        ----------
        ctx
        playerclass
        spec
        """

        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        # Replace quotes just incase
        spec = spec.replace('"', "")

        await self.addself(player_id)

        playerclass = playerclass.title()
        spec = spec.lower()

        if not await is_valid_combo(playerclass, spec):
            await ctx.send("Invalid class name or spec... try again.")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, main, mainspec)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET main = $3, mainspec = $4
        ''', guild_id, player_id, playerclass, spec)

        await ctx.send(f"{author.mention} set main to {spec} {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @customcommand.c_command(description="Sets user's alt. Use specific class and spec!",
                             examples=["addalt rogue combat"])
    async def addalt(self, ctx, playerclass, *, spec):
        """
        Adds user's alt to db

        Parameters
        ----------
        ctx
        playerclass
        spec
        """

        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        # Replace quotes just incase
        spec = spec.replace('"', "")

        await self.addself(player_id)

        playerclass = playerclass.title()
        spec = spec.lower()

        if not await is_valid_combo(playerclass, spec):
            await ctx.send("Invalid class name or spec... try again.")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, alt, altspec)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET alt = $3, altspec = $4
        ''', guild_id, player_id, playerclass, spec)

        await ctx.send(f"{author.mention} set alt to {spec} {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @customcommand.c_group()
    async def autosign(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Type `on` or `off` after the command ')

    @commands.cooldown(2, 60, commands.BucketType.user)
    @autosign.command(description="Gives the user autosign role, which makes the user sign automatically "
                                         "to all `main` raids with main.")
    async def on(self, ctx):
        """
        Gives user autosign and updates preference in db

        Parameters
        ----------
        ctx
        """

        guild = ctx.guild
        member = ctx.author

        playerclass_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT main, mainspec FROM membership
        WHERE guildid = $1 AND playerid = $2 LIMIT 1)''', guild.id, member.id)

        if playerclass_exists is False:
            await ctx.send(f"Autosign failed. {member.mention} add your main with `!addmain <classname> <spec>` "
                           f"and try again`")
            return

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = TRUE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        await ctx.send(f"{member.mention} added autosign!")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @autosign.command(description="Removes autosign.")
    async def off(self, ctx):
        """
        Disables autosign and updates preference in db

        Parameters
        ----------
        ctx
        """

        guild = ctx.guild
        member = ctx.author

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = FALSE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        await ctx.send(f"{member.mention} removed autosign!")


def setup(bot):
    bot.add_cog(Membership(bot))
