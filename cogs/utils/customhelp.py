import json
import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **kwargs):
        self.mod_cmds = kwargs.pop('mod_cmds')

        self.prefixes = ", ".join(kwargs.pop('prefixes'))

        super().__init__(verify_checks=False)

    # desc = desc, help = perms, brief = cd
    async def send_command_help(self, command):
        embed = discord.Embed(
            title='Command: ' + command.name,
            colour=discord.Colour.gold()
        )

        cd_value = 'None'
        perms = 'None'
        desc = "No Description"
        example = '!' + command.name

        if command.description:
            desc = command.description

        if command.brief is not None:
            brief_dict = json.loads(command.brief)

            example_list = brief_dict.get("examples", None)
            cd = brief_dict.get('cd', None)

            # Replace ` with quotes
            if example_list is not None and example_list:
                example_list[:] = [s.replace('`', "\"") for s in example_list]
                example = "\n".join(('!' + x for x in example_list))

            if example_list is not None and cd:
                cd = int(cd)
                if cd < 60:
                    cd_value = str(cd) + ' second(s)'
                else:
                    cd_value = str(cd//60) + ' minute(s)'

        if command.help is not None:
            permlist = command.help.split(', ')
            perms = " OR\n".join(perm for perm in permlist)
                
        if command.aliases:
            aliases = "\n".join(command.aliases)
        else:
            aliases = "None"

        if command.signature:
            usage_value = '!' + command.name + ' ' + command.signature + '\n [] parameters are optional.\n' \
                                                                         'If you want to give a parameter with spaces' \
                                                                         ' use quotation marks `""`'
        else:
            usage_value = '!' + command.name

        embed.description = desc
        embed.add_field(name='Aliases', value=aliases, inline=True)
        embed.add_field(name='Permissions', value=perms, inline=True)
        embed.add_field(name='Cooldown', value=cd_value, inline=True)
        embed.add_field(name='Usage', value=usage_value, inline=False)
        embed.add_field(name="Example(s)", value=example, inline=False)

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"Category: {cog.qualified_name}",
            description=cog.description or "No description",
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

        footer = "[] parameters are optional.\n'If you want to give a parameter with spaces use quotation marks `""`'"

        embed.set_footer(text=footer)

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_bot_help(self, mapping):
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
