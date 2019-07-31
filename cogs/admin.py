import discord
import datetime

from discord.ext import commands


class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bladd(self, ctx, user_id: int):
        date = datetime.datetime.utcnow().date()

        await self.bot.pool.execute('''
        INSERT INTO blacklist
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', user_id, date)

        await self.bot.pool.execute('''
        DELETE
        FROM player
        WHERE id = $1''', user_id)

    @commands.command()
    async def blrm(self, ctx, user_id: int):
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

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)


def setup(bot):
    bot.add_cog(Admin(bot))
