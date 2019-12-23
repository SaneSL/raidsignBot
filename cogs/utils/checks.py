import discord

from discord.ext import commands


async def is_mod(ctx):
    """
    Checks if command invoker has role named 'mod'

    Parameters
    ----------
    ctx

    Returns
    -------
    True or False
    """

    role = discord.utils.get(ctx.guild.roles, name='mod')
    if role is None:
        return False
    elif role in ctx.author.roles:
        return True
    else:
        return False


async def check_any_permission(ctx, perms, *, check=any):
    """
    Checks if user has any of the given discord permissions

    Parameters
    ----------
    ctx
    perms
        Discord permission kwargs
    check
        To check any or all

    Returns
    -------
    True or False
    """
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    if await is_mod(ctx):
        return True

    user_perms = ctx.author.guild_permissions

    return check(getattr(user_perms, name, None) == value for name, value in perms.items())


def has_any_permission(*, check=any, **perms):
    """
    Decorator, see check_any_permissions

    Parameters
    ----------
    check
        Discord permission kwargs
    perms
        To check any or all

    Returns
    -------
        True or False
    """
    async def pred(ctx):
        return await check_any_permission(ctx, perms, check=check)
    return commands.check(pred)
