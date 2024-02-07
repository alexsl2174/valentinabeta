#!/bin/python3

import discord
from discord.ext import commands

from utils import database

class Admin(commands.Cog):
  """
  Admin utilities, like give/take coin/gem.
  """

  def __init__(self, bot):
    self.bot: commands.Bot = bot

  async def cog_check(self, ctx: commands.Context) -> bool:
    # has admin in the server
    return ctx.author.guild_permissions.administrator

  # on fail error
  async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
    # if its about the cog check
    if isinstance(error, commands.CheckFailure):
      coin_or_gem = "coin" if ctx.command.name in ["givecoin", "takecoin"] else "gem"

      await ctx.send(f"<:no:1178686922768519280> Nahhh, You need to be an admin to give or take {coin_or_gem}s")
    else:
      raise error

  async def amount_check(self, ctx, user, amount):
    if user.bot:
      await ctx.send(f"<:no:1178686922768519280> You can't give gems to a bot")
      return False

    if amount < 1:
      await ctx.send(f"<:no:1178686922768519280> Seriously?")
      return False

    return True

  # database add_money signature
  # def add_money(member, guild, coin, gem)

  @commands.hybrid_command()
  @commands.guild_only()
  async def givegem(self, ctx: commands.Context, user: discord.Member, amount: int):
    """give gems to a user"""
    if not await self.amount_check(ctx, user, amount):
      return

    database.add_money(user.id, ctx.guild.id, 0, amount * 10)
    await ctx.send(f"<:yes:1184312448912732180> {user.mention} you got {amount} gems, keep behaving like this.")

  @commands.hybrid_command()
  @commands.guild_only()
  async def takegem(self, ctx: commands.Context, user: discord.Member, amount: int):
    """take gems from a user"""
    if not await self.amount_check(ctx, user, amount):
      return

    database.add_money(user.id, ctx.guild.id, 0, -amount * 10)
    await ctx.send(f"<:yes:1184312448912732180> Don't cry {user.mention}, but {ctx.author.mention} has taken {amount} gems from you. You can earn it back.")

  @commands.hybrid_command()
  @commands.guild_only()
  async def givecoin(self, ctx: commands.Context, user: discord.Member, amount: int):
    """give coins to a user"""
    if not await self.amount_check(ctx, user, amount):
      return

    database.add_money(user.id, ctx.guild.id, amount, 0)
    await ctx.send(f"<:yes:1184312448912732180> Marvelous {ctx.author.mention} has given {user.mention} the honor of {amount} coins. Spend it wisely.")

  @commands.hybrid_command()
  @commands.guild_only()
  async def takecoin(self, ctx: commands.Context, user: discord.Member, amount: int):
    """take coins from a user"""
    if not await self.amount_check(ctx, user, amount):
      return

    database.add_money(user.id, ctx.guild.id, -amount, 0)
    await ctx.send(f"<:yes:1184312448912732180> Don't cry {user.mention}, but {ctx.author.mention} has taken {amount} coins from you. You can earn it back.")


async def setup(bot):
  await bot.add_cog(Admin(bot))
