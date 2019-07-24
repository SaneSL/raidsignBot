CREATE TABLE IF NOT EXISTS guild(
id BIGINT PRIMARY KEY,
raidchannel BIGINT,
compchannel BIGINT,
category BIGINT,
autosignrole BIGINT);

CREATE TABLE IF NOT EXISTS player(
id BIGINT PRIMARY KEY );

CREATE TABLE IF NOT EXISTS membership(
guildid BIGINT,
playerid BIGINT,
main TEXT,
alt TEXT,
PRIMARY KEY (guildid, playerid),
FOREIGN KEY (guildid) REFERENCES guild (id),
FOREIGN KEY (playerid) REFERENCES player (id));

CREATE TABLE IF NOT EXISTS raid(
id BIGINT PRIMARY KEY,
guildid BIGINT,
name TEXT,
main BOOLEAN DEFAULT FALSE,
cleartime SMALLINT,
FOREIGN KEY (guildid) REFERENCES guild (id));

CREATE TABLE IF NOT EXISTS sign(
playerid BIGINT,
raidid BIGINT,
playerclass TEXT,
PRIMARY KEY (playerid, raidid),
FOREIGN KEY (playerid) REFERENCES player (id),
FOREIGN KEY (raidid) REFERENCES raid (id));