import discord

from discord.ext import commands


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(15, 15, commands.BucketType.member)

    @commands.command()
    async def help(self, ctx):
        author = ctx.message.author

        embed = discord.Embed(colour=discord.Colour.dark_orange())

        s = "Sign to raids"

        embed.set_author(name='Help')
        embed.add_field(name='!sign', value=s, inline=False)

        await author.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def clear(self, ctx, amount=2):
        await ctx.channel.purge(limit=amount)

    async def bot_check(self, ctx):
        if ctx.guild is None:
            return False
        bucket = self._cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return False
        # all global checks pass
        return True


def setup(bot):
    bot.add_cog(Misc(bot))
