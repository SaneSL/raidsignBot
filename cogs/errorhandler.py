import discord

from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Catches Command errors
        Parameters
        ----------
        ctx
        error
            CommandError child, the error that was raised
        """

        self.bot.log.error(ctx.message.content, exc_info=(type(error), error, error.__traceback__))
        ignored = (commands.CommandNotFound, commands.UserInputError, commands.CheckFailure, commands.CommandOnCooldown)
        
        # Get original error if exists
        error = getattr(error, 'original', error)
        
        if isinstance(error, (discord.NotFound, discord.Forbidden, discord.HTTPException)):
            return

        if isinstance(error, ignored):
            return

        return


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))