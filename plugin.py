from telethon import events
import traceback
import re
import os.path
import inspect
import functools
import asyncio 

import config
from util.log import logger


class Command:
  def __init__(
    self, cmd, *,
    pattern=None,
    info="", # BotCommand 中的描述信息
    scope="",
    **kwargs,
  ):
    self.cmd = cmd
    if pattern is None:
      pattern = r'^/' + self.cmd + '.*'
    self.pattern = pattern
    self.info = info
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
      if 'text' in _args:
        text = ''
        if len(args) > 0:
          args = list(args)
          text = args.pop(0)
        if not text and getattr(event, 'message', None) and getattr(event.message, 'message', None):
          text = event.message.message
        args = [text] + list(args)
      
      sender = await event.get_sender()
      name = getattr(sender, 'first_name', None) or getattr(sender, 'title', None)
      if t := getattr(sender, 'last_name', None):
        name += ' ' + t
      if event.chat_id == event.sender_id:
        info = f'被 {name}({sender.id}) 私聊触发'
      else:
        chat = await event.get_chat()
        chatname = getattr(chat, 'first_name', None) or getattr(chat, 'title', None)
        if t := getattr(chat, 'last_name', None):
          chatname += ' ' + t
        info = f'在群组 {chatname}({event.chat_id}) 中被 {name}({event.sender_id}) 触发'
    
      logger.info(f'命令 "{self.cmd}" ' + info)
      res = None
      try:
        res = await func(event, *args, **kwargs)
      except asyncio.CancelledError:
        logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 被取消')
      except events.StopPropagation:
        pass
      except:
        logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 异常结束')
      logger.info(f'命令 "{self.cmd}"({event.chat_id}-{event.sender_id}) 运行结束')
      return res
    
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
        