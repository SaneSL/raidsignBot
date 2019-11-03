import discord

from discord.ext import commands
from .utils.globalfunctions import clear_guild_from_db, clear_user_from_db
from .utils.permissions import default_role_perms_commands, default_role_perms_comp_raid, bot_perms, \
    bot_join_permissions


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_embed = discord.Embed(
            title="Raidsign bot",
            description="Some info on how to use the bot.",
            colour=discord.Colour.blurple()
        )

    async def add_reacted_signs(self):
        async with self.bot.pool.acquire() as con:
            for guild in self.bot.guilds:
                guild_id = guild.id

                raids = await self.bot.pool.fetch('''
                SELECT id
                FROM raid
                WHERE guildid = $1''', guild_id)

                if raids is None:
                    continue

                raid_channel_id = await con.fetchval('''
                SELECT raidchannel
                FROM guild
                WHERE id = $1''', guild_id)

                if raid_channel_id is None:
                    continue

                raid_channel = guild.get_channel(raid_channel_id)

                if raid_channel is None:
                    continue

                players = await con.fetch('''
                SELECT playerid, main, mainspec, alt, altspec
                FROM membership
                WHERE guildid = $1''', guild_id)

                player_dict = {}

                for player in players:
                    player_dict[player['playerid']] = (player['main'], player['alt'], player['mainspec'],
                                                       player['altspec'])

                for raid in raids:
                    try:
                        msg = await raid_channel.fetch_message(raid['id'])
                    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
                        continue
                    reactions = msg.reactions
                    for reaction in reactions:
                        if reaction.emoji in {'\U0001f1f2', '\U0001f1e9', '\U0001f1e6'}:
                            async for user in reaction.users():
                                player_tuple = player_dict.get(user.id, None)

                                if player_tuple is None:
                                    continue

                                elif reaction.emoji == '\U0001f1f2':
                                    playerclass = player_tuple[0]
                                    spec = player_tuple[2]

                                elif reaction.emoji == '\U0001f1e9':
                                    playerclass = 'Declined'
                                    spec = None

                                else:
                                    playerclass = player_tuple[1]
                                    spec = player_tuple[3]

                                if playerclass is None:
                                    continue

                                # No upsert due to possibility of many reactions
                                await con.execute('''
                                INSERT INTO sign (playerid, raidid, playerclass, spec)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (playerid, raidid) DO NOTHING''', user.id, raid['id'], playerclass, spec)

        await self.bot.pool.release(con)

    async def add_missing_channels(self):
        guild_cog = self.bot.get_cog('Server')
        member_cog = self.bot.get_cog('Player')
        async with self.bot.pool.acquire() as con:
            async with con.transaction():
                async for record in con.cursor('''
                SELECT id, raidchannel, compchannel, category
                FROM guild'''):
                    guild = self.bot.get_guild(record['id'])
                    if guild is None:
                        continue

                    await guild_cog.addcategory(con, guild, record['category'], record['raidchannel'],
                                                record['compchannel'])

                    role = discord.utils.get(guild.roles, name='autosign')

                    if role is None:
                        await member_cog.addautosign(guild)
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

        join_message = self.get_join_msg()

        msg = await cmd_channel.send(embed=join_message)
        misc_cog = self.bot.get_cog('Misc')
        ctx = await self.bot.get_context(msg)

        await ctx.invoke(misc_cog.howtouse)

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
            elif guild.owner.id == bot_id:
                await guild.leave()
            else:
                await self.addguildtodb(guild)

        await self.clear_ghost_guilds_db()
        await self.add_reacted_signs()
        await self.add_missing_channels()

        game = discord.Game("!whatsnew")
        await self.bot.change_presence(activity=game)

    @staticmethod
    def get_join_msg():
        join_message = discord.Embed(
            title="Raidsign bot",
            colour=discord.Colour.dark_teal()
        )
        join_message.add_field(name='Useful commands', value="`!help` for general help and list of commands.\n"
                                                             "`!howtouse`\n"
                                                             "`!botinfo` for information on bot.")

        return join_message

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


def setup(bot):
    bot.add_cog(Botevents(bot))
