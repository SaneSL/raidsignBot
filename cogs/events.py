import discord

from discord.ext import commands, tasks
from utils.globalfunctions import clear_guild_from_db, clear_all_signs, null_category,\
    null_raid_channel, null_comp_channel, get_raid_channel_id
from utils.permissions import default_role_perms_commands, default_role_perms_comp_raid, bot_perms, bot_join_permissions


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.add_missing_stuff.start()

    # Remove transaction?
    @commands.command()
    async def add_reacted_signs(self, ctx):
        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                raids = await self.bot.pool.fetch('''
                SELECT id
                FROM raid
                WHERE guildid = $1''', ctx.guild.id)

                if raids is None:
                    await self.bot.pool.release(con)
                    return

                raid_channel_id = await get_raid_channel_id(self.bot.pool, ctx.guild.id)

                if raid_channel_id is None:
                    await self.bot.pool.release(con)
                    return

                raid_channel = ctx.guild.get_channel(raid_channel_id)

                players = await con.fetch('''
                SELECT playerid, main, alt
                FROM membership
                WHERE guildid = $1''', ctx.guild.id)

                player_dict = {}

                for player in players:
                    player_dict[player['playerid']] = (player['main'], player['alt'])

                for raid in raids:
                    msg = await raid_channel.fetch_message(raid['id'])
                    reactions = msg.reactions
                    for reaction in reactions:
                        if reaction.emoji in {'\U0001f1fe', '\U0001f1f3', '\U0001f1e6'}:
                            async for user in reaction.users():
                                tuple_value = player_dict.get(user.id)

                                if tuple_value is None:
                                    continue

                                elif reaction.emoji == '\U0001f1fe':
                                    playerclass = tuple_value[0]

                                elif reaction.emoji == '\U0001f1f3':
                                    playerclass = 'Declined'

                                else:
                                    playerclass = tuple_value[1]

                                if playerclass is None:
                                    continue

                                await con.execute('''
                                INSERT INTO sign (playerid, raidid, playerclass)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (playerid, raidid) DO UPDATE
                                SET playerclass = $3''', user.id, raid['id'], playerclass)

        await self.bot.pool.release(con)

    async def add_missing_channels(self):
        all_guilds = await self.bot.pool.fetch('''
        SELECT id, raidchannel, compchannel, category, autosignrole
        FROM guild''')

        for guild_info in all_guilds:
            guild = self.bot.get_guild(guild_info['id'])
            if guild is None:
                continue

            if guild_info['raidchannel'] is not None:
                c = guild.get_channel(guild_info['raidchannel'])
                if c is None:
                    raid_channel = await guild.create_text_channel('Raids')
                    await self.bot.pool.execute('''
                    UPDATE guild
                    SET raidchannel = $1
                    WHERE id = $2''', raid_channel.id, guild_info['id'])

            if guild_info['compchannel'] is not None:
                c = guild.get_channel(guild_info['compchannel'])
                if c is None:
                    comp_channel = await guild.create_text_channel("Comps")
                    await self.bot.pool.execute('''
                    UPDATE guild
                    SET compchannel = $1
                    WHERE id = $2''', comp_channel.id, guild_info['id'])

            if guild_info['category'] is not None:
                c = guild.get_channel(guild_info['category'])
                if c is None:
                    category = await guild.create_category('Raidsign')
                    await self.bot.pool.execute('''
                    UPDATE guild
                    SET category = $1
                    WHERE id = $2''', category.id, guild_info['id'])

            if guild_info['autosignrole'] is not None:
                guild_role = guild.get_role(guild_info['autosignrole'])
                if guild_role is None:
                    role = await guild.create_role(name='AutoSign', reason="Bot created AutoSign role")
                    await self.bot.pool.execute('''
                    UPDATE guild
                    SET autosignrole = $1
                    WHERE id = $2''', role.id, guild_info['id'])

    async def clear_ghost_guilds_db(self):
        guilds = await self.bot.pool.fetch('''
                SELECT id
                FROM guild''')

        db_guilds = []
        bot_guilds = self.bot.guilds

        for guild in guilds:
            db_guilds.append(guild['id'])

        bot_guild_ids = []

        for guild in bot_guilds:
            bot_guild_ids.append(guild.id)

        clear_list = [x for x in db_guilds if x not in bot_guild_ids]

        if clear_list:
            await clear_guild_from_db(self.bot.pool, clear_list)

    async def addguildtopool(self, guild):
        guild_id = guild.id

        await self.bot.pool.execute('''
        INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING''', guild_id)

    async def setup_channels(self, guild):

        guild_cog = self.bot.get_cog('Guild')

        overwrites_bot_commands = {guild.default_role: default_role_perms_commands,
                                   guild.me: bot_perms}

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        category_name = "Raidsign"
        category = await guild.create_category(category_name)  # need overwrites?
        await guild.create_text_channel('Bot-commands', overwrites=overwrites_bot_commands, category=category)
        raid_channel = await guild.create_text_channel('Raids', overwrites=overwrites_raids_comps, category=category)
        comp_channel = await guild.create_text_channel('Comps', overwrites=overwrites_raids_comps, category=category)

        await guild_cog.category(guild.id, category.id)
        await guild_cog.raidchannel(guild.id, raid_channel.id)
        await guild_cog.compchannel(guild.id, comp_channel.id)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready.')
        bot_id = self.bot.user.id

        for guild in self.bot.guilds:
            bot_member = guild.get_member(bot_id)
            if bot_member is None:
                continue
            guild_perms = [pair for pair in bot_member.guild_permissions]
            if guild_perms != bot_join_permissions:
                await guild.leave()

        for guild in self.bot.guilds:
            await self.addguildtopool(guild)

        await self.clear_ghost_guilds_db()
        await self.add_missing_channels()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.addguildtopool(guild)
        await self.setup_channels(guild)

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        guild_id = [guild.id]
        await clear_guild_from_db(self.bot.pool, guild_id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        channel_id = channel.id

        guild_info = await self.bot.pool.fetchrow('''
        SELECT raidchannel, compchannel, category
        FROM guild
        WHERE id = $1''', guild.id)

        if guild_info is None:
            return

        guild_cog = self.bot.get_cog('Guild')

        raid_channel_id = guild_info['raidchannel']
        comp_channel_id = guild_info['compchannel']
        category_id = guild_info['category']

        if channel_id in {raid_channel_id, comp_channel_id, category_id}:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target.id in {raid_channel_id, comp_channel_id, category_id}:
                    await entry.user.send("You just deleted important channel")
                    pass

            if channel_id == raid_channel_id:
                # await clear_all_signs(self.bot.pool, guild.id)
                # await null_raid_channel(self.bot.pool, guild.id)
                await guild_cog.addraidchannel(guild, raid_channel_id, category_id)
            elif channel_id == comp_channel_id:
                # Tag the user who deleted the channel and ask them to create new channel with x command
                # await null_comp_channel(self.bot.pool, guild.id)
                await guild_cog.addcompchannel(guild, comp_channel_id, category_id)
            elif channel_id == category_id:
                # await null_category(self.bot.pool, guild.id)
                await guild_cog.addcategory(guild, category_id, raid_channel_id, comp_channel_id)

    @commands.command()
    async def addguild(self, ctx):
        await self.addguildtopool(ctx.guild)


def setup(bot):
    bot.add_cog(Botevents(bot))
