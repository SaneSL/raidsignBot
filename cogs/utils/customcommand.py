import discord
from discord.ext import commands


class CustomCommand(commands.Command):
    def __init__(self, func, cd=None, examples=None, perms=None, **kwargs):
        super().__init__(func, **kwargs)
        self.cd = cd
        self.examples = examples
        self.perms = perms


def c_command(**kwargs):
    return commands.command(cls=CustomCommand, **kwargs)