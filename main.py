from telethon import TelegramClient, events, types, functions, errors, utils
import telethon
import os.path 
import asyncio
import inspect

import config
import util
from plugin import load_plugins, handler
from util.log import logger
from util.data import MessageData


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
    logger.info('当前登录账户信息: %s', self.me)
    
    await self(functions.bots.ResetBotCommandsRequest(scope=types.BotCommandScopeDefault(), lang_code='zh'))
  
    
async def call_callback(request, res):
  logger.debug(f'触发 __call__ request: {request.__class__.__name__}; result: {res.__class__.__name__}')
  if (
    isinstance(request, functions.messages.SendMessageRequest) or 
    isinstance(request, functions.messages.SendMediaRequest) or 
    isinstance(request, functions.messages.SendMultiMediaRequest)
  ):
    if isinstance(res, types.UpdateShortSentMessage):
      MessageData.add_message(request.peer, res.id)
    else:
      messages = config.bot._get_response_message(request, res, request.peer)
      if utils.is_list_like(messages):
        for i in messages:
          MessageData.add_message(request.peer, i.id)
      else:
        MessageData.add_message(request.peer, messages.id)
      
    
if len(config.token) < 36 or ':' not in config.token:
  raise ValueError('请提供正确的 bot token')
if not config.api_id or not config.api_hash:
  raise ValueError('请提供正确的 api_id 和 api_hash')
logger.info(f'当前 bot_token={config.token.split(":")[0]+"*"*35}, api_id={config.api_id}')
bot = config.bot = Bot(util.getFile('bot.session'), config.api_id, config.api_hash).start(bot_token=config.token)
bot.set_call_callback(call_callback)


@handler('start')
async def start(event, text):
  if text == '':
    for i in config.bot.list_event_handlers():
      if getattr(i[1], 'pattern', None):
        p = i[1].pattern.__self__.pattern
        if (p.startswith('^/help') or p.startswith('/help')):
          await i[0](event)
          break
  raise events.StopPropagation


@handler('cancel', info='取消当前正在进行的任务')
async def _cancel(event):
  import traceback
  f = True
    
  for i in config.bot._event_handler_tasks:
    _locals = inspect.getargvalues(i.get_coro().cr_frame).locals
    
    c = _locals.get('callback', None)
    _event = _locals.get('event', None)
    module_name = inspect.getmodule(c).__name__
    if module_name != '__main__' and event.peer_id.user_id == _event.peer_id.user_id:
      logger.info(f'取消任务 {i.get_name()}')
      i.cancel()
      f = False
  if f:
    return await event.respond('当前没有任务正在进行中')
  await event.respond('已取消所有进行中的任务')
  

@bot.on(events.NewMessage)
async def _(event):
  MessageData.add_message(event.message.peer_id, event.message)
  

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