from telethon import TelegramClient, events, types, functions, errors, utils
import asyncio
import inspect
import functools
import itertools
from datetime import datetime, timedelta

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
        
  async def delete_messages(
    self,
    entity: 'hints.EntityLike',
    message_ids: 'typing.Union[hints.MessageIDLike, typing.Sequence[hints.MessageIDLike]]',
    *,
    revoke: bool = True,
    check_permission: bool = True
  ) -> 'typing.Sequence[types.messages.AffectedMessages]':
    has_permission = True
    if revoke and check_permission:
      peer = utils.get_peer(entity)
      if not isinstance(peer, types.PeerUser):
        permissions = await self.get_permissions(entity, 'me')
        has_permission = bool(permissions.delete_messages)
    if has_permission:
      return await super().delete_messages(entity, message_ids, revoke=revoke)
    
    if not utils.is_list_like(message_ids):
      message_ids = (message_ids,)
      
    gets = await self.get_messages(entity, ids=[m for m in message_ids if isinstance(m, int)])
    messages = [
      m for m in itertools.chain(message_ids, gets)
      if isinstance(m, (types.Message, types.MessageService, types.MessageEmpty))
    ]
    if any(i.sender_id != self.me.id for i in messages):
      t = [i.id for i in messages if i.sender_id != self.me.id]
      logger.warning(f'No permission to delete messages{t} in Channel {utils.get_peer_id(entity)}')
    return await super().delete_messages(entity, [i.id for i in messages if i.sender_id == self.me.id], revoke=revoke)
 
  @staticmethod
  def schedule_decorator(func):
    if not inspect.isawaitable(func):
      @functools.wraps(func)
      def _func(*args, **kwargs):
        logger.info(f'计划任务 {func.__qualname__} 开始执行')
        res = func(*args, **kwargs)
        logger.info(f'计划任务 {func.__qualname__} 执行完毕')
        return res
      return _func
    else:
      @functools.wraps(func)
      async def _func():
        logger.info(f'计划任务 {func.__qualname__} 开始执行')
        res = await func
        logger.info(f'计划任务 {func.__qualname__} 执行完毕')
        return res
      return _func()
    
  def schedule(self, time, func):
    run_time = (datetime.now() + timedelta(seconds=time)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    logger.info(f'计划任务 {func.__qualname__} 将在 {time}秒后({run_time}) 执行')
    func = self.schedule_decorator(func)
    if inspect.isawaitable(func):
      func = functools.partial(self.loop.create_task, func)
    self.loop.call_later(time, func)
  
  def schedule_delete_messages(self, time, *args, **kwargs):
    self.schedule(time, self.delete_messages(*args, **kwargs))
    