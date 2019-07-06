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
- Make some backup if someone deletes the channels bot created
- ^Check guild and events
- Notify user in raid event that it is main
- On_guild_channel_delete could use exists rather than get
- Maybe on setup channels check if only one channel was deleted
- \U0001f1f3 NO
- \U0001f1fe YES
- \U0001f1e6 A
- \U0000267f wheelchair

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
'''

from discord.ext import commands

'''
os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


bot = commands.Bot(command_prefix=cfg["prefix"])
bot.remove_command('help')


async def setup():
    bot.db = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

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
'''


def get_cfg():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('config.json') as json_data_file:
        cfg = json.load(json_data_file)
    return cfg


async def do_setup(cfg):
    db = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    # await bot.db.execute('''DROP TABLE IF EXISTS testitable''')

    fd = open("setupsql.txt", "r")
    file = fd.read()
    fd.close()

    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await db.execute(command)

    return db


class RaidSign(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.remove_command('help')

        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                self.load_extension(f"cogs.{name}")


def run_bot():
    cfg = get_cfg()
    bot = RaidSign(command_prefix=cfg['prefix'])
    bot.db = asyncio.get_event_loop().run_until_complete(do_setup(cfg))
    bot.run(cfg['token'])


run_bot()
