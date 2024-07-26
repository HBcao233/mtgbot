import os.path 
from telethon import TelegramClient, events, types, functions, errors

import config
import util
from plugin import load_plugins, handler
from util.log import logger


api_id = 4
api_hash = '014b35b6184100b085b0d0572f9b5103'


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
    
if len(config.token) < 10:
  raise ValueError('请提供正确的bot token')
bot = config.bot = Bot(util.getFile('bot.session'), api_id, api_hash).start(bot_token=config.token)


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
  bot.run_until_disconnected()
  