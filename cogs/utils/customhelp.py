import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **kwargs):
        super().__init__(verify_checks=False, command_attrs={"hidden": True})
        self.mod_cmds = kwargs.pop('mod_cmds')
        self.prefixes = ", ".join(kwargs.pop('prefixes'))

    async def send_command_help(self, command):
        """
        Sends help embed of given command to invokers channel
        Parameters
        ----------
        command
            Instance of Command
        """

        # Fixes help command subclassing issue with custom command
        if command.name == 'help':
            return

        footer_value = "Note: you may be able to use the command multiple times before triggering the cooldown.\n" \
                       "You should get a response or see the results of your command."

        embed = discord.Embed(
            title='Command: ' + command.name,
            colour=discord.Colour.gold()
        )

        cd = getattr(command._buckets._cooldown, 'per', None)

        if cd is not None:
            cd = int(cd)
            if cd < 60:
                cd_value = str(cd) + ' second(s)'
            else:
                cd_value = str(cd // 60) + ' minute(s)'
        else:
            cd_value = '-'

        if command.description:
            desc = command.description
        else:
            desc = "-"

        if command.examples is not None:
            example = "\n".join(('!' + x for x in command.examples))
        else:
            example = '-'

        if command.perms is not None:
            perms = "\n".join(perm for perm in command.perms)
        else:
            perms = '-'

        if command.aliases:
            aliases = "\n".join(command.aliases)
        else:
            aliases = "-"

        if command.signature:
            usage_value = '!' + command.name + ' ' + command.signature + '\n [] parameters are optional.\n' \
                                                                         'If you want to give a parameter with spaces' \
                                                                         ' use quotation marks `""`'
        else:
            usage_value = '!' + command.name

        embed.description = desc
        embed.add_field(name='Aliases', value=aliases, inline=True)
        embed.add_field(name='Permissions (Any)', value=perms, inline=True)
        embed.add_field(name='Cooldown', value=cd_value, inline=True)
        embed.add_field(name='Usage', value=usage_value, inline=False)
        embed.add_field(name="Example(s)", value=example, inline=False)
        embed.set_footer(text=footer_value)

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_cog_help(self, cog):
        """
        Sends help embed of given cog to invokers channel

        Parameters
        ----------
        cog
            Instance of Cog
        """
        embed = discord.Embed(
            title=f"Category: {cog.qualified_name}",
            description=cog.description or "-",
            colour=discord.Colour.gold()
        )

        sorted_commands = await self.filter_commands(cog.get_commands(), sort=True)

        """
        cmd_list = []

        for cmd in sorted_commands:
            cmd_name = str(cmd)

            desc = ""

            if cmd.description:
                desc = ' - ' + cmd.description

            cmd_name = cmd_name + desc
            cmd_list.append(cmd_name)

        cmd_string = '\n'.join(cmd_list)
        """

        embed.add_field(name='Commands:', value='\n'.join(str(cmd) + ' - !' + cmd.name + " " + cmd.signature for
                                                          cmd in sorted_commands))

        footer = """[] parameters are optional.\n'If you want to give a parameter with spaces use
         quotation marks " " """

        embed.set_footer(text=footer)

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_bot_help(self, mapping):
        """
        Sends embed with a list of all commands and other info to invokers channel
        Parameters
        ----------
        mapping
            Dict with Cogs and their Commands
        """
        embed = discord.Embed(
            title="All categories and commands",
            description="To get information on a specific command or category type\n"
                        "`!help <command/category`",
            colour=discord.Colour.gold()
        )

        no_category = "No category:"

        for cog, cog_commands in mapping.items():
            sorted_commands = await self.filter_commands(cog_commands, sort=True)
            if sorted_commands:
                name = cog.qualified_name if cog is not None else no_category

                cmd_list = []

                for cmd in sorted_commands:
                    cmd_name = str(cmd)
                    if cmd_name in self.mod_cmds:
                        cmd_name = '__' + cmd_name + '__'
                    cmd_list.append(cmd_name)

                cmd_string = '\n'.join(cmd_list)

                embed.add_field(name=name, value=cmd_string)

        footer_value = 'Underlined commands require either administrator or manage server permissions or ' \
                       'for the user to have role called mod, except !clear, which requires manage messages.'

        embed.set_footer(text=footer_value)

        embed.add_field(name='Prefixe(s)', value=self.prefixes, inline=False)

        dest = self.get_destination()

        await dest.send(embed=embed)
