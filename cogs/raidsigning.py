from discord.ext import commands
import re
from utils.globalfunctions import is_valid_class, sign_player, get_raidid


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sign(self, ctx, raidname, playerclass, player_id=None):
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

        if not (await sign_player(self.bot.pool, player_id, raid_id, playerclass)):
            await ctx.send("No player")

        # await ctx.invoke(self.raids.comp, ctx, raidname)

    @commands.command()
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.sign, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass):
        member_id = int(re.sub(r"\D", "", name))

        if member_id == self.bot.user.id:
            return

        member = ctx.guild.get_member(member_id)

        # No id found
        if member is None:
            await ctx.send("No player found")
            return

        await ctx.invoke(self.sign, raidname, playerclass, member_id)

    @commands.command()
    async def removeplayer(self, ctx, name, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.addplayer, name, raidname, playerclass)


def setup(bot):
    bot.add_cog(Signing(bot))
