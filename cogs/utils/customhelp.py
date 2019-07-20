import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()

    async def send_command_help(self, command):
        embed = discord.Embed(
            title='Command: ' + command.name,
            colour=discord.Colour.gold()
        )

        cd_value = 'None'
        perms = 'None'

        # Desc // Cooldown // Perms
        # Desc[0], Cooldown[1], Perms[2]

        if command.help is not None:
            command_info = command.help.split('// ')
            if command_info[0]:
                embed.description = command_info[0]

            if command_info[1]:
                cd = int(command_info[1])
                if cd < 60:
                    cd_value = str(cd) + ' second(s)'
                else:
                    cd_value = str(cd//60) + ' minute(s)'

            if command_info[2]:
                perms = command_info[2]
                
        if command.aliases:
            aliases = ", ".join(command.aliases)
        else:
            aliases = "None"

        if command.signature:
            usage_value = '!' + command.name + ' ' + command.signature + "\n [] parameters are optional."
        else:
            usage_value = '!' + command.name

        embed.add_field(name='Aliases', value=aliases, inline=True)
        embed.add_field(name='Permissions', value=perms, inline=True)
        embed.add_field(name='Cooldown', value=cd_value, inline=True)
        embed.add_field(name='Usage', value=usage_value)

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_cog_help(self, cog):
       # print(cog.__cog_name__)

        embed = discord.Embed(
            title=f"Category: {cog.qualified_name}",
            description=cog.description or "No description",
            colour=discord.Colour.gold()
        )

        sorted_commands = await self.filter_commands(cog.get_commands(), sort=True)

        embed.add_field(name='Commands:', value='\n'.join(str(cmd) for cmd in sorted_commands))

        dest = self.get_destination()

        await dest.send(embed=embed)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="All categories and commands",
            description='Test',
            colour=discord.Colour.gold()
        )

        no_category = "No category:"

        for cog, cog_commands in mapping.items():
            sorted_commands = await self.filter_commands(cog_commands, sort=True)
            if sorted_commands:
                name = cog.qualified_name if cog is not None else no_category
                embed.add_field(name=name, value='\n'.join(str(cmd) for cmd in sorted_commands))

        dest = self.get_destination()

        await dest.send(embed=embed)
