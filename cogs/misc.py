import discord
import re

from discord.ext import commands
from utils import checks


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(12, 12, commands.BucketType.user)

    @commands.command()
    async def help(self, ctx, sub=None):
        if sub is None:
            print("Default help here")
            return

        name = None

        if sub in self.bot.all_commands:
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
        """
        check_list = []

        for check in command.checks:
            check = str(check)
            result = re.search(r'\s(.*)\.<', check)
            result = result.group(1)
            check_list.append(result)

        if check_list:
            perms = ", ".join(check_list)
        else:
            perms = "None required."
        """

        perms = "EI OO"

        embed = discord.Embed(
            title='Command: ' + name,
            colour=discord.Colour.gold()
        )

        # embed.description = "Command name may differ due to aliases."

        if command.aliases:
            aliases = ", ".join(command.aliases)
        else:
            aliases = "None"

        embed.add_field(name='Aliases', value=aliases, inline=True)
        embed.add_field(name='Permissions', value=perms, inline=True)
        embed.add_field(name='Usage', value=command.signature + "\n [] parameters are optional.")

        await ctx.send(embed=embed)

    @commands.has_permissions(manage_messages=True)
    @commands.command()
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
