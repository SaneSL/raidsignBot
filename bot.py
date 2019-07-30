import discord
import os
import json
import asyncio
import asyncpg
import datetime
import logging

from collections import Counter
from discord.ext import commands
from utils import customhelp

''' 
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
- Handle permission error
- Autosign add could prolly be reworked to be more effective. IE just cursor all members with autosign role and add
- ^them to all raids with main that have matching ID / MAIN check the FAQ and use expression In
- add timestamp to blacklist
- Improve raidhandling adding raids sends etc
- Figure something out for calling add_bot_raids or something
- Test logging
- Improve error message sending and add cooldowns

- \U0001f1fe YES -- 
- \U0001f1f3 NO -- 
- \U0001f1e6 A -- 
- \U0000267f wheelchair
- \U0001f1f2 M 
- \U0001f1e9 D 

- Perms: 268823792

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
    
- TESTED:
    - guild
    - membership
    - raidhandling
    - raidsigning
'''

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_cfg():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('config.json') as json_data_file:
        cfg = json.load(json_data_file)
    return cfg


async def load_blacklist(pool):
    records = await pool.fetch('''
    SELECT userid
    FROM blacklist''')

    blacklist = [record['userid'] for record in records]

    return blacklist

async def do_setup(cfg):
    pool = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    #await pool.execute('''
    #DROP TABLE IF EXISTS sign, raid, player, membership, guild CASCADE''')

    fd = open("setup.sql", "r")
    file = fd.read()
    fd.close()

    def clear_stuff(elem):
        if elem == '\n' or not elem:
            return False
        else:
            return True

    # Remove empty values
    sqlcommands = file.split(';')
    sqlcommands = list(filter(clear_stuff, sqlcommands))

    for command in sqlcommands:
        await pool.execute(command)

    blacklist = await load_blacklist(pool)

    return pool, blacklist


class RaidSign(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pool = kwargs['pool']
        self.cmd_prefixes = ", ".join(kwargs['command_prefix'])
        self.mod_cmds = kwargs['mod_cmds']
        self.blacklist = kwargs['blacklist']
        self.cd = commands.CooldownMapping.from_cooldown(8, 12, commands.BucketType.user)
        self.cd_counter = Counter()

        # Load cogs
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                # if name == 'testcog':
                    # continue
                self.load_extension(f"cogs.{name}")

    async def blacklist_user(self, user_id):
        date = datetime.datetime.utcnow().date()

        await self.pool.execute('''
        INSERT INTO blacklist
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', user_id, date)

        await self.pool.execute('''
        DELETE
        FROM player
        WHERE id = $1''', user_id)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is None:
            return

        bucket = self.cd.get_bucket(message)
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
        retry_after = bucket.update_rate_limit(current)
        author_id = message.author.id

        if retry_after:
            print("CD")

        if retry_after and author_id != self.owner_id:
            self.cd_counter[author_id] += 1
            if self.cd_counter[author_id] >= 5:
                await self.blacklist_user(author_id)
                del self.cd_counter[author_id]
                return
        else:
            self.cd_counter.pop(author_id, None)

        await self.invoke(ctx)


def run_bot():
    cfg = get_cfg()

    try:
        pool, blacklist = asyncio.get_event_loop().run_until_complete(do_setup(cfg))
    except:
        return

    bot = RaidSign(command_prefix=cfg['prefix'], blacklist=blacklist, pool=pool, mod_cmds=cfg['mod_cmds'],
                   help_command=customhelp.CustomHelpCommand(mod_cmds=cfg['mod_cmds'], prefixes=cfg['prefix']))
    bot.run(cfg['token'])


run_bot()
