import discord

from utils.globalfunctions import is_valid_class
from discord.ext import commands


class Membership(commands.Cog, name='Player'):
    """
    These commands allow user to store their preferred main/alt class and add get autosign role.
    """
    def __init__(self, bot):
        self.bot = bot

    async def addself(self, player_id):
        await self.bot.pool.execute('''
        INSERT INTO player (id)
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @staticmethod
    async def addautosign(guild):
        await guild.create_role(name='autosign', reason="Bot created AutoSign role")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Adds user's main class to db.", brief='{"examples":["addmain rogue"], "cd":"60"}')
    async def addmain(self, ctx, playerclass):
        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("You prolly typed the class name wrong... try again")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, main)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET main = $3
        ''', guild_id, player_id, playerclass)

        await ctx.send(f"{author.mention} set main to {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Adds user's alt class to db.", brief='{"examples":["addalt rogue"], "cd":"60"}')
    async def addalt(self, ctx, playerclass):
        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("You prolly typed the class name wrong... try again")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, alt)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET alt = $3
        ''', guild_id, player_id, playerclass)

        await ctx.send(f"{author.mention} set alt to {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Gives the user autosign role, which makes the user sign automatically to all 'main'"
                                  "raids.", brief='{"examples":[], "cd":"60"}')
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        playerclass_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT main FROM membership
        WHERE guildid = $1 AND playerid = $2 LIMIT 1)''', guild.id, member.id)

        if playerclass_exists is False:
            await ctx.send(f"Autosign failed. {member.mention} add your main with `!addmain <classname> "
                           f"and try again`")
            return

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = TRUE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        role = discord.utils.get(guild.roles, name='autosign')

        if role is None:
            await ctx.send(f"{member.mention} added autosign! You might not have the role if it "
                           f"has been deleted or renamed.")
        else:
            try:
                await member.add_roles(role, reason='Added autosign role')
                await ctx.send(f"{member.mention} added autosign!")

            except discord.Forbidden:
                await ctx.send(f"{member.mention} removed autosign!\n"
                               f"Role hierarchy error: Role is higher than bot's role "
                               f"so it couldn't be added to the user.")

            except discord.HTTPException:
                await ctx.send(f"{member.mention} added autosign! Failed to remove role. Reason unknown.")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Removes autosign.", brief='{"examples":[], "cd":"60"}')
    async def autosignoff(self, ctx):
        guild = ctx.guild
        member = ctx.author

        await self.bot.pool.execute('''
        UPDATE membership
        SET autosign = FALSE
        WHERE playerid = $1 AND guildid = $2''', member.id, guild.id)

        role = discord.utils.get(guild.roles, name='autosign')

        if role is None:
            await ctx.send(f"{member.mention} removed autosign! You might still have the role if it"
                           f"has been deleted or renamed.")
        else:
            try:
                await member.remove_roles(role, reason='Removed autosign role')
                await ctx.send(f"{member.mention} removed autosign!")

            except discord.Forbidden:
                await ctx.send(f"{member.mention} removed autosign!\n"
                               f"Role hierarchy error: Role is higher than bot's role "
                               f"so it couldn't be removed from the user.")

            except discord.HTTPException:
                await ctx.send(f"{member.mention} removed autosign! Failed to remove role. Reason unknown.")


def setup(bot):
    bot.add_cog(Membership(bot))
