from telethon import events, utils, types
import traceback
import re
import os.path
import inspect
import functools
import asyncio
from typing import Union, Any, Callable
import logging

import config
from util.data import MessageData


logger = logging.getLogger('mtgbot.plugin')


class Scope(object):
  def __init__(self, type=None, chat_id=None, user_id=None):
    """
    一般情况下请用静态方法创建
    """
    if type is None:
      type = types.BotCommandScopeDefault
    self.type = type
    self.chat_id = chat_id
    self.user_id = user_id
    # 缓存的 InputPeer
    self._chat_id = None
    self._user_id = None

  def __hash__(self):
    return hash((hash(self.type), self.chat_id, self.user_id))

  def __eq__(self, other):
    return hash(self) == hash(other)

  def __str__(self):
    return f'Scope(type=types.{self.type.__name__}, chat_id={self.chat_id}, user_id={self.user_id})'

  def __repr__(self):
    return self.__str__()

  async def to_command_scope(self):
    if self.chat_id is None:
      return self.type()
    if self._chat_id is None:
      self._chat_id = await bot.get_input_entity(self.chat_id)
    if self.user_id is not None:
      if self._user_id is None:
        self._user_id = await bot.get_input_entity(self.user_id)
      return self.type(self._chat_id, self._user_id)
    return self.type(self._chat_id)

  @staticmethod
  @functools.cache
  def all():
    """
    默认范围，全部
    """
    return Scope(types.BotCommandScopeDefault)

  @staticmethod
  @functools.cache
  def private():
    """
    所有私聊
    """
    return Scope(types.BotCommandScopeUsers)

  @staticmethod
  @functools.cache
  def chat(chat_id):
    """
    给定 chat_id 指代的群聊/频道
    或给定 chat_id 的用户私聊
    """
    return Scope(types.BotCommandScopePeer, chat_id)

  @staticmethod
  @functools.cache
  def user(chat_id):
    """
    给定 chat_id 的用户 (不管群聊私聊)
    """
    return ScopeList(
      Scope.chat(chat_id),
      *(Scope.chats(i, chat_id) for i in MessageData.iter_chats() if i < 0),
    )

  @staticmethod
  @functools.cache
  def chats(chat_id=None, user_id=None):
    """
    所有群聊和频道;
    或给定 chat_id 指代的群聊/频道/用户;
    或给定 chat_id 指代的群聊/频道中特定的 user_id 指代的用户
    """
    if chat_id and user_id:
      return Scope(types.BotCommandScopePeerUser, chat_id, user_id)
    if chat_id:
      return Scope.chat(chat_id)
    return Scope(types.BotCommandScopeChats)

  @staticmethod
  @functools.cache
  def chat_admins(chat_id=None):
    """
    所有群聊和频道的管理员;
    或给定 chat_id 指代的群聊/频道的管理员
    """
    if chat_id:
      return Scope(types.BotCommandScopePeerAdmins, chat_id)
    return Scope(types.BotCommandScopeChatAdmins)

  @staticmethod
  @functools.cache
  def superadmin():
    """
    所有superadmin (请在 .env 中配置 superadmin 项, 可以为一个数字或以半角逗号 "," 隔开的id列表)
    """
    return ScopeList([Scope.user(i) for i in config.superadmin])


class ScopeList(list):
  def append(self, value):
    if utils.is_list_like(value):
      for i in value:
        self.append(i)
      return
    if not isinstance(value, Scope):
      raise ValueError("ScopeList's values must ALL be Scope or list[Scope]")
    super().append(value)

  def __init__(self, *args):
    def _append(value):
      nonlocal items
      if utils.is_list_like(value):
        for i in value:
          _append(i)
        return
      if not isinstance(value, Scope):
        raise ValueError("ScopeList's values must be ALL a Scope")
      items.append(value)

    items = []
    for i in args:
      _append(i)
    super().__init__(items)

  def __repr__(self):
    return 'ScopeList(' + super().__repr__() + ')'


async def get_event_info(event):
  sender = await event.get_sender()
  name = getattr(sender, 'first_name', None) or getattr(sender, 'title', None)
  if t := getattr(sender, 'last_name', None):
    name += ' ' + t

  if event.chat_id == event.sender_id:
    info = f'在私聊 {name}({sender.id}) 中被触发'
  else:
    chat = await event.get_chat()
    chatname = getattr(chat, 'first_name', None) or getattr(chat, 'title', None)
    if t := getattr(chat, 'last_name', None):
      chatname += ' ' + t
    info = f'在群组 "{chatname}"({event.chat_id}) 中被 "{name}"({event.sender_id}) 触发'
  return info


class Command:
  def __init__(
    self,
    cmd: str = '',
    *,
    pattern: Union[str, re.Pattern, callable] = None,
    enable: Union[Callable[[], bool], Any] = True,
    info: str = '',  # BotCommand 中的描述信息
    scope: Union[ScopeList, Scope] = None,  # BotCommand 显示的范围
    show_info: Union[bool, callable, Any] = True,
    filter: Any = None,
    **kwargs,
  ):
    if cmd == '':
      self.pattern_cmd = True
    else:
      self.pattern_cmd = False

    self.cmd = cmd
    if pattern is None and self.cmd:
      pattern = r'^/' + self.cmd + '.*'
    if isinstance(pattern, str):
      pattern = re.compile(pattern).match
    elif isinstance(pattern, re.Pattern):
      pattern = pattern.match
    self.pattern = pattern
    self.info = info
    self.show_info = show_info
    self.enable = enable
    if hasattr(filter, 'filter'):
      filter = filter.filter
    self.filter = filter
    kwargs['func'] = self.filter

    if scope is None:
      scope = ScopeList(Scope())
    elif isinstance(scope, Scope):
      scope = ScopeList(scope)
    elif not isinstance(scope, ScopeList):
      raise ValueError(
        'The parameter "scope" must be a plugin.Scope instance or a plugin.ScopeList instance'
      )
    self.scope = scope
    self.kwargs = kwargs

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    return (
      'Command('
      + ', '.join(
        f'{k}={v}'
        for k in ['cmd', 'func', 'pattern', 'info', 'desc', 'scope', 'kwargs']
        if (v := getattr(self, k, None)) is not None
      )
      + ')'
    )

  def __call__(self, func):
    if self.cmd == '':
      self.cmd = f'pattern_cmd<{func.__module__}:{func.__qualname__}>'
    config.commands.append(self)

    @functools.wraps(func)
    async def _func(event, *args, **kwargs):
      event.cmd = self
      _args = inspect.signature(func).parameters
      if 'text' in _args:
        text = ''
        if len(args) > 0:
          args = list(args)
          text = args.pop(0)
        if (
          not text
          and getattr(event, 'message', None)
          and getattr(event.message, 'message', None)
        ):
          text = event.message.message
        if text:
          text = re.sub(
            r'^/(%s|start)(@%s)?' % (self.cmd, bot.me.username), '', text
          ).strip()
        args = [text] + list(args)

      info = await get_event_info(event)
      if not self.pattern_cmd:
        logger.info(f'命令 "{self.cmd}" ' + info)

      try:
        res = await func(event, *args, **kwargs)
      except asyncio.CancelledError as e:
        logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 被取消')
        raise e
      except events.StopPropagation:
        raise
      except Exception:
        logger.error(
          f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 异常结束'
          + (f' ({info})' if self.pattern_cmd else ''),
          exc_info=1,
        )
      else:
        if not self.pattern_cmd:
          logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 运行结束')
      return res

    self.func = _func
    return self.func


class InlineCommand:
  def __init__(
    self,
    pattern: Union[str, re.Pattern, callable] = None,
  ):
    if not callable(pattern):
      if isinstance(pattern, re.Pattern):
        pattern = pattern.match
      else:
        pattern = re.compile(pattern).match
    self.pattern = pattern

  def __repr__(self):
    return (
      'InlineCommand('
      + ', '.join(
        f'{k}={v}' for k in ['pattern', 'func'] if (v := getattr(self, k, None))
      )
      + ')'
    )

  def __call__(self, func):
    config.inlines.append(self)
    self.func = func
    return self.func


handler = Command
inline_handler = InlineCommand


class Setting:
  def __init__(
    self,
    text: str,
  ):
    self.text = text
    self.data = b'setting_' + text.encode()
    self.pattern = re.compile(b'^' + self.data + b'$').match

  def __repr__(self):
    return f'Setting(func={self.func})'

  def __call__(self, func):
    config.settings.append(self)
    self.func = func
    config.bot.add_event_handler(self.func, events.CallbackQuery(pattern=self.pattern))
    return self.func


load_logger = logging.getLogger('mtgbot.plugin.load')


def load_plugin(name):
  try:
    __import__(name, fromlist=[])
    load_logger.info(f'Success to load plugin "{name}"')
  except Exception:
    load_logger.warning('Error to load plugin "' + name + '"')
    load_logger.warning(traceback.format_exc())


def load_plugins():
  dirpath = os.path.join(config.botRoot, 'plugins')
  for name in os.listdir(dirpath):
    path = os.path.join(dirpath, name)
    if os.path.isfile(path) and (name.startswith('_') or not name.endswith('.py')):
      continue
    if os.path.isdir(path) and (
      name.startswith('_') or not os.path.exists(os.path.join(path, '__init__.py'))
    ):
      continue
    m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
    if not m:
      continue
    load_plugin(f'{config.bot_home+"." if config.bot_home else ""}plugins.{m.group(1)}')
