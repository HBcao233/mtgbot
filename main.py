from telethon import events, types, functions, errors, utils
import asyncio
import inspect

import config
import util
from plugin import load_plugins, handler
from util.log import logger
from util.data import MessageData
from bot import Bot


if len(config.token) < 36 or ':' not in config.token:
  raise ValueError('请提供正确的 bot token')
if not config.api_id or not config.api_hash:
  raise ValueError('请提供正确的 api_id 和 api_hash')
logger.info(f'当前 bot_token={config.token.split(":")[0]+"*"*35}, api_id={config.api_id}')
bot = config.bot = Bot(util.getFile('bot.session'), config.api_id, config.api_hash).start(bot_token=config.token)


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
    if module_name != '__main__' and event.sender_id == _event.sender_id:
      logger.info(f'取消任务 {i.get_name()}')
      i.cancel()
      f = False
  if f:
    return await event.respond('当前没有任务正在进行中')
  await event.respond('已取消所有进行中的任务')
  

@bot.on(events.NewMessage)
async def _(event):
  MessageData.add_message(event.message.peer_id, event.message.id, getattr(event.message, 'grouped_id', None))
  

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