import asyncpg

from discord.ext import commands


player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Paladin", "Priest",
                  "Shaman", "Druid", "Declined"]

class_spec = {"Warrior": ("arms", "fury", "protection"),
              "Rogue": ("assassination", "combat", "subtlety"),
              "Hunter": ("beast mastery", "marksmanship", "survival"),
              "Warlock": ("affliction", "demonology", "destruction"),
              "Mage": ("arcane", "fire", "frost"),
              "Paladin": ("holy", "protection", "retribution"),
              "Priest": ("discipline", "holy", "shadow"),
              "Shaman": ("elemental", "enhancement", "restoration"),
              "Druid": ("moonkin", "feral combat", "restoration")}


async def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return name
    else:
        return None


async def is_valid_combo(name, spec):
    if name in player_classes and spec in class_spec[name]:
        return True
    else:
        return False


async def get_raidid(pool, guild_id, raidname):
    raid_id = await pool.fetchval('''
    SELECT raid.id
    FROM raid
    WHERE guildid = $1 AND name = $2 ''', guild_id, raidname)

    return raid_id


async def get_main(pool, guild_id, player_id):
    row = await pool.fetchrow('''
    SELECT main, mainspec
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return row


async def get_alt(pool, guild_id, player_id):
    row = await pool.fetchrow('''
    SELECT alt, altspec
    FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    return row


async def sign_player(pool, player_id, raid_id, playerclass, spec=None):
    try:
        await pool.execute('''
        INSERT INTO sign (playerid, raidid, playerclass, spec)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (playerid, raidid) DO UPDATE
        SET playerclass = $3, spec = $4''', player_id, raid_id, playerclass, spec)
        return True

    except asyncpg.ForeignKeyViolationError:
        return False


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


async def clear_guild_from_db(pool, guild_ids):
    async with pool.acquire() as con:
        for guild_id in guild_ids:
            await con.execute('''
            DELETE FROM guild
            WHERE id = $1''', guild_id)

            await con.execute('''
            DELETE FROM player
            WHERE NOT EXISTS(
                SELECT 1
                FROM membership
                WHERE membership.playerid = player.id)''')

    await pool.release(con)


async def clear_user_from_db(pool, guild_id, player_id):
    await pool.execute('''
    DELETE FROM membership
    WHERE guildid = $1 AND playerid = $2''', guild_id, player_id)

    await pool.execute('''
    DELETE FROM player
    WHERE id = $1 AND NOT EXISTS(
        SELECT 1
        FROM membership
        WHERE membership.playerid = $1)''', player_id)
