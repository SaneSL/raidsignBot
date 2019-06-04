

player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Priest",
                  "Shaman", "Druid", "Declined"]


async def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return True, name
    else:
        return False, name


async def getlevel(db, playerid):
    playerid = int(playerid)

    row = await db.fetchrow('''
    SELECT player.level
    FROM player
    WHERE player.id = $1''', playerid)

    return row


async def getraidid(db, guild_id, raidname):
    row = await db.fetchrow('''
    SELECT raid.id
    FROM raid
    WHERE guildid = $1 AND name = $2 ''', guild_id, raidname)

    return row
