from discord.ext import commands
from .utils.globalfunctions import get_main, get_alt, sign_player


class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Event triggered when user reacts to a message. Signs player to raid with data based emoji

        Parameters
        ----------
        payload
        """

        # Don't accept DMs
        if not payload.guild_id:
            return

        # Ignore Bot
        if payload.user_id == self.bot.user.id:
            return

        if payload.emoji.name not in {'\U0001f1f2', '\U0001f1e9', '\U0001f1e6'}:
            return

        raid_id = payload.message_id
        guild = self.bot.get_guild(payload.guild_id)
        guild_id = guild.id
        player_id = payload.user_id

        raid_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT id
        FROM raid
        WHERE id = $1 AND guildid = $2 LIMIT 1)''', raid_id, guild_id)

        # No raid found
        if raid_exists is False:
            return

        if payload.emoji.name == '\U0001f1f2':
            row = await get_main(self.bot.pool, guild_id, player_id)

            if row is None:
                return
            else:
                playerclass = row['main']
                spec = row['mainspec']

        elif payload.emoji.name == '\U0001f1e9':
            playerclass = "Declined"
            spec = None

        else:
            row = await get_alt(self.bot.pool, guild_id, player_id)

            if row is None:
                return
            else:
                playerclass = row['alt']
                spec = row['altspec']

        await sign_player(self.bot.pool, player_id, raid_id, playerclass, spec)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Event triggered when user removes a reaction. Removes player from raid

        Parameters
        ----------
        payload
        """

        # Don't accept DMs
        if not payload.guild_id:
            return

        # Ignore bot
        if payload.user_id == self.bot.user.id:
            return

        raid_id = payload.message_id
        guild = self.bot.get_guild(payload.guild_id)
        guild_id = guild.id

        raid_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE id = $1 AND guildid = $2 LIMIT 1)''', raid_id, guild_id)

        # No raid found
        if raid_exists is False:
            return

        player_id = payload.user_id

        await self.bot.pool.execute('''
        DELETE FROM sign
        WHERE playerid = $1 AND raidid = $2''', player_id, raid_id)


def setup(bot):
    bot.add_cog(React(bot))
