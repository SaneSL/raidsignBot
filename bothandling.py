import discord
import os
import json
import asyncio
import asyncpg

'''
When player is added to raid, should check if playername has changed aka if the user has changed their discord name
'''


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


# Load all cogs (classes)
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

asyncio.get_event_loop().run_until_complete(setup())
bot.run(cfg["token"])

