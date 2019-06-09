import discord
import asyncio
import asyncpg

from discord.ext import commands


class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Don't accept DMs
        if not payload.guild_id:
            return

        # Ignore Bot
        if payload.user_id == self.bot.user.id:
            return

        raid_id = payload.message_id
        guild = self.bot.get_guild(payload.guild_id)
        guild_id = guild.id
        player_id = payload.user_id
        member = guild.get_member(payload.user_id)

        row = await self.bot.db.fetchrow('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE id = $1 AND guildid = $2 LIMIT 1)''', raid_id, guild_id)

        # No raid found
        if row['exists'] is False:
            return

        if payload.emoji.name == '\U0001f1fe':
            print("XD")
            row = await self.bot.db.fetchrow('''
            SELECT playerclass
            FROM membership
            WHERE playerid = $1''', player_id)

            if row is None:
                return

            await self.bot.db.execute('''
            INSERT INTO sign VALUES ($1, $2, $3)
            ON CONFLICT (playerid, raidid) DO UPDATE
            set playerclass = $3''', player_id, raid_id, row['playerclass'])

        if payload.emoji.name == '\U0001f1f3':
            await self.bot.db.execute('''
            INSERT INTO sign VALUES ($1, $2, $3)
            ON CONFLICT (playerid, raidid) DO UPDATE
            set playerclass = $3''', player_id, raid_id, "Declined")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        # Don't accept DMs
        if not payload.guild_id:
            return

        # Ignore bot
        if payload.user_id == self.bot.user.id:
            return

        raid_id = payload.message_id
        guild = self.bot.get_guild(payload.guild_id)
        guild_id = guild.id

        row = await self.bot.db.fetchrow('''
        SELECT EXISTS (SELECT id FROM raid
        WHERE id = $1 AND guildid = $2 LIMIT 1)''', raid_id, guild_id)

        # No raid found
        if row['exists'] is False:
            return

        player_id = payload.user_id

        member = guild.get_member(payload.user_id)

        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE playerid = $1 AND raidid = $2''', player_id, raid_id)

    @commands.command()
    async def removereact(self, ctx, msg_id):
        msg_id = int(msg_id)
        message = await self.bot.get_channel(579744448687243266).fetch_message(msg_id)

        await message.clear_reactions()

        await message.add_reaction('\U0000267f')

        #embed = message.embeds[0]
        #embed.title = "Kendo"

        #await message.edit(embed=embed)


def setup(bot):
    bot.add_cog(React(bot))
