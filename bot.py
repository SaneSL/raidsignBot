import discord
import os
import json
import asyncio
import asyncpg

from discord.ext import commands

''' 
- Bot should respond if given information was invalid or otherwise didn't do anything.
- Note when getting members from guilds, if member leaves it can be an issue
- reactionsign doesnt work if bot is offline, maybe make command to counter this with on_ready
- Check add raid ifs
- Make embed with info and post it to bot commands etc
- Make exception for cooldown in testcog
- Test what permissions bot needs
- Possible improvments to setup_channels with saving category and getting it with guild.categories, maybe not needed.
- Check if both of the raid/comp channels exist on join, with get_channel in the actual guild and not just in db DONE?
- Make sure getting channel works in all sending methods if its deleted and ID is in DB but not in guild cuz deleted
- Maybe add deleting raid manually to on_message_delete?
- Improve the error handling in raidhandling atleast 
- add reacted signs in events needs to be done
- change fetch message on most channels to fetch it from the proper channel
- if you react to raid and you have already reacted with the other one, remove the old one to make ^easier ?? cant be done
- reasonably I guess
- improve autosign_add db wise
- ^also check if something is none and maybe checkj if user is member of guild??
- removealt but I guess its useless
- on_ready use executeman
- setup_channels could be combined with the other one that checks all channels to reduce 1 query
- if all comp channels are deleted when bot comes online they are not deleted from db
- bot apparently can't remove roles from server owners so do something about this
- add some send to autosign if the role is not found etc
- check what happens if for example autosign adds ppl to raids and someone clears it at the same time
- if bot is not given permissions it leaves the guild

- \U0001f1fe YES -- 
- \U0001f1f3 NO -- 
- \U0001f1e6 A -- 
- \U0000267f wheelchair

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
    
- TESTED:
    - membership
    - guild
    - misc
'''


def get_cfg():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('config.json') as json_data_file:
        cfg = json.load(json_data_file)
    return cfg


async def do_setup(cfg):
    pool = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    fd = open("setup.sql", "r")
    file = fd.read()
    fd.close()

    # Remove empty values
    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await pool.execute(command)

    return pool


class RaidSign(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.remove_command('help')

        # Load cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                self.load_extension(f"cogs.{name}")


def run_bot():
    cfg = get_cfg()
    bot = RaidSign(command_prefix=cfg['prefix'])
    bot.pool = asyncio.get_event_loop().run_until_complete(do_setup(cfg))
    bot.run(cfg['token'])


run_bot()
