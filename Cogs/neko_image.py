#!/bin/python3
import discord
import nekos
from discord.ext import commands


class Neko(commands.Cog):
  """cute neko like hug/tickle/etc..."""
  def __init__(self, bot):
    self.bot = bot

  @commands.hybrid_command()
  @commands.guild_only()
  async def hug(self, ctx, member: discord.Member):
    """hug someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('hug')
    embed = discord.Embed(title=f"{ctx.author.display_name} hugs {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('hug')
      embed = discord.Embed(title=f"Miss Valentina hugs {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def tickle(self, ctx, member: discord.Member):
    """tickle someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('tickle')
    embed = discord.Embed(title=f"{ctx.author.display_name} tickles {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('tickle')
      embed = discord.Embed(title=f"Miss Valentina tickles {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  # xxx: POKE is not available in nekos anymore
  # @commands.hybrid_command()
  # @commands.guild_only()
  # async def poke(self, ctx, member: discord.Member):
  #   """poke someone"""
  #   if ctx.author.bot:
  #     return
  #   image_url = nekos.img('poke')
  #   embed = discord.Embed(title=f"{ctx.author.display_name}",
  #                         color=0xF2A2C0)
  #   embed.set_image(url=image_url)
  #   await ctx.send(embed=embed)
  #   if member.id == self.bot.user.id:
  #     image_url = nekos.img('poke')
  #     embed = discord.Embed(title=f"Miss Valentina pokes {ctx.author.display_name} back.", color=0xF2A2C0)
  #     embed.set_image(url=image_url)
  #     await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def slap(self, ctx, member: discord.Member):
    """slap someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('slap')
    embed = discord.Embed(title=f"{ctx.author.display_name} slaps {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('slap')
      embed = discord.Embed(title=f"Miss Valentina slaps {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def pat(self, ctx, member: discord.Member):
    """pat someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('pat')
    embed = discord.Embed(title=f"{ctx.author.display_name} pats {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('pat')
      embed = discord.Embed(title=f"Miss Valentina pats {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def kiss(self, ctx, member: discord.Member):
    """kiss someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('kiss')
    embed = discord.Embed(title=f"{ctx.author.display_name} kisses {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('kiss')
      embed = discord.Embed(title=f"Miss Valentina kisses {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def spank(self, ctx, member: discord.Member):
    """spank someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('spank')
    embed = discord.Embed(title=f"{ctx.author.display_name} spanks {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('spank')
      embed = discord.Embed(title=f"Miss Valentina spanks {ctx.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def cuddle(self, ctx, member: discord.Member):
    """cuddle someone"""
    if ctx.author.bot:
      return
    image_url = nekos.img('cuddle')
    embed = discord.Embed(title=f"{ctx.author.display_name} cuddles {member.display_name}",
                          color=0xF2A2C0)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
    if member.id == self.bot.user.id:
      image_url = nekos.img('cuddle')
      embed = discord.Embed(title=f"Miss Valentina cuddles {ctx.author.display_name} back.", color=0xF2A2C0)
      embed.set_image(url=image_url)
      await ctx.reply(embed=embed)


async def setup(bot):
  await bot.add_cog(Neko(bot))
