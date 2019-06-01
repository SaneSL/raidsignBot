import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidsigning import Signing


class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.signing = Signing(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return

        if payload.message_id != 583951712625098752:
            return

        if payload.user_id is self.bot.user:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = discord.Object(583964043094786048)

        await member.add_roles(role, reason='Auto sign role')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return

        if payload.message_id != 583951712625098752:
            return

        if payload.user_id is self.bot.user:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = discord.Object(583964043094786048)

        await member.remove_roles(role, reason="Remove auto sign role")

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