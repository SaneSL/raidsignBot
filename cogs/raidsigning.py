import discord

from discord.ext import commands
from globalfunctions import selectevent


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def removesign(self, name, raidname):

        setup_shelf = selectevent(raidname)
        # Jos raidin nimi on virheellinen.
        if setup_shelf is None:
            return False

        for key in setup_shelf:
            for nickname in setup_shelf[key]:
                if nickname == name:
                    setup_shelf[key].discard(name)
                    break

        setup_shelf.close()
        return True

    # Tarkista jos annettu raidi on virheellinen
    @commands.command()
    async def sign(self, ctx, raidname, playerclass):

        name = ctx.message.author.display_name

        playerclass = playerclass.title()
        raidname = raidname.upper()

        # Jos annettu raidin nimi on virheellinen.
        setup_shelf = selectevent(raidname)
        if setup_shelf is None:
            return

        # Jos annettu class on virheellinen.
        if playerclass not in setup_shelf:
            setup_shelf.close()
            return

        # Jos nimeä ei poisteta
        if not self.removesign(name, raidname):
            return
        setup_shelf[playerclass].add(name)

        # await ctx.message.delete(delay=3)

        setup_shelf.close()

    @commands.command()
    async def decline(self, ctx, raidname):

        raidname = raidname.upper()

        name = ctx.message.author.display_name
        if not self.removesign(name, raidname):
            return

        setup_shelf = selectevent(raidname)
        if setup_shelf is None:
            return

        setup_shelf["Declined"].add(name)
        # await ctx.message.delete(delay=3)

        setup_shelf.close()


def setup(bot):
    bot.add_cog(Signing(bot))

