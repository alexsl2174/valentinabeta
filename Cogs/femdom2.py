#!/bin/python3
import asyncio
import typing

from utils import database
import discord
from discord import ButtonStyle
from discord.ext import commands
from cogs.femdom import YesNoView
from utils.relationship import who_is, roleplay_role


def general_checks(check_setup=True):
  async def predicate(ctx):
    if check_setup:
      if not database.is_config(ctx.guild.id):  # if bot is not configred in the server
        embed = discord.Embed(title='I am not ready yet.',
                              description=f"Ask the Admins to run the command **`/setup`** and try again",
                              color=0xF2A2C0)
        await ctx.send(embed=embed)
        return False

    return True

  return commands.check(predicate)


class BlindButton(discord.ui.Button):
  def __init__(self, key, action, member, ctx, **kw):
    super().__init__(**kw)
    self.key = key
    self.action = action
    self.member = member
    self.ctx = ctx

  async def callback(self, it: discord.Interaction):

    do_blind = False
    if self.key == 'give':
      embed = discord.Embed(
        description=f"{self.member.mention} can't see any of the Channels in this server for next 5 mins.",
        color=0xFF2030)

      do_blind = True

      database.update_slaveDB(self.member.id, 'muff', False, self.ctx.guild.id)
    elif self.key == 'cancel':
      embed = discord.Embed(description=f"Mission Aborted. lucky {self.member.mention}", color=0x08FF08)
      await self.action.chastity(True)

      database.update_slaveDB(self.member.id, 'muff', True, self.ctx.guild.id)

    # await it.channel.send('<:yes:1184312448912732180>')

    await it.response.edit_message(embed=embed, view=None)

    async def blind():
      await self.action.blind()

    if do_blind:
      await asyncio.create_task(blind())


class BlindView(discord.ui.View):
  def __init__(self, action, member, ctx):
    self.member = member
    self.ctx = ctx
    super().__init__(timeout=90)

    self.add_item(
      BlindButton(style=ButtonStyle.green, label='Yes do it', emoji='😵‍💫', key='give', ctx=ctx,
                  member=member,
                  action=action),
    )

    self.add_item(
      BlindButton(style=ButtonStyle.red, label='No', emoji='✖️', key='cancel', ctx=ctx,
                  member=member, action=action),
    )

  async def interaction_check(self, it: discord.Interaction):
    return self.ctx.author.id == it.user.id


class ChastityButton(discord.ui.Button):
  def __init__(self, key, action, member, ctx, **kw):
    super().__init__(**kw)
    self.key = key
    self.action = action
    self.member = member
    self.ctx = ctx

  async def callback(self, it: discord.Interaction):

    if self.key == 'lock':
      embed = discord.Embed(description=f"{self.member.mention} can't access NSFW Channels in this server.",
                            color=0xFF2030)
      await self.action.chastity(access=False)
      database.update_slaveDB(self.member.id, 'chastity', False, self.ctx.guild.id)
    elif self.key == 'unlock':
      embed = discord.Embed(description=f"{self.member.mention} can access NSFW Channels in this server.",
                            color=0x08FF08)
      await self.action.chastity(access=True)

      database.update_slaveDB(self.member.id, 'chastity', True, self.ctx.guild.id)

    # await it.channel.send('<:yes:1184312448912732180>')

    await it.response.edit_message(embed=embed, view=None)


class ChastityView(discord.ui.View):
  def __init__(self, action, member, ctx):
    self.member = member
    self.ctx = ctx
    super().__init__(timeout=90)

    dbrsp = database.get_slave_from_DB(member.id, ctx.guild.id)
    print(f'getSlave({member}, {ctx.guild}): chastity={dbrsp[0][6]}')

    dsbl = dbrsp[0][6]

    self.add_item(
      ChastityButton(style=ButtonStyle.red, label='Chastity Lock', emoji='🔒', key='lock', disabled=not dsbl, ctx=ctx,
                     member=member,
                     action=action),
    )

    self.add_item(
      ChastityButton(style=ButtonStyle.green, label='Chastity Unlock', emoji='🔓', key='unlock', disabled=dsbl,
                     ctx=ctx,
                     member=member, action=action),
    )

  async def interaction_check(self, it: discord.Interaction):
    return self.ctx.author.id == it.user.id


class MuffsButton(discord.ui.Button):
  def __init__(self, key, action, member, ctx, **kw):
    super().__init__(**kw)
    self.key = key
    self.action = action
    self.member = member
    self.ctx = ctx

  async def callback(self, it: discord.Interaction):

    if self.key == 'give':
      embed = discord.Embed(description=f"{self.member.mention} can't connect to any Voice Channels in this server.",
                            color=0xFF2030)
      await self.action.muff(False)
      database.update_slaveDB(self.member.id, 'muff', False, self.ctx.guild.id)
    elif self.key == 'rem':
      embed = discord.Embed(description=f"{self.member.mention} can connect to Voice Channels in this server.",
                            color=0x08FF08)
      await self.action.muff(True)

      database.update_slaveDB(self.member.id, 'muff', True, self.ctx.guild.id)

    # await it.channel.send('<:yes:1184312448912732180>')

    await it.response.edit_message(embed=embed, view=None)


class MuffsView(discord.ui.View):
  def __init__(self, action, member, ctx):
    self.member = member
    self.ctx = ctx
    super().__init__(timeout=90)

    dsbl = database.get_slave_from_DB(member.id, ctx.guild.id)[0][7]

    self.add_item(
      MuffsButton(style=ButtonStyle.green, label='Give Ear Muffs', key='give', disabled=not dsbl, ctx=ctx,
                  member=member,
                  action=action),
    )

    self.add_item(
      MuffsButton(style=ButtonStyle.red, label='Remove Ear Muffs', key='rem', disabled=dsbl, ctx=ctx, member=member,
                  action=action),
    )

  async def interaction_check(self, it: discord.Interaction):
    return self.ctx.author.id == it.user.id


class Action:
  def __init__(self, bot, ctx, member):
    self.bot = bot
    self.ctx = ctx
    self.author = ctx.author
    self.member = member

  def list_roles(self, roles):
    if isinstance(roles, list):
      role = '>'
      for r in roles:
        role = f"{role} <@&{r}>\n>"
      return role[:-2]
    else:
      return roles

  async def react(self, y_n):
    if y_n == 'yes' or y_n == 'y':
      await self.ctx.message.add_reaction('👌')
    elif y_n == 'no' or y_n == 'n':
      await self.ctx.message.add_reaction('<:no:1178686922768519280>')

  async def chastity(self, access, temp=False):
    channels = await self.ctx.guild.fetch_channels()
    for channel in channels:
      if channel.is_nsfw():
        if access:
          await channel.set_permissions(self.member, overwrite=None)
          database.update_slaveDB(self.member.id, 'chastity', True, self.ctx.guild.id)
        else:
          await channel.set_permissions(self.member, view_channel=False)
          database.update_slaveDB(self.member.id, 'chastity', False, self.ctx.guild.id)
    if temp:
      await asyncio.sleep(1 * 60 * 60)
      for channel in channels:
        if channel.is_nsfw():
          await channel.set_permissions(self.member, overwrite=None)
          database.update_slaveDB(self.member.id, 'chastity', True, self.ctx.guild.id)

  async def muff(self, access):
    channels = await self.ctx.guild.fetch_channels()
    for channel in channels:
      if isinstance(channel, discord.channel.VoiceChannel):
        if access:
          await channel.set_permissions(self.member, overwrite=None)
          database.update_slaveDB(self.member.id, 'muff', False, self.ctx.guild.id)
        else:
          await channel.set_permissions(self.member, connect=False)
          database.update_slaveDB(self.member.id, 'muff', True, self.ctx.guild.id)

  async def blind(self):
    self.bot.blinded_users[self.ctx.guild.id] = self.bot.blinded_users.get(self.ctx.guild.id, []) + [self.member.id]

    channels = await self.ctx.guild.fetch_channels()
    for channel in channels:
      await channel.set_permissions(self.member, view_channel=False, send_messages=False)
    await self.member.send(f"you are blindfolded in the server **{self.ctx.guild.name}** for 5 minutes.")
    await asyncio.sleep(5 * 60)
    for channel in channels:
      await channel.set_permissions(self.member, overwrite=None)


class Femdom2(commands.Cog):
  """Femdom commands part 2 😏"""
  def __init__(self, bot):
    self.bot = bot

  def list_roles(self, roles):
    if isinstance(roles, list):
      role = '>'
      for r in roles:
        role = f"{role} <@&{r}>\n>"
      return role[:-2]
    else:
      return roles

  async def check_error(self, ctx, msg: typing.Union[str, tuple[str, str]]):
    """Sends a custom error that wasn't handled on self.proper_checks() due to any reason"""
    if callable(msg):
      msg = msg()  # lambda

    title = 'Nah'

    if isinstance(msg, tuple):  # (title, desc)
      title, msg = msg

    em = discord.Embed(title=title, description=msg, color=0xF2A2C0)
    m = await ctx.send(embed=em)
    await m.reply('<:no:1178686922768519280>')

  async def proper_checks(self, ctx: commands.Context, member: discord.Member, messages: dict,
                          return_whois: bool = False) -> bool:
    """Does the checks on whether the command should be run (relationship checks, etc.)"""

    if not database.is_config(ctx.guild.id):  # if bot is not configred in the server
      embed = discord.Embed(title='I am not ready yet.',
                            description=f"Ask the Admins to run the command **`/setup`** and try again",
                            color=0xF2A2C0)
      await ctx.send(embed=embed)
      if return_whois:
        return False, -1
      return False

    if member.id == self.bot.user.id:  # Temptress ID, owning Temptress
      embed = discord.Embed(description=messages.get('on_temptress', "You can't run this command on me! 😤"),
                            color=0xF2A2C0)
      await ctx.send(embed=embed)
      print('bot')
      if return_whois:
        return False, -1
      return False

    if member.bot:  # owning a random bot
      if messages.get('on_bot') != True:
        embed = discord.Embed(description=messages.get('on_bot', "You can't run this command on a bot! 🐲"),
                              color=0xF2A2C0)
        await ctx.send(embed=embed)
        print('bot')
        if return_whois:
          return False, -1
        return False

    # relationship
    print('whois')
    member_is = who_is(ctx.author, member)
    print(f'The relationship is: {member_is}')

    if member_is in [222, 111]:
      msg = f"{member.mention} should have any of the following roles \n{self.list_roles(database.get_config('domme', member.guild.id))}\n{self.list_roles(database.get_config('slave', member.guild.id))}"
    elif member_is == 0:
      msg = f"{ctx.author.mention}, you should have any of the following roles \n{self.list_roles(database.get_config('domme', member.guild.id))}\n{self.list_roles(database.get_config('slave', member.guild.id))}"
    elif member_is == -1:
      msg = ("Bot ban", f"{member.mention} is banned from using {self.bot.user.mention}")
    elif member_is == 69:
      msg = f"{ctx.author.mention} i'm sorry but i can't let you do it. {member.mention} asked me to protect them from any actions that aren't from their owners."
    elif member_is < -1:
      msg = (
        "Bot ban",
        f"{ctx.author.mention} you are banned from using {self.bot.user.mention} till <t:{member_is * -1}:F>")
    else:
      if member_is > 300 and messages.get('>300') is not None:
        if return_whois:
          return True, member_is
        return True

      msg = messages.get(str(member_is))

    if msg is not None:
      if callable(msg):
        msg = msg()  # lambda

      if isinstance(msg, tuple):  # (title, desc)
        title, msg = msg
      else:
        title = 'Nah' if member_is in [2, 202, 201, 300] else 'Pathetic!'

      em = discord.Embed(title=title, description=msg, color=0xF2A2C0)
      await ctx.send(embed=em)
      if return_whois:
        return False, member_is
      return False

    if return_whois:
      return True, member_is
    return True

  @commands.hybrid_command()
  @commands.guild_only()
  async def chastity(self, ctx, member: discord.Member):
    """Blocks NSFW sub channels. Note: Dommes must own sub for chastity lock."""
    should_continue, member_is = await self.proper_checks(ctx, member, messages=dict(
      on_temptress=f"You can't deny my cum permission, I will cum all day long and you can't stop me.<a:bully:968288741733064814>",
      on_bot=f"You can't keep Bots in chastity.",
      **{
        "1": lambda: f"Pathetic!!, This simpleton slave is trying to be in chastity!, {ctx.author.mention} you can't "
                     f"do anything without Domme's permission.",
        "2": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                     f"a Domme in chastity.",
        "202": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                       f"a Domme in chastity.",
        "201": lambda: f"{ctx.author.mention}, you can't do such a thing. {member.mention} is a free slave!"
                       f" the sub must be owned by you.",
        ">300": lambda: f"{member.mention} is owned by somebody else it's their property.",
        "101": lambda: f"You foolish slave. You think you can chastity lock when you are a slave, {ctx.author.mention}! "
                       f"how Pathetic!!!\nI need to tell this joke to Deity, they will love it.",
        "102": lambda: f'{ctx.author.mention}, you are a slave, you are not as powerful as a domme and you '
                       f'will never be! How could you even consider trying something s'
                       f'o foolish!! {member.mention} I think someone needs to learn a lesson!!!, brainless slave'
      }
    ), return_whois=True)

    if not should_continue:
      return

    if member.guild_permissions.administrator:
      embed = discord.Embed(description=f"{member.mention} have administrator permission, I am sorry.",
                            color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    action = Action(self.bot, ctx, member)

    # --------------------------------------------------------
    if member_is == 200:
      embed = discord.Embed(title='So what should I do?', color=0xF2A2C0)
      await ctx.send(embed=embed, view=ChastityView(action, member, ctx))
      return

  @commands.hybrid_command()
  @commands.guild_only()
  async def muffs(self, ctx, member: discord.Member):
    """Blocks sub voice channels. Note: Dommes must own sub for voice block."""

    should_continue, member_is = await self.proper_checks(ctx, member, messages=dict(
      on_bot=f"{member.mention} is bot don't be dumb like Shaman.",
      **{
        "1": lambda: f"Pathetic!!, This simpleton slave is trying to cover ears!, {ctx.author.mention} you can't "
                     f"do anything without Domme's permission.",
        "2": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                     f"a Domme suffering.",
        "202": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                       f"a Domme suffering.",
        "201": lambda: f"{ctx.author.mention}, you can't do such a thing. {member.mention} is a free slave!"
                       f" the sub must be owned by you.",
        ">300": lambda: f"{member.mention} is owned by somebody else it's their property.",
        "101": lambda: f"You foolish slave. You think you can Ear Muff someone when you are a slave, {ctx.author.mention}! "
                       f"how Pathetic!!!\n I need to tell this joke to Deity, they will love it.",
        "102": lambda: f'{ctx.author.mention}, you are a slave, you are not as powerful as a domme and you '
                       f'will never be! How could you even consider trying something s'
                       f'o foolish!! {member.mention} I think someone needs to learn a lesson!!!, brainless slave'
      }
    ), return_whois=True)

    if not should_continue:
      return

    if member.guild_permissions.administrator:
      embed = discord.Embed(description=f"{member.mention} have administrator permission, I am sorry.",
                            color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    action = Action(self.bot, ctx, member)

    # --------------------------------------------------------
    if member_is == 200:
      print('BRUH!')
      embed = discord.Embed(title='So what should I do?', color=0xF2A2C0)
      await ctx.send(embed=embed, view=MuffsView(action, member, ctx))
      return

  @commands.hybrid_command()
  @commands.guild_only()
  @commands.cooldown(3, 4 * 60 * 60, commands.BucketType.user)
  async def blind(self, ctx, member: discord.Member):
    """This command blocks all sub channels for 5 minutes. Note: Dommes must own a sub before using this."""

    should_continue, member_is = await self.proper_checks(ctx, member, messages=dict(
      on_temptress=f"You can't blindfold me, my eyes are powerful I see everything.",
      on_bot=f"You can't blindfold Bots.",
      **{
        "1": lambda: f"Pathetic!!, This simpleton slave is trying to blindfold!, {ctx.author.mention} you can't "
                     f"do anything without Domme's permission.",
        "2": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                     f"a Domme blindfolded.",
        "202": lambda: f"I am sorry {ctx.author.mention}, but I can't do such a thing. It's unbearable to see "
                       f"a Domme blindfolded.",
        "201": lambda: f"{ctx.author.mention}, you can't do such a thing. {member.mention} is a free slave!"
                       f" the sub must be owned by you.",
        ">300": lambda: f"{member.mention} is owned by somebody else it's their property.",
        "101": lambda: f"You foolish slave. You think you can blindfold someone when you are a slave, {ctx.author.mention}! "
                       f"how Pathetic!!!\nI need to tell this joke to Deity, they will love it.",
        "102": lambda: f'{ctx.author.mention}, you are a slave, you are not as powerful as a domme and you '
                       f'will never be! How could you even consider trying something s'
                       f'o foolish!! {member.mention} I think someone needs to learn a lesson!!!, brainless slave'
      }
    ), return_whois=True)

    if not should_continue:
      return

    if member.guild_permissions.administrator:
      embed = discord.Embed(description=f"{member.mention} have administrator permission, I am sorry.",
                            color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    action = Action(self.bot, ctx, member)

    # --------------------------------------------------------

    if member_is == 200:
      embed = discord.Embed(title='Are you sure that you wanna do this?',
                            description=f"{member.mention} will not be able to see any channels in this server for 5 mins.",
                            color=0xF2A2C0)

      if member.id in self.bot.blinded_users.get(ctx.guild.id, []):
        em = discord.Embed(title='They are already blindfolded!',
                           description=f"{member.mention} is already blindfolded, do you want to undo the blind?",
                           color=discord.Color.brand_red())

        async def unblind(mem):
          channels = await mem.guild.fetch_channels()
          for channel in channels:
            await channel.set_permissions(mem, overwrite=None)

        return await ctx.send(embed=em, view=YesNoView(member, action=unblind, msg=dict(
          title='Blindfold removed!',
          description=f'{member.mention} can now see!'
        )))

      await ctx.send(embed=embed, view=BlindView(action, member, ctx))
      return

  @commands.hybrid_command()
  @general_checks()
  async def safeword(self, ctx: commands.Context):
    """apply a safeword if you are not feeling right."""

    # must be sub/switch
    is_locked = discord.utils.get(ctx.author.roles, name='Prisoner')

    if roleplay_role(ctx.author) not in ['sub', 'switch'] and not is_locked:
      return await self.check_error(ctx, "You must be a sub or switch to use this command.")

    # is gagged / is blindfolded / is fullgagged / is locked
    dbrsp = database.get_slave_from_DB(ctx.author.id, ctx.guild.id)[0]

    is_gagged = dbrsp[2] != 'off'

    if not (is_gagged or is_locked):
      return await self.check_error(ctx, "You are not under anything, relax 😤.")

    safelog_channel = database.get_config('safelog', ctx.guild.id)[0]
    if safelog_channel:
      safelog_channel = ctx.guild.get_channel(int(safelog_channel))

    async def send_safelog(on: str):
      if not safelog_channel:
        return

      em = discord.Embed(
        title='<:catblushyyy:1103124612637802496> safeword used!',
        description=f'**{on}** was too much for {ctx.author.mention} to handle.',
        color=discord.Color.brand_red()
      )
      em.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
      em.timestamp = ctx.message.created_at
      await safelog_channel.send(embed=em)

    em = discord.Embed(
      title='Safeword Applied',
      description=f'You are not under anything anymore.',
      color=discord.Color.brand_green()
    )

    if is_gagged:
      database.update_slaveDB(ctx.author.id, 'gag', 'off', ctx.guild.id)
      em.description = f"<:catblushyyy:1103124612637802496> {ctx.author.mention} you used the safeword, you are not gagged anymore."
      await ctx.send(embed=em)
      await send_safelog('Fullgag' if dbrsp[2] == 'fullgag' else f'Gag ({dbrsp[2]})')
      return





  ##############################################################################
  #                                                                            #
  #                                                                            #
  #                                 ERRORS                                     #
  #                                                                            #
  #                                                                            #
  ##############################################################################

  @chastity.error
  async def on_chastity_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(description=f"Usage:\n**`/chastity @mention`**",
                            color=0xFF2030)
      await ctx.send(embed=embed)

    raise error

  @muffs.error
  async def on_muff_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(description=f"Usage:\n**`/muffs @mention`**",
                            color=0xFF2030)
      await ctx.send(embed=embed)

    raise error

  @blind.error
  async def on_blind_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(description=f"Usage:\n> **`/blind @mention`** ",
                            color=0xFF2030)
      await ctx.send(embed=embed)


    elif isinstance(error, commands.errors.CommandOnCooldown):
      embed = discord.Embed(title="Blindfold Cooldown is 4h",
                            description="{} you need to wait {:,.1f} minutes to blindfold a slave again.".format(
                              ctx.author.mention, (error.retry_after // 60) + 1),
                            color=0xFF2030)
      await ctx.send(embed=embed)

    raise error


async def setup(bot):
  await bot.add_cog(Femdom2(bot))
