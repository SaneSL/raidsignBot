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
        if playerclass is None:
            await ctx.send("Invalid class")
            return

        if player_id is None:
            player_id = ctx.message.author.id

        raidname = raidname.upper()
        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.pool, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        if not await sign_player(self.bot.pool, player_id, raid_id, playerclass):
            await ctx.send("No player")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Signs to given raid with given class.",
                      brief='{"examples":["sign mc rogue"], "cd":"60"}')
    async def sign(self, ctx, raidname, playerclass):
        await self.add_sign(ctx, raidname, playerclass)

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Adds declined status to given raid.",
                      brief='{"examples":["decline MC"], "cd":"60"}')
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await self.add_sign(ctx, raidname, playerclass)

    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(description="Adds given player to raid.", help="Administrator, manage server",
                      brief='{"examples":["addplayer @User#1234 MC rogue"], "cd":"60"}')
    async def addplayer(self, ctx, member: discord.Member, raidname, playerclass):
        if member.id == self.bot.user.id:
            return

        await self.add_sign(ctx, raidname, playerclass, member.id)

    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(aliases=['rmplayer'], description="Removes given player from raid.",
                      help="Administrator, manage server", brief='{"examples":["removeplayer @User#1234 Mc"],'
                                                                 ' "cd":"60"')
    async def removeplayer(self, ctx, member: discord.Member, raidname):
        if member.id == self.bot.user.id:
            return

        playerclass = "Declined"
        await self.add_sign(ctx, raidname, playerclass, member.id)


def setup(bot):
    bot.add_cog(Signing(bot))
