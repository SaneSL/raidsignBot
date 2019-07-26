import discord

from discord.ext import commands
from utils.globalfunctions import clear_guild_from_db, get_raid_channel_id, clear_user_from_db
from utils.permissions import default_role_perms_commands, default_role_perms_comp_raid, bot_perms, \
    bot_join_permissions


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_embed = discord.Embed(
            title="Raidsign bot",
            description="Some info on how to use the bot.",
            colour=discord.Colour.blurple()
        )

    # Remove transaction?
    # @commands.command()
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
                        if reaction.emoji in {'\U0001f1f2', '\U0001f1e9', '\U0001f1e6'}:
                            async for user in reaction.users():
                                tuple_value = player_dict.get(user.id)

                                if tuple_value is None:
                                    continue

                                elif reaction.emoji == '\U0001f1f2':
                                    playerclass = tuple_value[0]

                                elif reaction.emoji == '\U0001f1e9':
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
        guild_cog = self.bot.get_cog('Server')
        member_cog = self.bot.get_cog('Player')
        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT id, raidchannel, compchannel, category, autosignrole
                FROM guild'''):
                    guild = self.bot.get_guild(record['id'])
                    if guild is None:
                        continue

                    await guild_cog.addcategory(con, guild, record['category'], record['raidchannel'],
                                                record['compchannel'])

                    if record['autosignrole'] is not None:
                        guild_role = guild.get_role(record['autosignrole'])
                        if guild_role is None:
                            await member_cog.addautosign(guild, con)
                    else:
                        await member_cog.addautosign(guild, con)

        await self.bot.pool.release(con)

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

    async def addguildtodb(self, guild):
        guild_id = guild.id

        await self.bot.pool.execute('''
        INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING''', guild_id)

    async def setup_channels_on_join(self, guild):

        overwrites_bot_commands = {guild.default_role: default_role_perms_commands,
                                   guild.me: bot_perms}

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        topic_c = "This channel displays all raids and their comps. Updated every 20 mins."
        topic_r = "This channel displays all available raids."
        topic_bc = "You can use bot-commands here or any other channel. If you already have a channel for " \
                   "this purpose or don't want to use this channel, feel free to delete it."

        category_name = "Raidsign"
        category = await guild.create_category(category_name)  # need overwrites?
        cmd_channel = await guild.create_text_channel('bot-commands', overwrites=overwrites_bot_commands
                                                      , category=category, topic=topic_bc)
        raid_channel = await guild.create_text_channel('raids', overwrites=overwrites_raids_comps, category=category,
                                                       topic=topic_r)
        comp_channel = await guild.create_text_channel('comps', overwrites=overwrites_raids_comps, category=category,
                                                       topic=topic_c)

        await self.bot.pool.execute('''
        UPDATE guild
        SET raidchannel = $1,
            compchannel = $2,
            category = $3
        WHERE id = $4''', raid_channel.id, comp_channel.id, category.id, guild.id)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready.')
        bot_id = self.bot.user.id

        perms = discord.Permissions(permissions=0)
        perms.update(**bot_join_permissions)

        # What is this bot_member stuff
        for guild in self.bot.guilds:
            bot_member = guild.get_member(bot_id)
            if bot_member is None:
                continue

            guild_perms = bot_member.guild_permissions

            if guild_perms < perms:
                await guild.leave()
            else:
                await self.addguildtodb(guild)

        await self.clear_ghost_guilds_db()
        await self.add_missing_channels()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        bot_id = self.bot.user.id
        bot_member = guild.get_member(bot_id)

        perms = discord.Permissions(permissions=0)
        perms.update(**bot_join_permissions)

        guild_perms = bot_member.guild_permissions

        if guild_perms < perms:
            await guild.leave()
        else:
            await self.addguildtodb(guild)
            await self.setup_channels_on_join(guild)


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_id = [guild.id]
        await clear_guild_from_db(self.bot.pool, guild_id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        player_id = member.id

        await clear_user_from_db(self.bot.pool, guild_id, player_id)


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

        guild_cog = self.bot.get_cog('Server')

        raid_channel_id = guild_info['raidchannel']
        comp_channel_id = guild_info['compchannel']
        category_id = guild_info['category']

        if channel_id in {raid_channel_id, comp_channel_id, category_id}:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target.id in {raid_channel_id, comp_channel_id, category_id}:
                    await entry.user.send("You just deleted important channel")
                    pass

            if channel_id == raid_channel_id:
                await guild_cog.addraidchannel(guild, raid_channel_id, category_id)
            elif channel_id == comp_channel_id:
                await guild_cog.addcompchannel(guild, comp_channel_id, category_id)
            elif channel_id == category_id:
                await guild_cog.addcategory(guild, category_id, raid_channel_id, comp_channel_id)


def setup(bot):
    bot.add_cog(Botevents(bot))
