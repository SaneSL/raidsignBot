import discord
from discord.ext import commands


class CustomCommands(commands.Command):
    def __init__(self, func, cd=None, examples=None, perms=None, **kwargs):
        super().__init__(func, **kwargs)
        self.cd = cd
        self.examples = examples
        self.perms = perms
