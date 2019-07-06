import asyncpg

from discord.ext import commands


player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Paladin", "Priest",
                  "Shaman", "Druid", "Declined"]


async def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return name
    else:
        return None


async def get_raidid(db, guild_id, raidname):
    raid_id = await db.fetchval('''
    SELECT raid.id
    FROM raid
    WHERE guildid = $1 AND name = $2 ''', guild_id, raidname)

    return raid_id


async def get_main(db, guild_id, player_id):
    playerclass = await db.fetchval('''
    SELECT main
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return playerclass


async def get_alt(db, guild_id, player_id):
    playerclass = await db.fetchval('''
    SELECT alt
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return playerclass


async def sign_player(db, player_id, raid_id, playerclass):
    try:
        await db.execute('''
        INSERT INTO sign (playerid, raidid, playerclass)
        VALUES ($1, $2, $3)''', player_id, raid_id, playerclass)

    except asyncpg.ForeignKeyViolationError:
        return False

    except asyncpg.UniqueViolationError:
        await db.execute('''
        UPDATE sign
        SET playerclass = $1
        WHERE playerid = $2 AND raidid = $3''', playerclass, player_id, raid_id)


async def get_raid_channel_id(db, guild_id):
    channel = await db.fetchval('''
    SELECT raidchannel
    FROM guild
    WHERE id = $1''', guild_id)

    return channel


async def get_comp_channel_id(db, guild_id):
    channel = await db.fetchval('''
    SELECT compchannel
    FROM guild
    WHERE id = $1''', guild_id)

    return channel


async def clear_all_signs(db, guild_id):
    await db.execute('''
    DELETE
    FROM sign
    WHERE sign.raidid = (SELECT id FROM raid WHERE raid.guildid = $1)''', guild_id)

    await db.execute('''
    DELETE 
    FROM raid
    WHERE guildid = $1''', guild_id)


async def null_comp_channel(db, guild_id):
    await db.execute('''
    UPDATE guild
    SET compchannel = NULL
    WHERE id = $1''', guild_id)


async def remove_raid_channel(db, guild_id):
    await db.execute('''
    UPDATE guild
    SET raidchannel = NULL
    WHERE id = $1''', guild_id)


async def clear_guild_from_db(db, guild_ids):
    async with db.acquire() as con:
        async with con.transaction():
            for guild_id in guild_ids:
                await con.execute('''
                DELETE FROM membership
                WHERE guildid = $1''', guild_id)

                await con.execute('''
                DELETE FROM sign
                WHERE sign.raidid = (SELECT id FROM raid WHERE raid.guildid = $1)''', guild_id)

                await con.execute('''
                DELETE FROM raid
                WHERE guildid = $1''', guild_id)

                await con.execute('''
                DELETE FROM guild
                WHERE id = $1''', guild_id)


async def check_any_permission(ctx, perms, *, check=any):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    user_perms = ctx.author.guild_permissions

    return check(getattr(user_perms, name, None) == value for name, value in perms.items())


def has_any_permission(*, check=any, **perms):
    async def pred(ctx):
        return await check_any_permission(ctx, perms, check=check)
    return commands.check(pred)


