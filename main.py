from telethon import TelegramClient, events, types, functions, errors
import os.path 
import asyncio
import inspect

import config
import util
from plugin import load_plugins, handler
from util.log import logger


class Bot(TelegramClient):
  async def connect(self):
    await super().connect()
    me = await self.get_me()
    if me is None:
      logger.info('认证失败, 尝试重新登录')
      try:
        await self.sign_in(bot_token=config.token)
      except errors.FloodWaitError as e:
        logger.info('遇到 FloodWaitError, %s秒后重试', e.seconds)
        await asyncio.sleep(e.seconds)
        await self.sign_in(bot_token=config.token)
      
      self.me = await self.get_me()
    else:
      self.me = me
    logger.info(self.me)
    
    await self(functions.bots.ResetBotCommandsRequest(scope=types.BotCommandScopeDefault(), lang_code='zh'))
    
if len(config.token) < 36 or ':' not in config.token:
  raise ValueError('请提供正确的 bot token')
if not config.api_id or not config.api_hash:
  raise ValueError('请提供正确的 api_id 和 api_hash')
logger.info(f'当前 bot_token={config.token.split(":")[0]+"*"*35}, api_id={config.api_id}')
bot = config.bot = Bot(util.getFile('bot.session'), config.api_id, config.api_hash).start(bot_token=config.token)


@handler('start')
async def start(event, text):
  logger.info(event.message)
  if text == '':
    for i in config.bot.list_event_handlers():
      if getattr(i[1], 'pattern'):
        p = i[1].pattern.__self__.pattern
        if (p.startswith('^/help') or p.startswith('/help')):
          await i[0](event)
          break
  raise events.StopPropagation


@handler('cancel', info='取消当前正在进行的任务')
async def _cancel(event):
  f1 = f2 = True
  for i in asyncio.all_tasks():
    coro = i.get_coro()
    c = coro.cr_frame
    _name = inspect.getmodule(c).__name__
    if coro.cr_running: 
      logger.info(f'任务: {i.get_name()}, 来自 {_name}')
    if coro.cr_running and not _name.startswith('telethon'):
      f1 = False
      i.cancel()
      _locals = inspect.getargvalues(c).locals
      
      if (mid := _locals.get('mid', None)):
        await event.reply(
          f'取消任务 {id(i)}',
          reply_to=mid.message_id,
        )
        f2 = False
  if f1:
    return await event.respond('没有任务正在进行中')
  if f2:
    await event.respond('已取消所有任务')
  
  
async def main():
  commands = []
  for i in config.commands:
    if i.info != '' and i.scope == '':
      commands.append(types.BotCommand(
        command=i.cmd,
        description=i.info
      ))
  if len(commands) > 0:
    await bot(functions.bots.SetBotCommandsRequest(
      scope=types.BotCommandScopeDefault(),
      lang_code='zh',
      commands=commands
    ))
    

if __name__ == '__main__':
  load_plugins()
  bot.loop.create_task(main())
  try:
    bot.run_until_disconnected()
  except asyncio.exceptions.CancelledError:
    pass
  except KeyboardInterrupt:
    pass