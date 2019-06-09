import discord
import os
import json
import asyncio
import asyncpg

''' 
- Bot should respond if given information was invalid or otherwise didn't do anything.
- Add some way of auto signing to raids
- Raids should tell the day like "Monday" instead of date and maybe time also, this is partialyl done in the note when
- creating raid
- Command to track attendance and clear raid with one "master" command
- You can get Message from msg = await ctx.message....
- Make cog creation from list a function, used in levels and raidhandling atleast
- Auto sign needs to take into account if player has already declined the event
- Transaction to addlevelbyrole
- Note when getting members from guilds, if member leaves it can be an issue
- Improve on_raw_reaction to add role if it doesnt and also sign to raid.
- Clear db and remove guild etc when bot leaves a guild
- Copy records to table
- Parameter for create events if they are mainevents and that information could be stored to table so autosign can tell
- which events are mainevents.
- rename membership class to playerclass or rename sign playerclass to class
- deleting raidevents could maybe be based of name rather than ID -not good?
- make alt and main options
- edit raidinfo method needed
- \U0001f1f3 NO
- \U0001f1fe YES
- \U0000267f wheelchair 
'''


from discord.ext import commands

os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)


bot = commands.Bot(command_prefix=cfg["prefix"])
bot.remove_command('help')


async def setup():
    bot.db = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    await bot.db.execute('''DROP TABLE IF EXISTS testitable''')

    fd = open("setupsql.txt", "r")
    file = fd.read()
    fd.close()

    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await bot.db.execute(command)


# Load all cogs (classes)
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        name = filename[:-3]
        bot.load_extension(f"cogs.{name}")

asyncio.get_event_loop().run_until_complete(setup())
bot.run(cfg["token"])
