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
    self, cmd, func, *,
    pattern=None,
    info="", # BotCommand 中的描述信息
    desc="", # 当 text 为空是返回的详细信息
    scope="",
    **kwargs,
  ):
    self.cmd = cmd
    self.func = func
    self.pattern = pattern
    self.info = info
    self.desc = desc
    self.scope = scope
  
  def __str__(self):
    res = f'Command(cmd={self.cmd}, func={self.func}'
    if self.pattern is not None:
      res += f', pattern={self.pattern}'
    return res + ')'


def handler(cmd, pattern=None, **kwargs):
  if pattern is None:
    pattern = r'^/'+cmd+'.*'
  def deco(func):
    @functools.wraps(func)
    async def _func(event, text=None, *_args, **_kwargs):
      event.cmd = Command(cmd, _func, **kwargs)
      args = inspect.signature(func).parameters
      if 'text' not in args:
        return await func(event, *_args, **_kwargs)
      if text is None and event.message.message:
        text = (
          event.message.message
            .lstrip('/' + cmd)
            .lstrip("@" + config.bot.me.username)
            .lstrip("/start")
            .lstrip(cmd)
            .strip()
        )
      if not text and kwargs.get('desc', ''):
        return await event.reply(desc)
      return await func(event, text, *_args, **_kwargs)
    config.commands.append(Command(cmd, _func, **kwargs))
    kw = {k:v for k, v in kwargs.items() if k in ['incoming', 'outgoing', 'from_users', 'forwards', 'chats', 'blacklist_chats', 'func']}
    
    config.bot.add_event_handler(_func, events.NewMessage(pattern=pattern, **kw))
    return _func
  return deco
  
  
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
        