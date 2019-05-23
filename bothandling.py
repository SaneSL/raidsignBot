import discord
import shelve
import os
import json

from discord.ext import commands

# removeSign pitäisi tarkistaa, että poistetaanko declinestä vai jostain muualta, koska muuten se poistaa joka
# tapauksessa.
# Monen serverin tukeminen
# Moneen funtkioon tarvitaan tarkistus, jos syntöksi on virheellinen. Tästä ehkä oma funktio? Tehty?
# Hyllyt voisi tehdä serverin nimen/ID:n perusteella. Esim 1234-MC. Sitten siihen joku splittaus.


os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


bot = commands.Bot(command_prefix=cfg["prefix"])
bot.remove_command('help')


@bot.event
async def on_ready():

    # setupShelf = shelve.open("signs")

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

    await author.send(embed=embed)


@bot.command()
@commands.is_owner()
# @sign.before_invoke
# @decline.before_invoke
async def clear(ctx, amount=2):
    await ctx.channel.purge(limit=amount)


for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

bot.run(cfg["token"])
