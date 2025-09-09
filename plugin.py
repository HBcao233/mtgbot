from telethon import events, utils, types
from typing import Union, Any, Callable
import re
import os.path
import inspect
import functools
import asyncio
import logging
import importlib

import config
import filters
from util.data import MessageData


logger = logging.getLogger('mtgbot.plugin')


class Scope(object):
  """
  命令显示范围

  一般情况下请用静态方法创建
  """

  def __init__(self, type=None, chat_id=None, user_id=None):
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
    """
    Scope 转 BotCommandScope
    """
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
    return ScopeList([Scope.chat(i) for i in config.superadmin])


class ScopeList(list):
  """
  命令范围列表
  """

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
  """
  event chat info

  :meta private:
  """

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
  """
  命令装饰器

  定制化的 bot.on(events.NewMessage()) 装饰器

  Arguments
    cmd (`str`):
      命令名称

    pattern (`str` | `re.Pattern` | `callable`):
      正则表达式

      默认值: re.compile(r'^/' + self.cmd + '( .*)?$').match

    enable (`callable` | `bool`):
      是否启用

    info (`str`):
      命令描述消息, 不为空则会在命令列表中显示

    scope (`ScopeList` | `Scope`):
      命令描述显示范围

    show_info (`bool` | `callable`):
      是否显示命令描述

    filter (`filters.Filter` | `Any`):
      过滤器, 需为 一个实现了filter方法的任意对象,

      建议使用 `filters <filters.html>`_ 中的内置的 `Filter <filters.html#filters.Filter>`_ 类实例化
  """

  def __init__(
    self,
    cmd: str = '',
    *,
    pattern: Union[str, re.Pattern, callable] = None,
    enable: Union[Callable[[], bool], Any] = True,
    info: str = '',  # BotCommand 中的描述信息
    scope: Union[ScopeList, Scope] = None,  # BotCommand 显示的范围
    show_info: Union[bool, callable, Any] = True,
    filter: Union[filters.Filter, Any] = None,
    **kwargs,
  ):
    if cmd == '':
      self.pattern_cmd: bool = True
    else:
      self.pattern_cmd: bool = False

    self.cmd: str = cmd
    if pattern is None and self.cmd:
      pattern = (
        r'^/'
        + re.escape(self.cmd)
        + '(@'
        + re.escape(config.bot.me.username)
        + r')?( [^\x00]*?)?$'
      )
    if isinstance(pattern, str):
      pattern = re.compile(pattern).match
    elif isinstance(pattern, re.Pattern):
      pattern = pattern.match
    self.pattern: callable = pattern
    self.info: str = info
    self.show_info: Any = show_info
    self.enable: Any = enable
    if hasattr(filter, 'filter'):
      filter = filter.filter
    self.filter: Any = filter
    kwargs['func'] = self.filter

    if scope is None:
      scope = ScopeList(Scope())
    elif isinstance(scope, Scope):
      scope = ScopeList(scope)
    elif not isinstance(scope, ScopeList):
      raise ValueError(
        'The parameter "scope" must be a plugin.Scope instance or a plugin.ScopeList instance'
      )
    self.scope: ScopeList = scope
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
      except asyncio.CancelledError:
        logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 被取消')
        raise
      except events.StopPropagation:
        if not self.pattern_cmd:
          logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 运行结束')
        raise
      except Exception:
        logger.error(
          f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 异常结束'
          + (f' ({info})' if self.pattern_cmd else ''),
          exc_info=1,
        )
        return
      else:
        if not self.pattern_cmd:
          logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 运行结束')
      return res

    self.func = _func
    return self.func


class InlineCommand:
  """
  内联命令装饰器

  定制化的 bot.on(events.InlineQuery() 装饰器

  Arguments
    pattern (`str` | `re.Pattern` | `callable`):
      正则表达式

      默认值: None (匹配全部)
  """

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


#: Command 别名
command_handler = Command
#: Command 别名
handler = Command
#: InlineCommand 别名
inline_handler = InlineCommand


class Setting:
  """
  设置按钮装饰器

  定制化的 bot.on(events.CallbackQuery()) 装饰器

  Arguments
    text (`str`):
      按钮文本
  """

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
modules = {}


def load_plugin(name):
  """
  加载指定名称的插件
  一般不在插件开发中使用, 导入插件请使用 `import_plugin`

  :meta private:
  """
  try:
    module = importlib.import_module(name)
    modules[name] = module
    load_logger.info(f'Success to load plugin "{name}"')
  except Exception:
    load_logger.error('Error to load plugin "' + name + '"', exc_info=1)


def load_plugins():
  """
  加载所有插件
  一般不在插件开发中使用

  :meta private:
  """
  dirpath = os.path.join(config.botHome, 'plugins')
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
    load_plugin(
      f'{config.bot_home + "." if config.bot_home else ""}plugins.{m.group(1)}'
    )


def reload_plugin(module):
  """
  重新加载插件
  一般不在插件开发中使用

  :meta private:
  """
  try:
    importlib.reload(module)
    load_logger.info(f'Success to reload plugin "{module.__name__}"')
  except ModuleNotFoundError:
    try:
      del modules[module.__name__]
    except KeyError:
      pass
    load_logger.error(f'Error to reload plugin "{module.__name__}": Module Not Found.')
  except Exception:
    load_logger.error(f'Error to reload plugin "{module.__name__}"', exc_info=1)


def reload_plugins():
  """
  重新加载所有插件
  一般不在插件开发中使用

  :meta private:
  """
  for i in list(modules.values()):
    reload_plugin(i)

  # 检测有无新增插件
  dirpath = os.path.join(config.botHome, 'plugins')
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
    if os.path.isdir(path):
      for i in os.listdir(path):
        if i.endswith('.py') and i != '__init__.py':
          mo = None
          try:
            name = f'{config.bot_home + "." if config.bot_home else ""}plugins.{m.group(1)}.{i.replace(".py", "")}'
            mo = importlib.import_module(name)
            importlib.reload(mo)
            load_logger.info(f'Success to reload plugin "{mo.__name__}"')
          except ModuleNotFoundError:
            load_logger.error(
              f'Error to reload plugin "{mo.__name__ if mo else name}"', exc_info=1
            )

    name = f'{config.bot_home + "." if config.bot_home else ""}plugins.{m.group(1)}'
    if name in modules.keys():
      continue
    load_plugin(name)


def import_plugin(name):
  """
  导入插件

  Arguments
    name (`str`):
      插件名, 去掉plugins.前缀, 及 .py 后缀的文件名或文件夹名
  """
  try:
    return __import__(
      f'{config.bot_home + "." if config.bot_home else ""}plugins.{name}',
      fromlist=[name],
    )
  except Exception:
    load_logger.error('Error to import plugin "' + name + '"', exc_info=1)
