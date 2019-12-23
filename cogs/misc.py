import discord
from discord.ext import commands
from .utils import customcommand


class Misc(commands.Cog):
    """
    Command to delete messages and some informative/helpful commands.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @customcommand.c_command(hidden=True)
    async def botinfo(self, ctx):
        """
        Sends info embed to invokers channel

        Parameters
        ----------
        ctx
        """

        info_embed = discord.Embed(
            title="Raidsign bot",
            description="Discord bot to replace calendar system/signing for classic wow.\n You can report bugs, ask "
                        "questions about using the bot or request features at the discord server the bot provides.",
            colour=discord.Colour.dark_green()
        )
        info_embed.add_field(name='Links', value="[Discord](https://discord.gg/Y7hrmDD)\n"
                                                 "[Github](https://github.com/SaneSL/raidsignBot)\n"
                                                 "[Invite](https://discordapp.com/api/oauth2/authorize?client_"
                                                 "id=577447640652840960&permissions=268561648&scope=bot)")
        info_embed.set_footer(text="Made by Sane#4042")

        await ctx.send(embed=info_embed)

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @customcommand.c_command()
    async def modinfo(self, ctx):
        """
        Sends info about mod commands to invokers channel

        Parameters
        ----------
        ctx
        """

        desc = "The commands listed below require the user to have either " \
               "`administrator` or `manage server` permission, except `!clear`, which requires `manage messages`" \
               ".\nThese requirements can be bypassed if the user has a role named `mod`. " \
               "This role needs to be created by the users."

        embed = discord.Embed(
            title="Mod info",
            description=desc,
            colour=discord.Colour.dark_green()
        )

        embed_value = '\n'.join(self.bot.mod_cmds)

        embed.add_field(name="Mod commands:", value=embed_value)

        await ctx.send(embed=embed)

    @commands.has_permissions(manage_messages=True)
    @customcommand.c_command(description="Clears given amount of messages from the channel, default = 2.", examples=["clear", "clear 5"])
    async def clear(self, ctx, amount=2):
        """
        Clears messages from text channel

        Parameters
        ----------
        ctx
        amount
        """

        await ctx.channel.purge(limit=amount)

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @customcommand.c_command()
    async def howtouse(self, ctx):
        """
        Sends info about using the bot to invoker's channel

        Parameters
        ----------
        ctx
        """

        msg_value = '```This section covers the basics on how to use the bot.\n' \
                    'Use command !help for more help. \n\n' \
                    'Everyone who uses to bot should add their main class and possibly an alt class. \n' \
                    'Example: !addmain mage frost and !addalt rogue combat \n\n' \
                    'The bot allows users with a role called "autosign" to automatically sign to raids that are ' \
                    'marked as "main" raids.\n' \
                    'Example: Get the role with !autosign and add the raid with !addraid MC main\n\n' \
                    'After the raid is over you can clear the signs manually or use automated feature, ' \
                    'which you have to setup.\n' \
                    'More info on this automated feature use !help autoclear.\n\n' \
                    'Some commands have cooldowns. This means if you use the command X amount of times in certain \n' \
                    'timeframe the cooldown triggers. More info on this with !help <command>. \n\n' \
                    'Prefixes ' + self.bot.cmd_prefixes + '\nLook into topics on bot created channels!```' \

        await ctx.send(msg_value)

    @customcommand.c_command()
    async def whatsnew(self, ctx):
        """
        Sends embed about new features to invoker's channel
        Parameters
        ----------
        ctx
        """
        
        msg = '```addmain and alt commands now support spec, use specific spec name! \n' \
              'Example : !addmain mage frost \n' \
              'Comps now display class/spec icon and sign order. \n' \
              'Removed manual sign and decline.```'

        await ctx.send(msg)


def setup(bot):
    bot.add_cog(Misc(bot))
