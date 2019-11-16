import discord

from .utils.globalfunctions import is_valid_class, is_valid_combo
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
    @commands.command(description="Sets user's main. Use specific class and spec!", brief='{"examples":["addmain rogue combat"], "cd":"60"}')
    async def addmain(self, ctx, playerclass, *, spec):
        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        # Replace quotes just incase
        spec = spec.replace('"', "")

        await self.addself(player_id)

        playerclass = playerclass.title()
        spec = spec.lower()

        if not await is_valid_combo(playerclass, spec):
            await ctx.send("Invalid class name or spec... try again.")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, main, mainspec)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET main = $3, mainspec = $4
        ''', guild_id, player_id, playerclass, spec)

        await ctx.send(f"{author.mention} set main to {spec} {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Sets user's alt. Use specific class and spec!", brief='{"examples":["addalt rogue combat"], "cd":"60"}')
    async def addalt(self, ctx, playerclass, *, spec):
        author = ctx.message.author
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        # Replace quotes just incase
        spec = spec.replace('"', "")

        await self.addself(player_id)

        playerclass = playerclass.title()
        spec = spec.lower()

        if not await is_valid_combo(playerclass, spec):
            await ctx.send("Invalid class name or spec... try again.")
            return

        await self.bot.pool.execute('''
        INSERT INTO membership (guildid, playerid, alt, altspec)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET alt = $3, altspec = $4
        ''', guild_id, player_id, playerclass, spec)

        await ctx.send(f"{author.mention} set alt to {spec} {playerclass}")

    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.command(description="Gives the user autosign role, which makes the user sign automatically to all 'main' "
                                  "raids with main.", brief='{"examples":[], "cd":"60"}')
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        playerclass_exists = await self.bot.pool.fetchval('''
        SELECT EXISTS (SELECT main, mainspec FROM membership
        WHERE guildid = $1 AND playerid = $2 LIMIT 1)''', guild.id, member.id)

        if playerclass_exists is False:
            await ctx.send(f"Autosign failed. {member.mention} add your main with `!addmain <classname> <spec>` "
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
