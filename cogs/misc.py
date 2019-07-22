import discord
import re

from discord.ext import commands
from utils import checks


class Misc(commands.Cog):
    """
    Miscellaneous command for deleting messages and some informative commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self.check_help_status = False
        self._cd = commands.CooldownMapping.from_cooldown(12, 12, commands.BucketType.user)

        self.mod_commands = ['addchannels', 'addplayer', 'clear', 'clearevent', 'delevent', 'editevent', 'readdevent',
                             'removeplayer']
        self.info_embed = discord.Embed(
            title="Raidsign bot",
            description="Discord bot to replace calendar system/signing for classic wow.\n You can report bugs, ask "
                        "questions about using the bot or request features at the discord server the bot provides.",
            colour=discord.Colour.dark_green()
        )
        self.info_embed.add_field(name='Links', value="[Discord](https://discord.gg/Y7hrmDD)\n[Github]"
                                                      "(https://github.com/SaneSL/raidsignBot)\n [Invite](AUTH HERE)")
        self.info_embed.set_footer(text="Made by Sane#4042")

        self.help_embed = discord.Embed(
            title="Help",
            description="To get information on a specific command type `!help <command>`\nMod commands require one of "
                        "the following permissions: administrator, manage server or having role named `mod`.",
            colour=discord.Colour.dark_green()
        )

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.command(help="Information about the bot.// 300 // ")
    async def botinfo(self, ctx):
        await ctx.channel.send(embed=self.info_embed)

    @commands.command()
    async def info(self, ctx):
        await ctx.channel.send(embed=self.bot.join_message)

    @commands.command()
    async def help(self, ctx, sub=None):
        if self.check_help_status is False:
            self.help_embed.add_field(name='Commands', value=", ".join([x.name for x in self.bot.commands]))
            self.help_embed.add_field(name="Mod commands", value=", ".join([x for x in self.mod_commands]))
            self.help_embed.add_field(name="Prefixes", value=self.bot.cmd_prefixes)
            self.check_help_status = True

        if sub is None:
            await ctx.send(embed=self.help_embed)
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

        cmd = self.bot.get_command(name)

        if cmd is None:
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

        cd_value = 'None'
        perms = 'None'

        # Desc // Cooldown // Perms
        # Desc[0], Cooldown[1], Perms[2]

        if cmd.help is not None:
            cmd_info = cmd.help.split('// ')
            if cmd_info[0]:
                embed.description = cmd_info[0]

            if cmd_info[1]:
                cd = int(cmd_info[1])
                if cd < 60:
                    cd_value = str(cd) + ' second(s)'
                else:
                    cd_value = str(cd//60) + ' minute(s)'

            if cmd_info[2]:
                perms = cmd_info[2]


        # embed.description = "Command name may differ due to aliases."

        if cmd.aliases:
            aliases = ", ".join(cmd.aliases)
        else:
            aliases = "None"

        if cmd.signature:
            usage_value = '!' + name + ' ' + cmd.signature + "\n [] parameters are optional."
        else:
            usage_value = '!' + name

        embed.add_field(name='Aliases', value=aliases, inline=True)
        embed.add_field(name='Permissions', value=perms, inline=True)
        embed.add_field(name='Cooldown', value=cd_value, inline=True)
        embed.add_field(name='Usage', value=usage_value)

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
