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
- If category is deleted and new one is made move channels under that category
- Add new check to on_channel_delete

- \U0001f1f3 NO
- \U0001f1fe YES
- \U0001f1e6 A
- \U0000267f wheelchair

- TO TEST:
    - clear_guild_from_db
    - setup_channels with on_ready
'''


def get_cfg():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('config.json') as json_data_file:
        cfg = json.load(json_data_file)
    return cfg


async def do_setup(cfg):
    db = await asyncpg.create_pool(database=cfg["pg_db"], user=cfg["pg_user"], password=cfg["pg_pw"])

    # await bot.db.execute('''DROP TABLE IF EXISTS testitable''')

    fd = open("setup.sql", "r")
    file = fd.read()
    fd.close()

    sqlcommands = file.split(';')
    sqlcommands = list(filter(None, sqlcommands))

    for command in sqlcommands:
        await db.execute(command)

    return db


class RaidSign(commands.Bot):
    def __init__(self, **kwargs):
        self._cd = commands.CooldownMapping.from_cooldown(2, 15, commands.BucketType.member)
        super().__init__(**kwargs)

        self.remove_command('help')

        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                self.load_extension(f"cogs.{name}")

    async def bot_check(self, ctx):
        bucket = self._cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            print("Failed")
            return False
        # you're not rate limited
        return True


def run_bot():
    cfg = get_cfg()
    bot = RaidSign(command_prefix=cfg['prefix'])
    bot.db = asyncio.get_event_loop().run_until_complete(do_setup(cfg))
    bot.run(cfg['token'])


run_bot()
