import discord
import os
import json
import asyncio
import asyncpg

''' 
- Bot should respond if given information was invalid or otherwise didn't do anything.
- You can get Message from msg = await ctx.message....
- Make cog creation from list a function, used in levels and raidhandling atleast
- Auto sign needs to take into account if player has already declined the event
- Note when getting members from guilds, if member leaves it can be an issue
- reactionsign doesnt work if bot is offline, maybe make command to counter this
- Check add raid ifs
- Handle errors if command is used in wrong channel or now change all commands which need comp channel or raid channel
- to work correctly.
- Overall improvemts to how the db is handled, so no unnesessary connections are opened. Not needed?
- Make bot create channel category and channels on join or make command and send embed to those channels telling what
- they are
- Make exception for cooldown in testcog
- Make class from bot.py

- \U0001f1f3 NO
- \U0001f1fe YES
- \U0001f1e6 A
- \U0000267f wheelchair

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
'''

from discord.ext import commands

os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


bot = commands.Bot(command_prefix=cfg["prefix"])
bot.remove_command('help')


async def setup():
    bot.db = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    # await bot.db.execute('''DROP TABLE IF EXISTS testitable''')

    fd = open("setupsql.txt", "r")
    file = fd.read()
    fd.close()

    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await bot.db.execute(command)


@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# Load all cogs (classes)
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

asyncio.get_event_loop().run_until_complete(setup())
bot.run(cfg["token"])
