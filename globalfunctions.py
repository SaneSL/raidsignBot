

player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Priest",
                  "Shaman", "Druid", "Declined"]


async def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return name
    else:
        return None


async def get_level(db, playerid):
    playerid = int(playerid)

    level = await db.fetchval('''
    SELECT player.level
    FROM player
    WHERE player.id = $1''', playerid)

    return level


async def get_raidid(db, guild_id, raidname):
    raid_id = await db.fetchval('''
    SELECT raid.id
    FROM raid
    WHERE guildid = $1 AND name = $2 ''', guild_id, raidname)

    return raid_id


async def get_userid(members, name):
    for member in members:
        member_name = member.name + "#" + member.discriminator
        if member_name == name:
            return member.id

    return -1


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
    await db.execute('''
    INSERT INTO sign VALUES ($1, $2, $3)
    ON CONFLICT (playerid, raidid) DO UPDATE
    SET playerclass = $3''', player_id, raid_id, playerclass)