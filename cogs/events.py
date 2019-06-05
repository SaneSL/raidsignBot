import discord
import asyncio
import asyncpg

from discord.ext import commands


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def addguildtodb(self, guild):
        guild_id = guild.id

        await self.bot.db.execute('''
        INSERT INTO guild VALUES ($1) ON CONFLICT DO NOTHING''', guild_id)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready.')
        for guild in self.bot.guilds:
            await self.addguildtodb(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.addguildtodb(guild)

    @commands.command()
    async def addguild(self, ctx):
        await self.addguildtodb(ctx.guild)


def setup(bot):
    bot.add_cog(Botevents(bot))
