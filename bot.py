from telethon import TelegramClient, events, types, functions, errors, utils
import asyncio

import config
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
    
  async def _call_callback(self, request, res):
    logger.debug(f'触发 __call__ request: {request.__class__.__name__}; result: {res.__class__.__name__}')
    if (
      isinstance(request, functions.messages.SendMessageRequest) or 
      isinstance(request, functions.messages.SendMediaRequest) or 
      isinstance(request, functions.messages.SendMultiMediaRequest)
    ):
      if isinstance(res, types.UpdateShortSentMessage):
        return MessageData.add_message(request.peer, res.id)
        
      _request = request
      if isinstance(request, functions.messages.SendMultiMediaRequest):
        _request = [i.random_id for i in request.multi_media]
      messages = self._get_response_message(_request, res, request.peer)
      if not utils.is_list_like(messages):
        messages = [messages]
      for i in messages:
        MessageData.add_message(request.peer, i)
     