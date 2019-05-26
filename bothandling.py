import discord
import os
import json
import asyncio
import asyncpg


from discord.ext import commands

os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


bot = commands.Bot(command_prefix=cfg["prefix"])
bot.remove_command('help')


async def setup():
    bot.db = await asyncpg.connect(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    # await bot.db.execute('''DROP TABLE IF EXISTS ''')

    fd = open("setupsql.txt", "r")
    file = fd.read()
    fd.close()

    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await bot.db.execute(command)


@bot.event
async def on_ready():
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

# Load all cogs (classes)
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

asyncio.get_event_loop().run_until_complete(setup())
bot.run(cfg["token"])

