import discord
from discord.ext import commands


class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    """
    Admin commands not visible/usable for normal users. Require bot ownership to use.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bladd(self, ctx, user_id: int):
        await self.bot.blacklist_user(user_id)

    @commands.command()
    async def blrm(self, ctx, user_id: int):
        if user_id in self.bot.blacklist:
            self.bot.blacklist.remove(user_id)

        await self.bot.pool.execute('''
        DELETE
        FROM blacklist
        WHERE userid = $1''', user_id)

    @commands.command()
    async def checkbl(self, ctx, user_id: int):
        ban_date = await self.bot.pool.fetchval('''
        SELECT bandate
        FROM blacklist
        WHERE userid = $1''', user_id)

        if ban_date is None:
            await ctx.send("This user hasn't been banned.")
        else:
            await ctx.send(f"This user was banned on {ban_date}")

    @commands.command()
    async def c_status(self, ctx, *, status):
        game = discord.Game(status)
        await self.bot.change_presence(activity=game)

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)


def setup(bot):
    bot.add_cog(Admin(bot))
