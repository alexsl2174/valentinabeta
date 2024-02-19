#!/bin/python3
import asyncio
import random

from utils import database, relationship
import discord
from discord.ext import commands


def custom_ruin_cooldown(message):
  cooldown_minutes = int(database.get_config('ruin_cooldown', message.guild.id)[0]) or 60
  return commands.Cooldown(1, 1 * cooldown_minutes * 60)


class Games(commands.Cog):
  """special games to play and more"""

  def __init__(self, bot):
    self.bot = bot

  def ban_check(self, author, member):
    ban_data = database.is_botban(author.id)
    if ban_data is not None:
      embed = discord.Embed(title='Bot ban',
                            description=f"{author.mention} you are banned from using {self.bot.user.mention} till <t:{ban_data[1]}:F>",
                            color=0xF2A2C0)
      return embed
    elif database.is_botban(member.id) is not None:
      embed = discord.Embed(title='Bot ban',
                            description=f"{member.mention} is banned from using {self.bot.user.mention}.",
                            color=0xF2A2C0)
      return embed

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author.bot:
      if message.author.id != 302050872383242240:  # user ID of Disboard bot
        return
      else:
        for embed in message.embeds:
          try:
            if "https://disboard.org/images/bot-command-image-bump.png" == embed.to_dict()['image']['url']:
              user_id = int(embed.to_dict()['description'][2:20].replace('>', ''))
              if database.is_botban(user_id) is not None:
                return
              coins_to_add = 100 + random.randint(0, 50)
              database.add_money(user_id, message.guild.id, coins_to_add, 0)
              embed = discord.Embed(
                description=f"<@{user_id}> received {coins_to_add} <:coin:1178687013583585343> for Bumping the server.",
                color=0xF2A2C0)
              await message.channel.send(embed=embed)
              return
          except Exception:
            return

    if random.random() < 0.1 and database.is_botban(message.author.id) is None:
      coins_to_add = 3
      database.add_money(message.author.id, message.guild.id, coins_to_add, 0)

    try:
      data = database.get_config_raw('counting', message.guild.id).split(
        '_')  # [number, channel, member, message, count_length]
    except AttributeError:
      return
    if message.channel.id != int(data[1]):
      return

    try:
      count = int(message.content)
    except ValueError:
      if message.content.lower() == '/ruin':  # string is passed
        return
      else:
        # await message.delete()
        return

    number = int(data[0])
    if number < 0:
      if (-1 * number) == count:
        embed = discord.Embed(
          description=f"{message.author.mention} you guessed the correct number and you earned 30 <:coin:1178687013583585343>",
          color=0xF2A2C0)
        await message.reply(embed=embed)
        if database.is_botban(message.author.id) is None:
          database.add_money(message.author.id, message.guild.id, 30, 0)
        data[0] = str(-1 * number + 1)
        data[2] = str(message.author.id)
        data[3] = str(message.id)
        data[4] = '1'
        database.insert_config('counting', message.guild.id, '_'.join(data))
        await message.add_reaction('<:coin:1178687013583585343>')
      else:
        if count > number * -1:
          hint = f"Next number is {len(str(number * -1))} digit number and less than {count}"
        else:
          hint = f"Next number is {len(str(number * -1))} digit number and greater than {count}"
        embed = discord.Embed(title='Hint', description=hint, color=0xF2A2C0)
        await message.channel.send(embed=embed)

    else:
      if message.author.id == int(data[2]):
        await message.delete()
        m = await message.channel.send(f"{message.author.mention} you can't continues wait for someone else.")
        await asyncio.sleep(5)
        await m.delete()
      elif count == number:
        if database.is_botban(message.author.id) is None:
          database.add_money(message.author.id, message.guild.id, 1, 0)
        data[0] = str(number + 1)
        data[2] = str(message.author.id)
        data[3] = str(message.id)
        data[4] = str(int(data[4]) + 1)
        database.insert_config('counting', message.guild.id, '_'.join(data))
        await message.add_reaction('<:coin:1178687013583585343>')
      else:
        await message.delete()

  @commands.hybrid_command()
  @commands.has_permissions(administrator=True)
  @commands.guild_only()
  async def setcount(self, ctx, channel: discord.TextChannel = None):
    """this command will set the  mentioned channel as counting channel."""
    channel = channel or ctx.channel
    data = f"70_{channel.id}_0_0_0"
    database.insert_config('counting', ctx.guild.id, data)
    await channel.send('I will start with my fav number.')
    m = await channel.send('69')
    await m.add_reaction('<:coin:1178687013583585343>')
    embed = discord.Embed(title='Counting',
                          description=f"{channel.mention} is the counting channel.\n**How to earn more coins <:coin:1178687013583585343>**"
                                      f"\n> Counting earns coins <:coin:1178687013583585343>\n> Dommes can ruin by **`/ruin`** the game and earn coins <:coin:1178687013583585343>"
                                      f"\n> Guessing the correct number after ruing also gives coins <:coin:1178687013583585343>",
                          color=0xF2A2C0)
    embed.set_thumbnail(url=self.bot.user.display_avatar.url)
    await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  @commands.dynamic_cooldown(custom_ruin_cooldown, commands.BucketType.user)
  async def ruin(self, ctx):
    """Counting earns coins, Dommes can ruin the game by running this. they will earn coins."""
    if ctx.author.bot:
      return

    print('ruin 1')

    try:
      data = database.get_config_raw('counting', ctx.guild.id).split(
        '_')  # [number, channel, member, message, count_length]

      if ctx.channel.id != int(data[1]):
        await ctx.reply(f"You should use this command in <#{data[1]}>")
        return False

    except AttributeError:
      embed = discord.Embed(
        description=f"Counting channel is not configured yet, ask Admins to run **`/setcount #countChannel`**",
        color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return False

    ban_data = database.is_botban(ctx.author.id)
    if ban_data is None:
      try:
        data = database.get_config_raw('counting', ctx.guild.id).split(
          '_')  # [number, channel, member, message, count_length]
      except AttributeError:
        embed = discord.Embed(
          description=f"Counting channel is not configured yet, ask Admins to run **`/setcount #countChannel`**",
          color=0xF2A2C0)
        await ctx.reply(embed=embed)
        return

      has_role = lambda rid: str(rid) in [str(role.id) for role in ctx.author.roles]
      domme = database.get_config('domme', ctx.author.guild.id)[0]
      sub = database.get_config('slave', ctx.author.guild.id)[0]
      switch = database.get_config('switch', ctx.author.guild.id)[0]

      if ctx.channel.id != int(data[1]):
        await ctx.reply(f"You should use this command in <#{data[1]}>")
      elif has_role(domme) or has_role(switch):
        database.add_money(ctx.author.id, ctx.guild.id, int(data[4]), 0)
        data_ = f"{-1 * random.randint(70, 1000)}_{ctx.channel.id}_0_0_0"
        database.insert_config('counting', ctx.guild.id, data_)
        embed = discord.Embed(
          description=f"{ctx.author.mention} ruined the counting and earned {data[4]} <:coin:1178687013583585343>"
                      f"\n\n\n> **Now guess the next number to earn more**", color=0xF2A2C0)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
      else:
        roles = '>'
        for r in [*database.get_config('domme', ctx.guild.id), *database.get_config('switch', ctx.guild.id)]:
          roles = f"{roles} <@&{r}>\n>"
        embed = discord.Embed(description=f"you don't have any of the following roles to ruin the game.\n{roles[:-2]}",
                              color=0xF2A2C0)
        await ctx.send(embed=embed)
    else:
      embed = discord.Embed(title='Bot ban',
                            description=f"{ctx.author.mention} you are banned from using {self.bot.user.mention} till <t:{ban_data[1]}:F>",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def give(self, ctx, member: discord.Member, amount: int):
    """transfer coins to other members, you can only transfer coins you have."""
    if ctx.author.bot:
      return

    elif member.bot:  # when mentioned member is bot
      embed = discord.Embed(description=f"{member.mention} is a bot not a Person!",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)
      return

    ban_embed = self.ban_check(ctx.author, member)
    if ban_embed is not None:
      await ctx.send(embed=ban_embed)
      return

    coin = database.get_money(ctx.author.id, ctx.guild.id)[2]
    if coin < amount:
      await ctx.reply(
        f"🧏‍♀️ really, you are broke, you only have {coin}<:coin:1178687013583585343>")
    elif amount < 10:
      await ctx.reply(
        f"🧏‍♀️ Grrr....,  10<:coin:1178687013583585343> is minimum amount to transfer")
    else:
      database.add_money(member.id, ctx.guild.id, amount, 0)
      database.remove_money(ctx.author.id, ctx.guild.id, amount, 0)
      embed = discord.Embed(
        description=f"{ctx.author.mention} gave {amount} <:coin:1178687013583585343> to {member.mention}",
        color=0xF2A2C0)
      await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def simp(self, ctx: commands.Context, member: discord.Member):
    """simp someone, this is identical to the worship command"""
    await ctx.invoke(self.worship, member=member)

  @commands.hybrid_command(aliases=['praise', 'footkiss', 'feetkiss'])
  @commands.guild_only()
  async def worship(self, ctx, member: discord.Member):
    """worship someone, this is identical to the simp command"""
    if ctx.author.bot:
      return

    if ctx.author == member:
      embed = discord.Embed(description=f"{ctx.author.mention} you can't {ctx.command.name} yourself!",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)
      return

    elif member.bot:  # when mentioned member is bot
      embed = discord.Embed(description=f"{member.mention} is a bot not a Person!",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)
      return

    ban_embed = self.ban_check(ctx.author, member)
    if ban_embed is not None:
      await ctx.send(embed=ban_embed)
      return

    if (set(database.get_config('domme', ctx.guild.id)) & set([str(role.id) for role in member.roles])) or (
        set(database.get_config('switch', ctx.guild.id)) & set([str(role.id) for role in member.roles])):
      if ctx.channel.is_nsfw():
        money = database.get_money(ctx.author.id, ctx.guild.id)[2]
        if money >= 100:
          database.remove_money(ctx.author.id, ctx.guild.id, 100, 0)
          if not set(database.get_config('domme', ctx.guild.id)) & set([str(role.id) for role in ctx.author.roles]):
            database.add_money(ctx.author.id, ctx.guild.id, 0, 1)
            database.add_money(member.id, ctx.guild.id, 0, 5)
          database.simp(ctx.author.id, ctx.guild.id, member.id)
          simp_embed = discord.Embed(
            title=f"{ctx.author.display_name} Simps for {member.display_name}",
            description=f"",
            color=0xF2A2C0)
          with open('./assets/text/simp_image.txt', 'r') as f:
            lines = f.read().splitlines()
            link = random.choice(lines)
          simp_embed.set_image(url=link)
          await ctx.send(embed=simp_embed)
        else:
          embed = discord.Embed(
            description=f"{ctx.author.mention} you need at least 100 <:coin:1178687013583585343> to simp for {member.mention}",
            color=0xF2A2C0)
          await ctx.send(embed=embed)
      else:
        embed = discord.Embed(description=f'{ctx.author.mention} This is not a NSFW Channel try again in NSFW channel.',
                              color=0xF2A2C0)
        await ctx.reply(embed=embed)
    else:
      roles = '>'
      for r in database.get_config('domme', ctx.guild.id):
        roles = f"{roles} <@&{r}>\n>"
      embed = discord.Embed(description=f"You can only simp/worship members with following roles.\n{roles[:-2]}",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def bal(self, ctx, member: discord.Member = None):
    """this command will show your coins and gems"""
    if ctx.author.bot:
      return

    member = member or ctx.author
    ban_embed = self.ban_check(ctx.author, member)
    if ban_embed is not None:
      await ctx.send(embed=ban_embed)
      return

    elif member.bot:  # when mentioned member is bot
      embed = discord.Embed(description=f"{member.mention} is a bot not a Person!",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)

    else:
      money = database.get_money(member.id, member.guild.id)
      embed = discord.Embed(title="Cash",
                            description=f"\n> <:coin:1178687013583585343> {money[2]}\n> 💎 {money[3]}",
                            color=0xF2A2C0)
      embed.set_thumbnail(url=member.display_avatar.url)
      await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  @commands.cooldown(3, 1 * 60 * 30, commands.BucketType.user)
  async def bondageroulette(self, ctx: commands.Context, member: discord.Member):
    """
    Subs can spin the wheel and happen to run gagging, blindfolding, spanking, slapping, and more.
    """

    possible_commands = ['gag', 'fullgag', 'spank', 'slap', 'chastity', 'emoji', 'badword', 'muffs']
    chosen = random.choice(possible_commands)
    m = await ctx.send(f'Spinning...')
    await asyncio.sleep(1)
    await m.edit(content=f'😱 {chosen.title()}!')

    cmd = ctx.bot.get_command(chosen)

    try:
      print(await cmd.can_run(ctx))
    except Exception as error:
      em = discord.Embed(title=f'😭 I wanted to run {chosen}, but it\'s just that...', description=str(error.args[0]),
                         color=discord.Color.dark_red())
      return await ctx.send(embed=em)

    ctx.is_part_of_wheel = True

    await ctx.invoke(cmd, member=member)

  @commands.hybrid_command()
  @commands.guild_only()
  @relationship.sub_only()
  @commands.cooldown(3, 1 * 60 * 30, commands.BucketType.user)
  async def glitter(self, ctx: commands.Context):
    """
    As a sub/switch you can sprinkle some glitter on the glittering channel and earn 1 coin.
    """

    # is glittering channel set?

    if not (glitter_channel := database.get_config('glitterchannel', ctx.guild.id)[0]):
      return await ctx.send('> <:no:1178686922768519280> Glittering channel is not set. Ask admins to set it up.')

    # is this channel the glittering channel?
    if ctx.channel.id != int(glitter_channel):
      return await ctx.send(f'> <:no:1178686922768519280> You can only use this command in <#{glitter_channel}>')

    # is this channel in slow mode?
    if ctx.channel.slowmode_delay > 0:
      return await ctx.send(
        '> <:no:1178686922768519280> Some domme/switch wanted to make your life harder, wait until the slowmode to disappear from this channel... 😭')

    gifs_list = [
      'https://i.imgur.com/h7qTaTl.gif',
      'https://i.imgur.com/tpIWtVR.gif',
      'https://i.imgur.com/3YV33n2.gif',
      'https://i.imgur.com/9ZjAKlI.gif',
      'https://i.imgur.com/5VuO6ol.gif',
      'https://i.imgur.com/FSenGQB.gif',
      'https://i.imgur.com/I0hCc4L.gif',
      'https://i.imgur.com/W4aTdGw.gif',
      'https://i.imgur.com/uNNhRkU.gif',
      'https://i.imgur.com/zeFzKSd.gif',
      'https://i.imgur.com/WWVghFk.gif',
      'https://i.imgur.com/dlSJ2WI.gif',
      'https://i.imgur.com/sFrcfMV.gif',
      'https://i.imgur.com/QNJ7AJ5.gif',
      'https://i.imgur.com/USvbWSV.gif',
      'https://i.imgur.com/842rgyu.gif'
    ]

    gif = random.choice(gifs_list)

    embed = discord.Embed(title='<:aaglitter:1198243298716954774> Glittering',
                          description=f'{ctx.author.mention} sprinkles some glitter on the chat and earns 1 <:coin:1178687013583585343>',
                          color=0xF2A2C0)
    embed.set_image(url=gif)

    database.add_money(ctx.author.id, ctx.guild.id, 1, 0)

    await ctx.send(embed=embed)

  @commands.hybrid_command()
  @commands.guild_only()
  @commands.bot_has_permissions(manage_channels=True)
  @relationship.domme_only()
  @commands.cooldown(1, 1 * 60 * 30, commands.BucketType.user)
  async def glitterruin(self, ctx: commands.Context):
    """
    As a Domme/Switch you can ruin the glittering & do slow mode for 10mins (1 gem).
    """

    # is glittering channel set?
    if not (glitter_channel := database.get_config('glitterchannel', ctx.guild.id)[0]):
      return await ctx.send('> <:no:1178686922768519280> Glittering channel is not set. Ask admins to set it up.')

    # is this channel the glittering channel?
    if ctx.channel.id != int(glitter_channel):
      return await ctx.send(f'> <:no:1178686922768519280> You can only use this command in <#{glitter_channel}>')

    # is this channel in slow mode?
    if ctx.channel.slowmode_delay > 0:
      return await ctx.send(
        '> <:no:1178686922768519280> Someone did your dirty work already, wait until the slowmode to disappear from this channel... 🤣')

    # has money (gems)?
    if database.get_money(ctx.author.id, ctx.guild.id)[3] < 1:
      return await ctx.send('> <:no:1178686922768519280> You need at least 1 💎 to ruin the glittering channel... 😥')

    embed = discord.Embed(title='🔴 GLITTER RUIN <:yes:1184312448912732180>',
                          description=f'{ctx.author.mention} ruins the glittering channel and makes it slow mode for 10 minutes.',
                          color=0xF2A2C0)

    gifs = ['https://i.imgur.com/yatxpm5.gif',
            'https://i.imgur.com/ZMGWtMM.gif',
            'https://i.imgur.com/dvXxoG1.gif']

    embed.set_image(url=random.choice(gifs))

    database.remove_money(ctx.author.id, ctx.guild.id, 0, 1)

    await ctx.send(embed=embed)
    await ctx.channel.edit(slowmode_delay=600)

    self.bot.glitter_ruiners[ctx.guild.id] = ctx.author.id

  @commands.hybrid_command()
  @commands.guild_only()
  @commands.bot_has_permissions(manage_channels=True)
  @relationship.sub_only()
  @commands.cooldown(1, 1 * 60 * 30, commands.BucketType.user)
  async def glitterbomb(self, ctx: commands.Context):
    """
    As a bratty sub you can fix the glittering channel and undo the slow mode (1 gem).
    """

    # is glittering channel set?
    if not (glitter_channel := database.get_config('glitterchannel', ctx.guild.id)[0]):
      return await ctx.send('> <:no:1178686922768519280> Glittering channel is not set. Ask admins to set it up.')

    # is this channel the glittering channel?
    if ctx.channel.id != int(glitter_channel):
      return await ctx.send(f'> <:no:1178686922768519280> You can only use this command in <#{glitter_channel}>')

    # is this channel not in slow mode?
    if not (ctx.channel.slowmode_delay > 0):
      return await ctx.send(
        '> <:no:1178686922768519280> It\'s lovely that you want to fix the glittering channel, but it\'s not broken... 🤭')

    # has money (gems)?
    if database.get_money(ctx.author.id, ctx.guild.id)[3] < 1:
      return await ctx.send(
        '> <:no:1178686922768519280> You need at least 1 💎 to fix the glittering channel... 😥')

    embed = discord.Embed(
      title='<:aaglitter:1198243298716954774> <:aaglitter:1198243298716954774> <:aaglitter:1198243298716954774> GLITTER FIX <:aaglitter:1198243298716954774> <:aaglitter:1198243298716954774> <:aaglitter:1198243298716954774>',
      description=f'{ctx.author.mention} fixes the glittering channel and removes the slow mode.',
      color=0xF2A2C0)

    gifs = ['https://i.imgur.com/YPKWzTz.gif',
            'https://i.imgur.com/HAlMUPE.gif',
            'https://i.imgur.com/jIXiNgK.gif',
            'https://i.imgur.com/FcM2Sj6.gif']

    embed.set_image(url=random.choice(gifs))

    database.remove_money(ctx.author.id, ctx.guild.id, 0, 1)

    await ctx.send(embed=embed)
    await ctx.channel.edit(slowmode_delay=0)

    # blind the domme who did the ruin
    if ctx.guild.id not in self.bot.glitter_ruiners or not self.bot.glitter_ruiners[ctx.guild.id]:
      return

    ruiner = await ctx.guild.fetch_member(self.bot.glitter_ruiners[ctx.guild.id])

    self.bot.blinded_users[ctx.guild.id] = self.bot.blinded_users.get(ctx.guild.id, []) + [ruiner.id]

    channels = await ctx.guild.fetch_channels()
    rollback_channels = []
    for channel in channels:
      # does have read message history permission
      if not channel.permissions_for(ruiner).read_message_history:
        continue
      await channel.set_permissions(ruiner, read_message_history=False)
      rollback_channels.append(channel)

    await ruiner.send(f"you are blindfolded in the server **{ctx.guild.name}** for 10 minutes.")
    await asyncio.sleep(10 * 60)
    for channel in rollback_channels:
      await channel.set_permissions(ruiner, read_message_history=None)

  ##############################################################################
  #                                                                            #
  #                                                                            #
  #                                  ERRORS                                    #
  #                                                                            #
  #                                                                            #
  ##############################################################################

  @bondageroulette.error
  async def on_roulette_error(self, ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
      print(f'{error.retry_after=}')

      embed = discord.Embed(title="Bondageroulette Cooldown is 1h",
                            description="{} you need to wait {:,.1f} minutes to run it again.".format(
                              ctx.author.mention, (error.retry_after // 60) + 1),
                            color=0xFF2030)
      return await ctx.send(embed=embed)

    raise

  @ruin.error
  async def on_ruin_error(self, ctx, error):
    if isinstance(error, commands.CheckFailure):
      return

    if isinstance(error, commands.errors.CommandOnCooldown):
      print(f'{error.retry_after=}')

      embed = discord.Embed(title="Ruin Cooldown is 1h",
                            description="{} you need to wait {:,.1f} minutes to ruin the game again.".format(
                              ctx.author.mention, (error.retry_after // 60) + 1),
                            color=0xFF2030)
      return await ctx.send(embed=embed)
    raise


  @glitter.error
  async def on_glitter_error(self, ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
      return await ctx.send(embed=discord.Embed(title="<:no:1178686922768519280> Glittering Cooldown", description=f"You need to wait **{round(error.retry_after / 60)} minutes** to glitter again.", color=0xF2A2C0))
    raise

  @glitterruin.error
  async def on_glitterruin_error(self, ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
      return await ctx.send(embed=discord.Embed(title="<:no:1178686922768519280> Glitter Ruin Cooldown", description=f"You need to wait **{round(error.retry_after / 60)} minutes** to glitter ruin again.", color=0xF2A2C0))
    raise

  @glitterbomb.error
  async def on_glitterbomb_error(self, ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
      return await ctx.send(embed=discord.Embed(title="<:no:1178686922768519280> Glitter Fix Cooldown", description=f"You need to wait **{round(error.retry_after / 60)} minutes** to glitter fix again.", color=0xF2A2C0))
    raise

  @worship.error
  async def on_worship_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(description=f"Usage:\n**`/worship @mention`**",
                            color=0xFF2030)
      await ctx.send(embed=embed)

  @give.error
  async def on_give_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(description=f"Usage:\n**`/give @mention <amount>`**",
                            color=0xFF2030)
      await ctx.send(embed=embed)


async def setup(bot):
  await bot.add_cog(Games(bot))
