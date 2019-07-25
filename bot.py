import discord
import os
import json
import asyncio
import asyncpg

from discord.ext import commands
from utils import customhelp

''' 
- Bot should respond if given information was invalid or otherwise didn't do anything.
- Note when getting members from guilds, if member leaves it can be an issue
- Make embed with info and post it to bot commands etc
- Make exception for cooldown in testcog
- Test what permissions bot needs
- Make sure getting channel works in all sending methods if its deleted and ID is in DB but not in guild cuz deleted
- change fetch message on most channels to fetch it from the proper channel
- improve autosign_add db wise
- on_ready use executeman
- setup_channels could be combined with the other one that checks all channels to reduce 1 query
- if all comp channels are deleted when bot comes online they are not deleted from db
- if bot is not given permissions it leaves the guild
- add to help like important tags like how to create raid etc and make embeds of those
- on guild_channel_delete could be improved to create the channel back, doesn't need to clear signs right?
- on guild join post embed like how to use bot, most usefull commands etc, this could be global embed so it could be
- ^reposted with like !howtouse
- Catch forbinned with command error unless local error handler.
- Somehow example needs to be included in help command? Maybe put it on help and use split etc.
- allow deleteraid to delete if channel doesnt exist
- clearraid doesnt work if raid msg doesnt exist, maybe make this constant with delraid
- add missing channels needs major reword, use con instead, not pool. Also reword add_autosign and some other stuff that is involved
- Maybe !raids doesn't need transaction and con.  
- Update mod commands with autoclear and off.


- \U0001f1fe YES -- 
- \U0001f1f3 NO -- 
- \U0001f1e6 A -- 
- \U0000267f wheelchair
- \U0001f1f2 M 
- \U0001f1e9 D 

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
    
- TESTED:
    - guild
    - membership
    - raidhandling
    - raidsigning
'''


def get_cfg():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('config.json') as json_data_file:
        cfg = json.load(json_data_file)
    return cfg


async def do_setup(cfg):
    pool = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    # await pool.execute('''
    # DROP TABLE IF EXISTS sign, raid, player, membership, guild CASCADE''')

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
    def __init__(self, prefixes, **kwargs):
        self.command_aliases = None
        self.cmd_prefixes = ", ".join(prefixes)

        self._cd = commands.CooldownMapping.from_cooldown(12, 12, commands.BucketType.user)

        self.join_message = discord.Embed(
            title="Raidsign bot",
            colour=discord.Colour.dark_teal()
        )
        self.join_message.add_field(name='Useful commands', value="`!help` for general help and list of commands.\n"
                                                                  "`!howtouse`"
                                                                  "`!botinfo` for information on bot.")
        super().__init__(**kwargs)

        # Load cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                #if name == 'testcog':
                    #continue
                self.load_extension(f"cogs.{name}")

        self.data()

    def data(self):
        command_aliases = {}
        for command in self.commands:
            if command.aliases:
                command_aliases[command.name] = command.aliases
        self.command_aliases = command_aliases


def run_bot():
    cfg = get_cfg()

    try:
        pool = asyncio.get_event_loop().run_until_complete(do_setup(cfg))
    except Exception as e:
        return

    bot = RaidSign(prefixes=cfg['prefix'], command_prefix=cfg['prefix'], help_command=customhelp.CustomHelpCommand())
    bot.pool = pool

    bot.run(cfg['token'])

run_bot()
