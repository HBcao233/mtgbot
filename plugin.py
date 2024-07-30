import traceback
import re
import os.path
import inspect
import functools

import config
from util.log import logger
from telethon import events


class Command:
  def __init__(
    self, cmd, *,
    pattern=None,
    info="", # BotCommand 中的描述信息
    desc="", # 当 text 为空是返回的详细信息
    scope="",
    **kwargs,
  ):
    self.cmd = cmd
    if pattern is None:
      pattern = r'^/' + self.cmd + '.*'
    self.pattern = pattern
    self.info = info
    self.desc = desc
    self.scope = scope
    self.kwargs = {k:v for k, v in kwargs.items() if k in ['incoming', 'outgoing', 'from_users', 'forwards', 'chats', 'blacklist_chats', 'func']}
    
  def __str__(self):
    return 'Command(' + ', '.join(f'{k}={v}' for k in ['cmd', 'func', 'pattern', 'info', 'desc', 'scope', 'kwargs'] if (v := getattr(self, cmd, None)) is not None) + ')'
    
  def __repr__(self):
    return self.__str__()
    
  def __call__(self, func):
    config.commands.append(self)
    
    @functools.wraps(func)
    async def _func(event, *args, **kwargs):
      event.cmd = self
      _args = inspect.signature(func).parameters
      if 'text' not in _args:
        return await func(event, *args, **kwargs)
      text = ''
      if event.message.message:
        text = (
          event.message.message
            .lstrip('/' + self.cmd)
            .lstrip("@" + config.bot.me.username)
            .lstrip("/start")
            .lstrip(self.cmd)
            .strip()
        )
      if not text and self.desc:
        return await event.reply(self.desc)
      return await func(event, text, *args, **kwargs)
    
    self.func = _func
    config.bot.add_event_handler(self.func, events.NewMessage(pattern=self.pattern, **self.kwargs))
    return self.func
    
  
handler = Command

  
def load_plugin(name):
  try:
    __import__(name, fromlist=[])
    logger.info('Success to load plugin "' + name + '"')
  except Exception:
    logger.warning('Error to load plugin "' + name + '"')
    logger.warning(traceback.format_exc())
  
  
def load_plugins():
  dirpath = os.path.join(config.botRoot, 'plugins')
  for name in os.listdir(dirpath):
    path = os.path.join(dirpath, name)
    if os.path.isfile(path) and \
       (name.startswith('_') or not name.endswith('.py')):
      continue
    if os.path.isdir(path) and \
       (name.startswith('_') or 
        not os.path.exists(os.path.join(path, '__init__.py'))):
      continue
    m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
    if not m:
      continue
    load_plugin(f'{config.bot_home+"." if config.bot_home else ""}plugins.{m.group(1)}')
        