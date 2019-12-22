import discord
import os
import json
import asyncio
import asyncpg
import datetime
import logging

from collections import Counter
from discord.ext import commands
from cogs.utils import customhelp

''' 
- \U0001f1fe YES 
- \U0001f1f3 NO 
- \U0001f1e6 A 
- \U0000267f wheelchair
- \U0001f1f2 M 
- \U0001f1e9 D 
'''

'''
TODO:
- If u are already added to comp and change the reaction it doesn't update correctly and leaves the old sign on
the message when bot comes online'''

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
        self.log = logger

        # Load cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                # Comment to disable errorhandler module
                if name == 'errorhandler':
                    continue
                self.load_extension(f"cogs.{name}")

    async def blacklist_user(self, user_id):
        date = datetime.datetime.utcnow().date()
        self.blacklist.append(user_id)

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
        author_id = message.author.id

        if ctx.command is None:
            return

        # Allow admin commands through DMs
        if ctx.command.cog_name == 'Admin' and author_id == self.owner_id:
            await self.invoke(ctx)
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is None:
            return

        bucket = self.cd.get_bucket(message)
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
        retry_after = bucket.update_rate_limit(current)

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
