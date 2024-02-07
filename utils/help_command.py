import itertools

import starlight
import discord
from discord.ext import commands
from discord.ext.commands import Command as Cmd


class CustomHelp(starlight.MenuHelpCommand):
  def __init__(self, *args, **kwargs):
    super().__init__(
      per_page=5,
      accent_color=0x907fe9,
      error_color=discord.Color.dark_red(),
      inline_fields=False,
      no_category='Other',
      no_documentation='',
      with_app_command=True,
    )

  async def format_bot_page(self, view: starlight.HelpMenuBot, mapping):
    title = "💜 Valentina Usage"
    if view.max_pages > 1:
      title += f" ({view.current_page + 1}/{view.max_pages})"

    embed = discord.Embed(
      title=title,
      description=self.context.bot.description if view.current_page == 0 else None,
      color=self.accent_color
    )
    embed.set_footer(text='💗 Show your love to me by Donating here - https://ko-fi.com/kyrian',
                     icon_url=self.context.bot.user.display_avatar.url)

    data = [(cog, cmds) for cog, cmds in mapping.items()]
    data.sort(key=lambda d: self.resolve_cog_name(d[0]))
    for cog, cmds in data:
      name_resolved = self.resolve_cog_name(cog)
      value = getattr(cog, "description", None) or self.no_documentation
      name = f"{name_resolved} (`{len(cmds)}`)"
      embed.add_field(name=name, value=value, inline=self.inline_fields)

    return embed

  async def format_group_detail(self, view: starlight.HelpMenuGroup):
    group = view.group
    subcommands = "\n".join([self.format_command_brief(cmd) for cmd in group.commands])
    group_description = self.get_command_description(group) or self.no_documentation

    if isinstance(group, commands.Group) and group.aliases:
      group_description += f"\n\n**Aliases**\n{', '.join(group.aliases)}"

    if isinstance(group, commands.HybridGroup):
      group_description += f"\n\n*Slash command available.*"

    description = group_description + (f"\n\n**Subcommands**\n{subcommands}" if subcommands else "")

    em = discord.Embed(
      title=self.get_command_signature(group),
      description=description,
      color=self.accent_color
    )

    em.set_footer(text='💗 Show your love to me by Donating here - https://ko-fi.com/kyrian',
                  icon_url=self.context.bot.user.display_avatar.url)

    return em

  async def format_command_detail(self, view: starlight.HelpMenuCommand):
    cmd = view.command
    desc = self.get_command_description(cmd) or self.no_documentation
    if isinstance(cmd, commands.Command) and cmd.aliases:
      desc += f"\n\n**Aliases**\n{', '.join(cmd.aliases)}"

    em = discord.Embed(
      title=self.get_command_signature(cmd),
      description=desc,
      color=self.accent_color
    )
    em.set_footer(text='💗 Show your love to me by Donating here - https://ko-fi.com/kyrian',
                  icon_url=self.context.bot.user.display_avatar.url)

    return em

  async def format_cog_page(self, view: starlight.HelpMenuCog, cmds):
    title = f"{self.resolve_cog_name(view.cog)} ({view.current_page + 1}/{view.max_pages})"
    desc = ""
    if view.current_page == 0:
      desc = getattr(view.cog, "description", None) or self.no_documentation
      all_cmds = [*itertools.chain.from_iterable(view.data_source)]
      desc += f"\n\n**Commands[`{len(all_cmds)}`]**\n"

    list_cmds = "\n".join([self.format_command_brief(cmd).strip() for cmd in cmds])
    em = discord.Embed(
      title=title,
      description=f"{desc}{list_cmds}",
      color=self.accent_color
    )

    em.set_footer(text='💗 Show your love to me by Donating here - https://ko-fi.com/kyrian',
                  icon_url=self.context.bot.user.display_avatar.url)
    return em

  def get_command_signature(self, command):
    signature = ' '
    if isinstance(command, commands.Command):
      signature += command.signature
    elif isinstance(command, discord.app_commands.Group):
      signature = ''
    else:
      signature += starlight.get_app_signature(command)

    prfx = '/'
    return f'{prfx}{command.qualified_name}{signature}'

  async def filter_commands(self, commands, sort=False, key=None):
    if sort and key is None:
      key = lambda c: c.name

    iterator = commands if self.show_hidden else filter(lambda c: not getattr(c, 'hidden', None), commands)

    if self.verify_checks is False:
      # if we do not need to verify the checks then we can just
      # run it straight through normally without using await.
      return sorted(iterator, key=key) if sort else list(iterator)  # type: ignore # the key shouldn't be None

    if self.verify_checks is None and not self.context.guild:
      # if verify_checks is None and we're in a DM, don't verify
      return sorted(iterator, key=key) if sort else list(iterator)  # type: ignore

    # if we're here then we need to check every command if it can run
    async def predicate(cmd) -> bool:
      ctx = self.context
      if isinstance(cmd, Cmd):
        try:
          return await cmd.can_run(ctx)
        except (
            discord.ext.commands.CommandError,
            discord.ext.commands.HybridCommandError,
          discord.app_commands.BotMissingPermissions
        ):
          return False

      no_interaction = ctx.interaction is None
      if not cmd.checks and no_interaction:
        binding = cmd.binding
        if cmd.parent is not None and cmd.parent is not binding:
          return False  # it has group command interaction check

        if binding is not None:
          check = getattr(binding, 'interaction_check', None)
          if check:
            return False  # it has cog interaction check

        return True

      if no_interaction:
        return False

      try:
        return await cmd._check_can_run(ctx.interaction)
      except app_commands.AppCommandError:
        return False

    ret = []
    for cmd in iterator:
      valid = await predicate(cmd)
      if valid:
        ret.append(cmd)

    if sort:
      ret.sort(key=key)
    return ret
