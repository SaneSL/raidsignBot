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


async def get_raidid(pool, guild_id, raidname):
    raid_id = await pool.fetchval('''
    SELECT raid.id
    FROM raid
    WHERE guildid = $1 AND name = $2 ''', guild_id, raidname)

    return raid_id


async def get_main(pool, guild_id, player_id):
    playerclass = await pool.fetchval('''
    SELECT main
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return playerclass


async def get_alt(pool, guild_id, player_id):
    playerclass = await pool.fetchval('''
    SELECT alt
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return playerclass


async def sign_player(pool, player_id, raid_id, playerclass):
    try:
        await pool.execute('''
        INSERT INTO sign (playerid, raidid, playerclass)
        VALUES ($1, $2, $3)''', player_id, raid_id, playerclass)

    except asyncpg.ForeignKeyViolationError:
        return False

    except asyncpg.UniqueViolationError:
        await pool.execute('''
        UPDATE sign
        SET playerclass = $1
        WHERE playerid = $2 AND raidid = $3''', playerclass, player_id, raid_id)


async def get_raid_channel_id(pool, guild_id):
    channel_id = await pool.fetchval('''
    SELECT raidchannel
    FROM guild
    WHERE id = $1''', guild_id)

    return channel_id


async def get_comp_channel_id(pool, guild_id):
    channel_id = await pool.fetchval('''
    SELECT compchannel
    FROM guild
    WHERE id = $1''', guild_id)

    return channel_id


async def get_category_id(pool, guild_id):
    category = await pool.fetchval('''
    SELECT category
    FROM guild
    WHERE id = $1''', guild_id)

    return category


async def clear_all_signs(pool, guild_id):
    await pool.execute('''
    DELETE
    FROM sign
    WHERE sign.raidid = (SELECT id FROM raid WHERE raid.guildid = $1)''', guild_id)

    await pool.execute('''
    DELETE 
    FROM raid
    WHERE guildid = $1''', guild_id)


async def null_comp_channel(pool, guild_id):
    await pool.execute('''
    UPDATE guild
    SET compchannel = NULL
    WHERE id = $1''', guild_id)


async def null_raid_channel(pool, guild_id):
    await pool.execute('''
    UPDATE guild
    SET raidchannel = NULL
    WHERE id = $1''', guild_id)


async def null_category(pool, guild_id):
    await pool.execute('''
    UPDATE guild
    SET category = NULL
    WHERE id = $1''', guild_id)


async def clear_guild_from_db(pool, guild_ids):
    async with pool.acquire() as con:
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

    await pool.release(con)