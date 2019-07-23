import discord
from discord.ext import commands

from utils import checks


class Misc(commands.Cog):
    """
    Miscellaneous command for deleting messages and some informative commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(12, 12, commands.BucketType.user)
        self.mod_commands = ['addchannels', 'addplayer', 'clearevent', 'delevent', 'editevent', 'readdevent',
                             'removeplayer']

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.command()
    async def botinfo(self, ctx):
        info_embed = discord.Embed(
            title="Raidsign bot",
            description="Discord bot to replace calendar system/signing for classic wow.\n You can report bugs, ask "
                        "questions about using the bot or request features at the discord server the bot provides.",
            colour=discord.Colour.dark_green()
        )
        info_embed.add_field(name='Links', value="[Discord](https://discord.gg/Y7hrmDD)\n"
                                                 "[Github](https://github.com/SaneSL/raidsignBot)\n"
                                                 "[Invite](AUTH HERE)")
        info_embed.set_footer(text="Made by Sane#4042")

        await ctx.channel.send(embed=info_embed)

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.command()
    async def modinfo(self, ctx):
        desc = "The commands listed below require the user to have either " \
               "`administrator` or `manage server` permission, except `!clear`, which requires `manage messages`" \
               ".\nThese requirements can be bypassed if the user has a role named `mod`. " \
               "This role needs to be created by the users."

        embed = discord.Embed(
            title="Mod info",
            description=desc,
            colour=discord.Colour.dark_green()
        )

        embed_value = '\n'.join(self.mod_commands) + "\nclear"

        embed.add_field(name="Mod commands:", value=embed_value)

        await ctx.channel.send(embed=embed)

    @commands.has_permissions(manage_messages=True)
    @commands.command(description="Clears given amount of messages from the channel, default = 2.")
    async def clear(self, ctx, amount=2):
        await ctx.channel.purge(limit=amount)

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.command()
    async def howtouse(self, ctx):
        msg_value = '```This section covers the basic usage of the bot. Use command `!help` for more help.\n\n' \
                    'Everyone who uses the bot should add their main class with `!addmain` and optionally an alt' \
                    ' with `!addalt`. This makes using the bot easier. Messages and channels created by the bot' \
                    ' should only be deleted/edited with bot commands. Incase a channel is deleted' \
                    ' (excluding bot-commands) created by the bot you can readd them with addchannels and' \
                    ' a message (event) with `readdevent`.\n\nMost of the signing to raids is intended happen via' \
                    ' having the role `AutoSign` (can be renamed). This makes you sign to all main raids with your' \
                    ' main class. A raid can be created the following command' \
                    ' !addraid <raidname> [note] [main], where [] parameters are optional.' \
                    ' Example !addraid MC "Some note" main. After this users can sign to the raid via' \
                    ' reacting or command !sign <raidname> <playerclass> or if they have the AutoSign role' \
                    ' (for main raids).\n\nUsers can see the current raids in #raidchannel and comps in ' \
                    '#compchannel (refresh every X minutes).```'

        embed = discord.Embed(
            title="How to use",
            description=msg_value,
            colour=discord.Colour.dark_green()
        )

        await ctx.channel.send(embed=embed)

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
