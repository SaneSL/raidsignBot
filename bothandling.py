import discord
import shelve
import os
import json

# removeSign pitäisi tarkistaa, että poistetaanko declinestä vai jostain muualta, koska muuten se poistaa joka
# tapauksessa.
# Monen serverin tukeminen
# Moneen funtkioon tarvitaan tarkistus, jos syntöksi on virheellinen. Tästä ehkä oma funktio? Tehty?
# Hyllyt voisi tehdä serverin nimen/ID:n perusteella. Esim 1234-MC. Sitten siihen joku splittaus.

os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


from discord.ext import commands

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

# Alustus
setupTest = shelve.open("signs")
setupTest.close()


# Apufunktio oikean eventin valitsemista varte.
def selectevent(raidname):
    setup_shelf = None

    if raidname == "MC":
        setup_shelf = shelve.open("MC", writeback=True)

    elif raidname == "BWL":
        setup_shelf = shelve.open("BWL", writeback=True)

    return setup_shelf


# Alustaa eventin hyllyyn.
def setupevent(raidname):

    setup_shelf = selectevent(raidname)
    if setup_shelf is None:
        return

    setup_shelf["Warrior"] = set()
    setup_shelf["Rogue"] = set()
    setup_shelf["Hunter"] = set()
    setup_shelf["Warlock"] = set()
    setup_shelf["Mage"] = set()
    setup_shelf["Priest"] = set()
    setup_shelf["Shaman"] = set()
    setup_shelf["Druid"] = set()
    setup_shelf["Declined"] = set()

    setup_shelf.close()


def removesign(name, raidname):

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

@bot.event
async def on_ready():

    #setupShelf = shelve.open("signs")

   # if not setupShelf:
       # setupShelf.close()
       # setupEvent()

    # setupShelf.close()

    print('Bot is ready.')


@bot.command()
async def help(ctx):
    author = ctx.message.author

    embed = discord.Embed(colour=discord.Colour.dark_orange())

    s = "Sign to raids"

    embed.set_author(name='Help')
    embed.add_field(name='!sign', value=s, inline=False)

    # msg = 'Mee töihin'

    await author.send(embed=embed)

# Tarkista jos annettu raidi on virheellinen
@bot.command()
async def sign(ctx, raidname, playerclass):

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
    if not removesign(name, raidname):
        return
    setup_shelf[playerclass].add(name)

    # await ctx.message.delete(delay=3)

    setup_shelf.close()


@bot.command()
async def decline(ctx, raidname):

    raidname = raidname.upper()

    name = ctx.message.author.display_name
    if not removesign(name, raidname):
        return

    setup_shelf = selectevent(raidname)
    if setup_shelf is None:
        return

    setup_shelf["Declined"].add(name)
    # await ctx.message.delete(delay=3)

    setup_shelf.close()


@bot.command()
# @decline.after_invoke
# @sign.after_invoke
async def comp(ctx, raidname):

    raidname = raidname.upper()

    setup_shelf = selectevent(raidname)
    if setup_shelf is None:
        return

    # channel = bot.get_channel(577485845083324427)

    total_signs = 0

    for key in setup_shelf:
        total_signs += len(setup_shelf[key])

    embed = discord.Embed(
        title='Attending (' + str(total_signs) + ")",
        colour=discord.Colour.blue()
    )

    for key in setup_shelf:
        header = key + " (" + str(len(setup_shelf[key])) + ")"

        class_string = ""
        for nickname in setup_shelf[key]:
            class_string += nickname + "\n"

        if not class_string:
            class_string = "-"

        embed.add_field(name=header, value=class_string, inline=False)

    await ctx.send(embed=embed)

    setup_shelf.close()


@bot.command()
async def addevent(ctx, raidname):

    raidname = str(raidname).upper()
    setupevent(raidname)


# Poisto oikealta kanavalta


@bot.command()
@commands.is_owner()
# @sign.before_invoke
# @decline.before_invoke
async def clear(ctx, amount=2):
    await ctx.channel.purge(limit=amount)


@bot.command()
@commands.is_owner()
async def clearevent(ctx, raidname):
    raidname = raidname.upper()
    setupevent(raidname)


bot.run(cfg["token"])
