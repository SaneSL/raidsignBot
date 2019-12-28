import discord
from discord.ext import commands


class CustomCommand(commands.Command):
    """
    A subclass of Command with few added attributes

    Attributes
    ----------
    examples
        List of command usage examples
    perms
        List of required discord permissions to use the command
    """
    def __init__(self, func, examples=None, perms=None, **kwargs):
        super().__init__(func, **kwargs)
        self.examples = examples
        self.perms = perms


def c_command(**kwargs):
    """
    Decorator for commands

    Parameters
    ----------
    kwargs

    Returns
    -------
    Decortator that transform command into a class Command
    """
    return commands.command(cls=CustomCommand, **kwargs)