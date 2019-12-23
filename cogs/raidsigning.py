import discord

from discord.ext import commands
from .utils.globalfunctions import get_main, get_alt, sign_player, get_raidid
from .utils import checks
from .utils import customcommand


class Signing(commands.Cog):
    """
    This category handles signing to raids.
    Most of the signing should be done via reacting or having the 'AutoSign' role.
    """
    def __init__(self, bot):
        self.bot = bot

    async def add_sign(self, ctx, raidname, player_id, sign_type):
        """
        Adds player to given raid

        Parameters
        ----------
        ctx
        raidname
        player_id
        sign_type
            Defines if the player is signed with main, alt or declined
        """

        raidname = raidname.upper()
        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        if sign_type == 'main':
            row = await get_main(self.bot.pool, guild_id, player_id)

            if row is None:
                return
            else:
                playerclass = row['main']
                spec = row['mainspec']

        elif sign_type == 'alt':
            row = await get_alt(self.bot.pool, guild_id, player_id)

            if row is None:
                return
            else:
                playerclass = row['alt']
                spec = row['altspec']

        elif sign_type == 'Declined':
            playerclass = sign_type
            spec = None

        else:
            return

        if not await sign_player(self.bot.pool, player_id, raid_id, playerclass, spec):
            await ctx.send("No player")

    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @customcommand.c_command(description="Adds given player to raid.", examples=["addplayer @User#1234 MC main"], perms=["Administrator", "manage server"])
    async def addplayer(self, ctx, member: discord.Member, raidname, main_or_alt):
        """
        Adds player to raid

        Parameters
        ----------
        ctx
        member
            Instance of Member
        raidname
        main_or_alt
        """

        if member.id == self.bot.user.id or member.id is None:
            return

        main_or_alt = main_or_alt.lower()

        if main_or_alt not in ('main', 'alt'):
            return

        await self.add_sign(ctx, raidname, member.id, main_or_alt)

    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @customcommand.c_command(aliases=['rmplayer'], description="Removes given player from raid.", examples=["removeplayer @User#1234 MC"], perms=["Administrator", "manage server"])
    async def removeplayer(self, ctx, member: discord.Member, raidname):
        if member.id == self.bot.user.id or member.id is None:
            return

        playerclass = "Declined"
        await self.add_sign(ctx, raidname, member.id, playerclass)


def setup(bot):
    bot.add_cog(Signing(bot))
