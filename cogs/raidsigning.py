import discord

from discord.ext import commands
from utils.globalfunctions import is_valid_class, sign_player, get_raidid
from utils import checks


class Signing(commands.Cog):
    """
    This category handles signing to raids.
    Most of the signing should be done via reacting or having the 'AutoSign' role.
    """
    def __init__(self, bot):
        self.bot = bot

    async def add_sign(self, ctx, raidname, playerclass, player_id=None):
        playerclass = await is_valid_class(playerclass)

        if player_id == self.bot.user.id:
            return

        if playerclass is None:
            await ctx.send("Invalid class")
            return

        if player_id is None or not isinstance(player_id, int):
            player_id = ctx.message.author.id

        raidname = raidname.upper()
        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        if not await sign_player(self.bot.pool, player_id, raid_id, playerclass):
            await ctx.send("No player")

    @commands.command(description="Signs to given raid with given class.")
    async def sign(self, ctx, raidname, playerclass):
        await self.addplayer(ctx, raidname, playerclass)

        # await ctx.invoke(self.raids.comp, ctx, raidname)

    @commands.command(description="Adds declined status to given raid.")
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await self.addplayer(ctx, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(description="Adds given player to raid.", help="Administrator, manage server",
                      brief='{"examples":["addplayer @User#1234 MC rogue"], "cd":""}')
    async def addplayer(self, ctx, member: discord.Member, raidname, playerclass):
        if member.id == self.bot.user.id:
            return

        member = ctx.guild.get_member(member.id)

        # No id found
        if member is None:
            await ctx.send("No player found.")
            return

        await self.add_sign(ctx, raidname, playerclass, member.id)

    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['rmplayer'], description="Removes given player from raid.",
                      help="Administrator, manage server", brief='{"examples":["removeplayer @User#1234 Mc"], "cd":""')
    async def removeplayer(self, ctx, member: discord.Member, raidname):
        if member.id == self.bot.user.id:
            return

        # No id found
        if member is None:
            await ctx.send("No player found.")
            return

        playerclass = "Declined"
        await self.add_sign(ctx, raidname, playerclass, member.id)


def setup(bot):
    bot.add_cog(Signing(bot))
