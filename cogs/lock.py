# !/bin/python3
"""
commands    |   description
----------------------------
lock        |   member will domme/switch role can lock members with slave role
unlock      |   admins and the member who locked the slave can unlock the locked slave from prison
escape      |   if the prisoner has gem then they can use it to escape the prison without lines and get 6h of lockproof


events              |   description
----------------------------
on_message          |   when prisoner sends message bot checks it and gives new line if its correct
on_prisoner_remove  |   unlocks all the prisoner
on_prison_delete    |   deletes the prisoner role and unlocks all the prisoners

Note: a slave can't be locked multiple times without 30 minutes of cooldown in between
"""
import asyncio
import contextlib
import random
import re
import textwrap
from random import choice, getrandbits
from string import ascii_letters
import typing

from utils import database
import discord
import unicodedata
from PIL import Image, ImageDraw, ImageFont
from discord import ButtonStyle
from discord.ext import commands, tasks
from utils.relationship import who_is


def make_image(sentence, memberid, level=None):
  """
  Saves lines png in ./Image with filename coresponding to member's ID
  returns randomly capitalized string.

  Note string includes newline as character
  """
  new_string = ''
  for character in sentence:
    if bool(getrandbits(1)):
      new_string += character.upper()
    else:
      new_string += character.lower()

  img = Image.open('./assets/images/blank_discord_bg.png')
  font = ImageFont.truetype('./Fonts/Kalam-Bold.ttf', 43)
  draw = ImageDraw.Draw(img)
  avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
  max_char_count = int(img.size[0] * .95 / avg_char_width)  # 618
  new_string = textwrap.fill(text=new_string, width=max_char_count)

  draw.text(xy=(img.size[0] / 2, img.size[1] / 2), text=new_string, font=font, fill='#ffffff', anchor='mm')
  img.save(f'./assets/temp/{memberid}.png')
  return new_string


def deEmojify(text):
  "function to remove emojis from text"
  regrex_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002500-\U00002BEF"  # chinese char
                              u"\U00002702-\U000027B0"
                              u"\U00002702-\U000027B0"
                              u"\U000024C2-\U0001F251"
                              u"\U0001f926-\U0001f937"
                              u"\U00010000-\U0010ffff"
                              u"\u2640-\u2642"
                              u"\u2600-\u2B55"
                              u"\u200d"
                              u"\u23cf"
                              u"\u23e9"
                              u"\u231a"
                              u"\ufe0f"  # dingbats
                              u"\u3030"
                              "]+", re.UNICODE)
  return regrex_pattern.sub(r'', text)


class LockActionButton(discord.ui.Button):
  def __init__(self, ctx, member, member_is, key, **kw):
    self.ctx = ctx
    self.member = member
    self.key = key
    self.member_is = member_is
    self.sentence = kw.pop('sentence', None)

    self.custom_lock_times = None

    super().__init__(**kw)

  async def first_stage(self, it: discord.Interaction):
    if self.key == 'praise':
      print('HEI')
      with open('./assets/text/praise.txt', 'r') as praise:
        lines = praise.read().splitlines()
        sentence = choice(lines)
    elif self.key == 'degrade':
      with open('./assets/text/degrade.txt', 'r') as degrade:
        lines = degrade.read().splitlines()
        sentence = choice(lines)
    elif self.key == 'custom':
      check = lambda m: self.ctx.author.id == m.author.id and m.channel.id == self.ctx.channel.id

      em = discord.Embed(title='Type the Custom line.', description='not more that 120 characters', color=0x9479ED)
      await it.message.edit(embed=em, view=None)
      await it.response.defer()

      try:
        m = await self.ctx.bot.wait_for('message', timeout=120, check=check)
        sentence = re.sub('[^A-Za-z0-9]+', ' ',
                          unicodedata.normalize('NFD', m.content).encode('ascii', 'ignore').decode(
                            'utf-8')).lower()
        sentence = deEmojify(sentence)

        if sentence.replace(' ', '') == '':
          embed = discord.Embed(title='Invalid Sentence',
                                description=f'{self.ctx.author.mention} failed to lock {self.member.mention}',
                                color=0xFF2030)
          return await it.message.edit(embed=embed)
        elif len(sentence) > 125:
          embed = discord.Embed(title='Not more than 120 characters',
                                description=f'{self.ctx.author.mention} failed to lock {self.member.mention}',
                                color=0xFF2030)
          return await it.message.edit(embed=embed)

        await m.delete()
      except TimeoutError:
        em = discord.Embed(title='Time is over the slave escaped from prison', color=0x9479ED)
        return await it.message.edit(embed=em)

    # torture level
    self.view.clear_items()
    self.view.add_item(
      LockActionButton(self.ctx, self.member, self.member_is, sentence=sentence, key="easy", style=ButtonStyle.green,
                       label="Easy", emoji='🥱'))
    self.view.add_item(
      LockActionButton(self.ctx, self.member, self.member_is, sentence=sentence, key="medium",
                       style=ButtonStyle.blurple, label="Medium", emoji='😈'))
    self.view.add_item(
      LockActionButton(self.ctx, self.member, self.member_is, sentence=sentence, key="hard", style=ButtonStyle.red,
                       label="Hard", emoji='💀'))

    self.view.add_item(
      LockActionButton(self.ctx, self.member, self.member_is, sentence=sentence, key="customlines",
                       style=ButtonStyle.gray,
                       label="Custom Times", emoji='🔢'))

    em = discord.Embed(title='Which level of torture do you prefer?', color=0x9479ED)

    # await it.message.edit(content='\u200b', embed=None, view=None)
    try:
      await it.response.defer()
    except Exception as e:
      pass
    await it.message.edit(embed=em, view=self.view)

  async def second_stage(self, it: discord.Interaction):
    print('second stage!!!!!!!!!!!', self.key)

    if self.key == 'easy':
      num = random.randint(2, 3)
    elif self.key == 'medium':
      num = random.randint(3, 5)
    elif self.key == 'hard':
      num = random.randint(7, 10)
    elif self.key == 'customlines':
      em = discord.Embed(title='How many times should they say it?', description='type a reasonable number',
                         color=0x9479ED)
      print('hii')
      await it.message.edit(embed=em, view=None)

      num = None
      try:
        check = lambda m: it.user.id == m.author.id and m.channel.id == it.channel.id
        m = await self.ctx.bot.wait_for('message', timeout=120, check=check)

        try:
          num = int(m.content)
        except ValueError:
          embed = discord.Embed(title='Invalid Number',
                                description=f'{self.ctx.author.mention} failed to lock {self.member.mention}',
                                color=0xFF2030)
          return await it.message.edit(embed=embed)

        await m.delete()
      except TimeoutError:
        em = discord.Embed(title='Time is over the slave escaped from prison', color=0x9479ED)
        return await it.message.edit(embed=em)
      except discord.NotFound:
        return

    roles = "".join([str(role.id) for role in self.member.roles][1:])

    with contextlib.suppress(AttributeError):
      roles = roles.replace(str(self.ctx.guild.premium_subscriber_role.id), '')

    i_have_power = (self.ctx.me.top_role > self.member.top_role) and (self.ctx.guild.owner.id != self.member.id if self.ctx.guild.owner else True)

    if not i_have_power:
      no_power_embed = discord.Embed(title='I don\'t have power',
                                     description=f'{self.member.mention} might be server owner or having higher role than me <:cry:968287446217400320>',
                                     color=0xFF2030)
      await it.response.defer()
      return await it.message.edit(embed=no_power_embed, view=None)

    embed = discord.Embed(description=f"I am locking {self.member.mention} ⏱️", color=0xFF2030)
    await it.message.edit(embed=embed)

    switch = self.ctx.guild.get_role(int(database.get_config('switch', self.ctx.guild.id)[0]))
    sub = self.ctx.guild.get_role(int(database.get_config('slave', self.ctx.guild.id)[0]))

    if sub in self.member.roles:
      await self.member.remove_roles(sub)
      self.ctx.bot.prison_roles[self.member.id] = 'slave'

    if switch in self.member.roles:
      await self.member.remove_roles(switch)
      self.ctx.bot.prison_roles[self.member.id] = 'switch'

    if self.member_is == 200:
      database.remove_money(self.ctx.author.id, self.ctx.guild.id, 0, 0)
    else:
      database.remove_money(self.ctx.author.id, self.ctx.guild.id, 0, 10)

    prisoner = self.ctx.guild.get_role(int(database.get_config('prisoner', self.ctx.guild.id)[0]))
    await self.member.add_roles(prisoner)
    domme_name = re.sub('[^A-Za-z0-9]+', ' ',
                        unicodedata.normalize('NFD', self.ctx.author.name).encode('ascii', 'ignore').decode(
                          'utf-8')).lower()
    sub_name = re.sub('[^A-Za-z0-9]+', ' ',
                      unicodedata.normalize('NFD', self.member.name).encode('ascii', 'ignore').decode(
                        'utf-8')).lower()

    sentence = self.sentence.replace('#domme', domme_name).replace('#slave', sub_name)

    # todo: suggestion to have a different font for each difficulty
    #       pass self.key to make_image and use it to select the font
    #       with a mapping dict or something.

    sentence = make_image(sentence, self.member.id, level=self.key).replace('\n', ' ')
    sentence = sentence.replace('  ', ' ')

    prison = self.ctx.guild.get_channel(int(database.get_config('prison', self.ctx.guild.id)[0]))

    embed = discord.Embed(
      description=f"{self.ctx.author.mention} received 50 <:coin:1178687013583585343> by locking {self.member.mention} in {prison.mention}",
      color=0x9479ED)
    await it.message.edit(embed=embed, view=None)

    await prison.send(
      f"{self.member.mention} you have to write 👇 {num} times to be free or you have to wait 2h or use **`/escape`** to be free from prison. ||(it is case sensitive)||")
    await prison.send(file=discord.File(f'./assets/temp/{self.member.id}.png'))
    database.lock(self.member.id, self.ctx.guild.id, self.ctx.author.id, num, sentence, roles)
    database.add_money(self.ctx.author.id, self.ctx.guild.id, 50, 0)

    await asyncio.sleep(60 * 60 * 2)

    member = await self.ctx.guild.fetch_member(self.member.id)
    if prisoner in member.roles:
      await self.member.remove_roles(prisoner)
      database.insert_escape(self.ctx.author.id, self.ctx.guild.id, 0.5, 'cooldown')
      await member.add_roles(
        member.guild.get_role(int(database.get_config(self.ctx.bot.prison_roles[member.id], member.guild.id)[0])))

  async def callback(self, it: discord.Interaction):
    if self.key in ['praise', 'degrade', 'custom']:
      await self.first_stage(it)
    elif self.key in ['easy', 'medium', 'hard', 'customlines']:
      await self.second_stage(it)


class LockActionView(discord.ui.View):
  def __init__(self, ctx, member, member_is):
    self.ctx = ctx
    self.member = member

    super().__init__(timeout=60 * 30)

    self.add_item(
      LockActionButton(ctx, member, member_is, key="praise", style=ButtonStyle.green, label="Praise", emoji='🛐'))
    self.add_item(
      LockActionButton(ctx, member, member_is, key="degrade", style=ButtonStyle.red, label="Degrade", emoji='🙇‍♂️'))
    self.add_item(
      LockActionButton(ctx, member, member_is, key="custom", style=ButtonStyle.blurple, label="Custom Lines",
                       emoji='✍️'))

  async def interaction_check(self, it: discord.Interaction):
    return it.user == self.ctx.author


class Lock(commands.Cog):
  """commands for the lock roleplay"""
  def __init__(self, bot):
    self.bot = bot
    self.escape_cleanup.start()

  def list_roles(self, roles):
    """
    returns string-metion-roles for embed
    """
    if isinstance(roles, list):
      role = '>'
      for r in roles:
        role = f"{role} <@&{r}>\n>"
      return role[:-2]
    else:
      return roles

  @tasks.loop(seconds=60 * 5)
  async def escape_cleanup(self):
    """
    clears escape and botban DB
    """
    database.clear_escape()

  @commands.Cog.listener()
  async def on_member_update(self, before, after):
    """
    gives back all the roles of member when prisoner role is removed from member or when role gets deleted.
    """
    prisoner = before.guild.get_role(int(database.get_config('prisoner', before.guild.id)[0]))
    if prisoner is not None:
      if {prisoner.id} & set([str(role.id) for role in before.roles]) and not (
          {prisoner.id} & set([str(role.id) for role in after.roles])):
        roles = database.release_prison(after.id, after.guild.id)
        if roles != [0]:
          for role in roles:
            r = after.guild.get_role(role)
            await after.add_roles(r)
          await after.send(
            f"You are now released from <#{database.get_config('prison', before.guild.id)[0]}> of {after.guild.name}")

  @commands.Cog.listener()
  async def on_guild_channel_create(self, channel):
    """
    when new channel is created, bot added prisoner role to the channel.
    if prisoner role is not found bot creates it and add it to all channel.
    """
    prisoner = channel.guild.get_role(int(database.get_config('prisoner', channel.guild.id)[0]))
    if prisoner is None:
      prisoner = await channel.guild.create_role(name='Prisoner', color=0x591B32)
      database.insert_config('prisoner', channel.guild.id, prisoner.id)
      channels = await channel.guild.fetch_channels()
      for ch in channels:
        await ch.set_permissions(prisoner, view_channel=False, send_messages=False)
      prison = channel.guild.get_channel(database.get_config('prison', channel.guild.id)[0])
      if prison is not None:
        await prison.set_permissions(prisoner, view_channel=True, send_messages=True, read_message_history=True)

    with contextlib.suppress(discord.Forbidden):
      await channel.set_permissions(prisoner, view_channel=False, send_messages=False)

  @commands.Cog.listener()
  async def on_message(self, message):
    """
    if author have prisoner role checks if its correct line and updates prison DB
    there is 10% of lossing 2 coins on every wrong lines
    """

    if message.author.bot:
      return


    if str(database.get_config('prisoner', message.guild.id)[0]) in [str(role.id) for role in message.author.roles]:
      data = database.get_prisoner(message.author.id, message.guild.id)
      print(data)
      if message.content.lower().strip() == data[4].lower().strip():
        await message.add_reaction('👌')
        await message.add_reaction('<:coin:1178687013583585343>')
        sentence = make_image(message.content, message.author.id).replace('\n', ' ')
        sentence = sentence.replace('  ', ' ')
        database.update_lock(message.author.id, sentence, message.guild.id)
        if data[3] == 1:
          member = message.author
          prisoner = message.guild.get_role(int(database.get_config('prisoner', message.guild.id)[0]))
          await message.author.remove_roles(prisoner)
          await message.reply(
            f"{message.author.mention} you are now released from {message.channel.mention} for good behavior and writing the lines.")
          database.insert_escape(message.author.id, message.guild.id, 0.2, 'cooldown')
          await member.add_roles(member.guild.get_role(
            int(database.get_config(self.bot.prison_roles[message.author.id], member.guild.id)[0])))

          return
        prison = message.guild.get_channel(int(database.get_config('prison', message.guild.id)[0]))
        await prison.send(
          f"{message.author.mention} you have to write 👇 {int(data[3] - 1)} times to be free or you have to wait 2h or use **`s.escape`** to be free from prison. ||(it is case sensitive)||")
        await prison.send(file=discord.File(f'./assets/temp/{message.author.id}.png'))
      else:
        await message.add_reaction('<:no:1178686922768519280>')
        if random.random() < 0.1:
          coins_to_remove = (2 + random.randint(0, 3))
          database.remove_money(message.author.id, message.guild.id, coins_to_remove, 0)

  @commands.Cog.listener()
  async def on_guild_channel_delete(self, channel):
    """
    deletes prisoner role of prison channel is deleted to release all prisoner from prison
    """
    if channel.id == database.get_config('prison', channel.guild.id)[0]:
      prisoner = channel.guild.get_role(int(database.get_config('prisoner', channel.guild.id)[0]))
      await prisoner.delete()

  async def check_error(self, ctx, msg: typing.Union[str, tuple[str, str]]):
    """Sends a custom error that wasn't handled on self.proper_checks() due to any reason"""
    msg = msg()  # lambda

    title = 'Nah'

    if isinstance(msg, tuple):  # (title, desc)
      title, msg = msg

    em = discord.Embed(title=title, description=msg, color=0xF2A2C0)
    await ctx.send(embed=em)

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
  # @commands.cooldown(2, 3 * 60 * 60, commands.BucketType.user)
  async def lock(self, ctx, member: discord.Member):
    """
    the might lock command which brings chaos to servers
    """

    should_continue = await self.proper_checks(ctx, member, messages=dict(
      on_bot=f"Bots are too powerful you can't lock them.",
      **{
        "2": lambda: f"Only Subs can be locked in punished in <#{database.get_config('prison', ctx.guild.id)[0]}>",
        "202": lambda: f"Only Subs can be locked in punished in <#{database.get_config('prison', ctx.guild.id)[0]}>",
        "1": lambda: f"{ctx.author.mention} you are not worthy to use this command.",
        "101": lambda: f"{ctx.author.mention} you are not worthy to use this command.",
        "102": lambda: f"{ctx.author.mention} you are not worthy to use this command.",
        # "200": lambda: ("Hmmm", f"{ctx.author.mention} You already own him, {member.mention} is already your pet"),
        #                 f'{ctx.author.mention} , you are a slave, you are not worthy of owning anyone or anything in your whole life! Especially not a Domme, how could you even consider trying something so foolish!! {member.mention} I think someone needs to learn a lesson!!!'),

      }
    ))

    if not should_continue:
      print(f'I do not continue, ')
      return

    if ctx.author.id in database.get_blacklist(ctx.guild.id):  # if the author is a blacklisted member
      await ctx.reply('you are blacklisted by the Admins ¯\\_(ツ)_/¯')
      return

    if set(str(database.get_config('prisoner', ctx.guild.id))) & set(
        [str(role.id) for role in member.roles]):  # if the mentioned member already having prisoner role.
      embed = discord.Embed(title='Already suffering',
                            description=f"{member.mention} is already suffering in <#{database.get_config('prison', ctx.guild.id)[0]}>",
                            color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    is_escaped = database.is_escaped(member.id, ctx.guild.id)
    if is_escaped is not None:  # if the member is under gem cooldown or 30 mins cooldown.
      if is_escaped[3] == 'gem':
        embed = discord.Embed(title='Magic Gem is Real',
                              description=f"{member.mention} used the power of Magic Gem💎 "
                                          f"to be free, Magic Gem's Power will deteriorate <t:{is_escaped[2] + 60}:R>.\n> *patience is a virtue*",
                              color=0xF47FFF)
      elif is_escaped[3] == 'cooldown':
        embed = discord.Embed(title='Cooldown',
                              description=f'{ctx.author.mention} you can lock {member.mention} <t:{is_escaped[2]}:R>',
                              color=0xF47FFF)
      await ctx.reply(embed=embed)
      return

    member_is = who_is(ctx.author, member)  # checking relationship between author and member

    if member_is in [201, 200] or member_is > 300:
      def check(res):
        return ctx.author == res.user and res.channel == ctx.channel

      if member_is != 200:
        if not database.get_money(ctx.author.id, ctx.guild.id)[3] > 0:  # checking if author has gems
          no_gem_embed = discord.Embed(title='No Gems',
                                       description=f"{ctx.author.mention} you don't have gems to lock {member.mention}",
                                       color=0xF2A2C0)
          await ctx.reply(embed=no_gem_embed)
          return

      prison = ctx.guild.get_channel(int(database.get_config('prison', ctx.guild.id)[0]))
      prisoner = ctx.guild.get_role(int(database.get_config('prisoner', ctx.guild.id)[0]))

      print(f'{prison=} {prisoner=}')

      if prisoner is None:  # if prisoner role is deleted makes a new prisoner role and configures it
        prisoner = await ctx.guild.create_role(name='Prisoner', color=0x591B32)
        database.insert_config('prisoner', ctx.guild.id, prisoner.id)
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
          if channel.id == prison.id:
            continue
          await channel.set_permissions(prisoner, view_channel=False, send_messages=False)

        await prison.set_permissions(prisoner, view_channel=True, send_messages=True, read_message_history=True)
        print(f'fix {prison}')

      em = discord.Embed(title='What should this slave do while they are in prison?', color=0x9479ED)
      await ctx.send(embed=em, view=LockActionView(ctx, member, member_is))

  @commands.hybrid_command()
  @commands.guild_only()
  async def unlock(self, ctx, member: discord.Member):
    """
    unlock command unlocks prisoner and sets them free
    """
    if ctx.author.bot:  # returns if the author is a bot
      return

    sroles = [str(role.id) for role in member.roles]
    prrole = database.get_config('prisoner', ctx.guild.id)[0]

    if prrole not in sroles or member.bot:
      print('already free here')
      embed = discord.Embed(title='Already Free', description=f"{member.mention} is already in woods enjoying the sun.",
                            color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    member_is = who_is(ctx.author, member)
    prisoner = ctx.guild.get_role(int(database.get_config('prisoner', ctx.guild.id)[0]))

    if member_is < -1:  # if author is bot banned
      embed = discord.Embed(
        description=f"{ctx.author.mention} you are banned from {self.bot.user.display_name} till <t:{-1 * member_is}:F>",
        color=0xF2A2C0)
      await ctx.reply(embed=embed)

    elif member_is in [2, 202]:  # when locker is self unlocking or unlocking a locker.
      embed = discord.Embed(
        description=f"{member.mention} is free in Woods enjoying the sun, nobody can lock the Domme.", color=0xF2A2C0)
      await ctx.reply(embed=embed)

    elif member_is in [222] or ctx.author.guild_permissions.administrator:  # locker/admin unlocking a slave
      domme = database.get_prisoner(member.id, ctx.guild.id)[2]
      if ctx.author.id == int(domme) or ctx.author.guild_permissions.administrator:
        await member.remove_roles(prisoner)

        await member.add_roles(ctx.guild.get_role(int(database.get_config('slave', member.guild.id)[0])))

        embed = discord.Embed(description=f'{member.mention} is free now, released by {ctx.author.mention}',
                              color=0xF2A2C0)
        await ctx.reply(embed=embed)
      else:
        embed = discord.Embed(title='Nah', description=f"Only <@{domme}> or the Admins can set {member.mention} free.",
                              color=0xF2A2C0)
        await ctx.reply(embed=embed)

    else:
      unlock_slave_embed = discord.Embed(title='Pathetic…',
                                         description=f"you are not worthy to use this command.",
                                         color=0xF2A2C0)
      await ctx.reply(embed=unlock_slave_embed)

  @commands.hybrid_command()
  @commands.guild_only()
  async def escape(self, ctx):
    """
    this command will enable prisoner to escape from prison and grand 6h of protection.
    """
    if ctx.author.bot:
      return

    is_prisoner = discord.utils.get(ctx.author.roles, name='Prisoner')

    if not is_prisoner:  # if author does not have prisoner role
      print('already freee there')
      embed = discord.Embed(title='Already Free',
                            description=f"{ctx.author.mention} is already in woods enjoying the sun.", color=0xF2A2C0)
      await ctx.reply(embed=embed)
      return

    if database.get_money(ctx.author.id, ctx.guild.id)[
      3] != 0 or ctx.author.id == 104373103802466304:  # if prisoner have gems
      if ctx.author.id != 0:
        database.remove_money(ctx.author.id, ctx.guild.id, 0, 10)
      prisoner = ctx.guild.get_role(int(database.get_config('prisoner', ctx.guild.id)[0]))
      await ctx.author.remove_roles(prisoner)
      embed = discord.Embed(
        description=f"{ctx.author.mention} was lucky to have a magic gem 💎 and escaped from {ctx.channel.mention}",
        color=0xF2A2C0)
      await ctx.send(embed=embed)
      database.insert_escape(ctx.author.id, ctx.guild.id, 1, 'gem')
    else:  # if prisoner does not have a gem
      embed = discord.Embed(
        description=f"{ctx.author.mention} you don't have magic gem 💎 to be free.",
        color=0xF2A2C0)
      await ctx.reply(embed=embed)

  ##############################################################################
  #                                                                            #
  #                                                                            #
  #                                  ERRORS                                    #
  #                                                                            #
  #                                                                            #
  ##############################################################################

  @lock.error
  async def on_lock_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(title='How to use Prison?', description=f"Usage:\n> **`/lock @mention`** "
                                                                    f"\nAfter it just enjoy the slave punishment!",
                            color=0xFF2030)
      await ctx.send(embed=embed)

    elif isinstance(error, commands.errors.CommandOnCooldown):
      embed = discord.Embed(title="Prison Cooldown is 3h",
                            description="{} you need to wait {:,.1f} minutes to lock a slave again.".format(
                              ctx.author.mention, (error.retry_after // 60) + 1),
                            color=0xFF2030)
      await ctx.send(embed=embed)
    else:
      raise error

  @unlock.error
  async def on_unlock_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(
        error, commands.MemberNotFound):
      embed = discord.Embed(title='How to save a slave from Prison?', description=f"Usage:\n> **`t.unlock @mention`** ",
                            color=0xFF2030)
      await ctx.send(embed=embed)

    raise error


async def setup(bot):
  await bot.add_cog(Lock(bot))
