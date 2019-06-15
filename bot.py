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
- Transaction to addlevelbyrole
- Note when getting members from guilds, if member leaves it can be an issue
- Clear db and remove guild etc when bot leaves a guild
- Copy records to table
- Parameter for create events if they are mainevents and that information could be stored to table so autosign can tell
- which events are mainevents.
- deleting raidevents could maybe be based of name rather than ID -not good?
- reactionsign doesnt work if bot is offline, maybe make command to counter this
- @commands.has_permissions(administration=True)
- Check add raid ifs
- Handle errors if command is used in wrong channel or now change all commands which need comp channel or raid channel
- to work correctly.
- \U0001f1f3 NO
- \U0001f1fe YES
- \U0001f1e6 A
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
