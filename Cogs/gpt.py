import json
import time
import traceback

import discord
from discord import app_commands
from discord.ext import commands

personas = [
  app_commands.Choice(name="Mister Dominic", value="mister"),
  app_commands.Choice(name="Switch Dominic", value="switch-mister"),
  app_commands.Choice(name="Mistress Valentina", value="miss"),
  app_commands.Choice(name="Switch Valentina", value="switch-miss"),
  app_commands.Choice(name="Custom", value="custom")
]


# prompt engineering
async def switch_persona(persona, client, raw=False, bring_back=False) -> None:
  if not raw:
    contents = client.PERSONAS.get(persona)
  else:
    contents = persona

  if client.chat_model == "UNOFFICIAL":
    client.chatbot.reset_chat()
    async for _ in client.chatbot.ask(contents):
      pass
  elif client.chat_model == "OFFICIAL":

    if bring_back:
      return client.get_chatbot_model(prompt=contents)
    else:
      client.chatbot = client.get_chatbot_model(prompt=contents)


  elif client.chat_model == "Bard":
    client.chatbot = client.get_chatbot_model()
    await sync_to_async(client.chatbot.ask)(contents)
  elif client.chat_model == "Bing":
    await client.chatbot.reset()
    async for _ in client.chatbot.ask_stream(contents):
      pass


class Gpt(commands.Cog):
  """GPT in your server, acting with a special persona."""
  def __init__(self, bot):
    self.bot = bot

  @commands.hybrid_command()
  async def private(self, it: discord.Interaction):
    """Toggle private access"""

    if it.author.id not in self.bot.privates:
      self.bot.privates.append(it.author.id)

      await it.send(
        "> **INFO: Next, the response will be sent so that only you can see it. If you want to switch back to public mode, use `/public`**")
    else:
      await it.send(
        "> **WARN: You already on private mode. If you want to switch to public mode, use `/public`**")

  @commands.hybrid_command()
  async def public(self, it: discord.Interaction):
    """Toggle public access"""

    if it.author.id in self.bot.privates:
      self.bot.privates.remove(it.author.id)
      await it.send(
        "> **INFO: Next, the response will be sent so that everyone can see them. If you want to switch back to private mode, use `/private`**")
    else:
      await it.send(
        "> **WARN: You already on public mode. If you want to switch to private mode, use `/private`**")


  @commands.hybrid_command()
  @app_commands.choices(persona=personas)
  async def groupchat(self, it: discord.Interaction, persona: app_commands.Choice[str]):
    """Create a thread for anyone to chat with the bot"""

    # create a thread

    persona = persona.value

    thread = await it.channel.create_thread(
      name=f'groupchat-{persona}',
      type=discord.ChannelType.public_thread,
      auto_archive_duration=60,
      reason="Group chat"
    )

    await thread.send(f"> **INFO: Group chat started! Use `/chat <message>` to chat with the bot.**")

    self.bot.groupchat_personas[str(thread.id)] = {
      "client": await switch_persona(persona, self.bot, bring_back=True),
      "last_req": time.time()
    }

    await it.send(f"<:yes:1184312448912732180> enjoy the groupchat in {thread.mention}")

  @app_commands.command()
  async def chat(self, it: discord.Interaction, *, message: str):
    """Have a chat with ChatGPT"""


    await it.response.defer(ephemeral=it.user.id in self.bot.privates)

    self.bot.has_job = True
    await self.bot.enqueue_message(it, message)

  @app_commands.command(name="switchpersona", description="Switch between optional chatGPT jailbreaks")
  @app_commands.choices(persona=personas)
  async def switchpersona(self, it: discord.Interaction, persona: app_commands.Choice[str]):
    if it.author == self.bot.user:
      return

    await it.response.defer(thinking=True)
    username = str(it.author)
    channel = str(it.channel)

    persona = persona.value

    if persona == self.bot.current_persona:
      await it.followup.send(f"> **WARN: Already set to `{persona}` persona**")

    elif persona == "custom":
      if str(it.guild.id) not in self.bot.custom_personas:
        return await it.followup.send(
          "> ❌ **ERROR: No custom persona set for this server!** Admins can set one using `/custompersona <prompt file>`")

      await switch_persona(str(self.bot.custom_personas[str(it.guild.id)]), self.bot, raw=True)
      return await it.followup.send(f"> **INFO: Switched to `custom` persona**")

    elif persona == "standard":
      if self.bot.chat_model == "OFFICIAL":
        self.bot.chatbot.reset(convo_id=str(it.author.id))
      elif self.bot.chat_model == "UNOFFICIAL":
        self.bot.chatbot.reset_chat()
      elif self.bot.chat_model == "Bard":
        self.bot.chatbot = self.bot.get_chatbot_model()
      elif self.bot.chat_model == "Bing":
        self.bot.chatbot = self.bot.get_chatbot_model()

      self.bot.current_persona = "standard"
      await it.followup.send(
        f"> **INFO: Switched to `{persona}` persona**")

    elif persona == "random":
      choices = list(self.bot.PERSONAS.keys())
      choice = randrange(0, 6)
      chosen_persona = choices[choice]
      self.bot.current_persona = chosen_persona
      await switch_persona(chosen_persona, self.bot)
      await it.followup.send(
        f"> **INFO: Switched to `{chosen_persona}` persona**")


    elif persona in self.bot.PERSONAS:
      try:
        await switch_persona(persona, self.bot)
        self.bot.current_persona = persona
        await it.followup.send(
          f"> **INFO: Switched to `{persona}` persona**")
      except Exception as e:
        await it.followup.send(
          "> **ERROR: Something went wrong, please try again later! 😿**")

        traceback.print_exc()

    else:
      await it.followup.send(
        f"> **ERROR: No available persona: `{persona}` 😿**")

  @commands.hybrid_command()
  @app_commands.checks.has_permissions(administrator=True)
  @app_commands.describe(persona_file="A text file with the persona prompt")
  async def custompersona(self, it: discord.Interaction, persona_file: discord.Attachment):
    """
    Set a custom persona that can be changed to using /switchpersona custom
    """

    # is it a text file?
    if "text/plain" not in persona_file.content_type:
      return await it.response.send_message("> ❌ **ERROR: The file must be a text file!**")

    # max
    if persona_file.size > 1000000:
      return await it.response.send_message("> ❌ **ERROR: That file is too big!! What did you put in there?**")

      # is it empty?
      if persona_file.size == 0:
        return await it.response.send_message("> ❌ **ERROR: The file must not be empty!**")

    try:
      content = (await persona_file.read()).decode("utf-8")
    except UnicodeDecodeError:
      return await it.response.send_message("> ❌ **ERROR: Is this really a text file?**")

    if len(content) > 5000:
      return await it.response.send_message("> ❌ **ERROR: Prompt should be around 500 words (max 5000 chars)**")

    # put it
    self.bot.custom_personas[str(it.guild.id)] = content

    with open("custom_personas.json", "w") as f:
      print('setting', self.bot.custom_personas)
      json.dump(self.bot.custom_personas, f, indent=2)

    await it.response.send_message("> ✅ **SUCCESS: Custom persona set!** Use `/switchpersona Custom` to use it.")


async def setup(bot):
  await bot.add_cog(Gpt(bot))
