import discord

from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError, commands.CheckFailure)

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return
    """

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))