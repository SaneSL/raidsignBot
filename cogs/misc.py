import discord

from discord.ext import commands


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(12, 12, commands.BucketType.user)

    @commands.command()
    async def help(self, ctx, sub=None):
        if sub is None:
            print("Default help here")
            return

        command_names = [cmd.name for cmd in self.bot.commands]
        name = None

        if sub in self.bot.all_commands:
            print("XDDDDD")
            name = sub
        else:
            for key, value_list in self.bot.command.aliases:
                if sub in value_list:
                    name = key

        if name is None:
            return

        command = self.bot.get_command(name)

        if command is None:
            return

        embed = discord.Embed(
            title=name,
            colour=discord.Colour.gold()
        )

        embed.description = "The title might be different from what you typed in the help command depending on if it " \
                            "has aliases."

        if command.aliases:
            aliases = ", ".join(command.aliases)
        else:
            aliases = "Command has no aliases."

        embed.add_field(name='Aliases', value=aliases)

        await ctx.send(embed=embed)

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
