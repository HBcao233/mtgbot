from telethon import TelegramClient, types, functions, errors, utils, hints
from datetime import datetime, timedelta
import asyncio
import inspect
import functools
import typing
import time
import os

import config
from util.log import logger
from util.data import MessageData


class Bot(TelegramClient):
  async def connect(self):
    """
    连接 Telegram 服务器, 自动处理异常, 记录登录用时

    :meta private:
    """
    start_time = time.perf_counter()
    logger.info('登录中')
    try:
      await super().connect()
    except errors.AuthKeyDuplicatedError as e:
      logger.warn(f'AuthKeyDuplicatedError: {e}')
      path = os.path.join(config.botHome, 'bot.session')
      os.remove(path)
      await self.sign_in(bot_token=config.token)
    try:
      me = await self.get_me()
    except errors.AuthKeyDuplicatedError:
      logger.warn(f'AuthKeyDuplicatedError: {e}')
      path = os.path.join(config.botHome, 'bot.session')
      os.remove(path)
      await self.sign_in(bot_token=config.token)
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
    logger.info(f'登录完成, 用时: {time.perf_counter() - start_time}s')
    logger.info('当前登录账户信息: %s', self.me)

  async def request_callback(self, request, res):
    """
    请求回调

    使用 ``bot(functions.XXX)`` (``bot.__call__``) 向telegram发送 Request 后做后续处理 (如记录发送消息id, debug记录所有请求)
    """
    logger.debug(
      f'触发 request: {request.__class__.__name__}; result: {res.__class__.__name__}'
    )
    if isinstance(
      request,
      (
        functions.messages.SendMessageRequest,
        functions.messages.SendMediaRequest,
        functions.messages.SendMultiMediaRequest,
      ),
    ):
      if isinstance(res, types.UpdateShortSentMessage):
        return MessageData.add_message(utils.get_peer_id(request.peer), res.id)

      _request = request
      if isinstance(request, functions.messages.SendMultiMediaRequest):
        _request = [i.random_id for i in request.multi_media]
      messages = self._get_response_message(_request, res, request.peer)
      if not utils.is_list_like(messages):
        messages = [messages]
      for i in messages:
        MessageData.add_message(request.peer, i)

  async def __call__(self, request, *args, **kwargs):
    res = await TelegramClient.__call__(self, request, *args, **kwargs)
    try:
      await self.request_callback(request, res)
    except Exception:
      logger.error(exc_info=1)
    return res

  async def edit_message(
    self,
    entity: 'typing.Union[hints.EntityLike, types.Message]',
    message: 'hints.MessageLike' = None,
    text: str = None,
    *,
    parse_mode: str = (),
    attributes: 'typing.Sequence[types.TypeDocumentAttribute]' = None,
    formatting_entities: typing.Optional[typing.List[types.TypeMessageEntity]] = None,
    link_preview: bool = True,
    file: 'hints.FileLike' = None,
    thumb: 'hints.FileLike' = None,
    force_document: bool = False,
    buttons: typing.Optional['hints.MarkupLike'] = None,
    supports_streaming: bool = False,
    schedule: 'hints.DateLike' = None,
  ) -> 'types.Message':
    """
    编辑消息前去除空Button

    :meta private:
    """
    # 自动去除 buttons 中的空列表
    if isinstance(buttons, typing.Sequence):
      for i, ai in enumerate(reversed(buttons)):
        if isinstance(ai, typing.Sequence) and len(ai) == 0:
          buttons.pop(i)
      if len(buttons) == 0:
        buttons = None
    return await super().edit_message(
      entity,
      message,
      text,
      parse_mode=parse_mode,
      attributes=attributes,
      formatting_entities=formatting_entities,
      link_preview=link_preview,
      file=file,
      thumb=thumb,
      force_document=force_document,
      buttons=buttons,
      supports_streaming=supports_streaming,
      schedule=schedule,
    )

  async def delete_messages(
    self,
    entity: 'hints.EntityLike',
    message_ids: 'typing.Union[hints.MessageIDLike, typing.Sequence[hints.MessageIDLike]]',
    *,
    revoke: bool = True,
  ):
    """
    删除信息, 触发 MessageDeleteForbiddenError 时自动尝试对 `ids` 每一个进行删除

    :meta private:
    """
    try:
      return await super().delete_messages(entity, message_ids, revoke=revoke)
    except errors.MessageDeleteForbiddenError:
      if not utils.is_list_like(message_ids) or len(message_ids) == 1:
        raise
      for i in message_ids:
        try:
          await super().delete_messages(entity, i, revoke=revoke)
        except errors.MessageDeleteForbiddenError:
          pass
      raise

  @staticmethod
  def schedule_decorator(func):
    """
    计划任务装饰器
    """
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
    """
    设置计划任务

    Arguments
      time (`int`):
        延迟时间

      func (`callable`):
        执行函数

        .. note::
          非异步函数传参请用: functools.partial(func, \\*args, \\*\\*kwargs)
    """
    run_time = (datetime.now() + timedelta(seconds=time)).strftime(
      '%Y-%m-%d %H:%M:%S.%f'
    )[:-3]
    logger.info(f'计划任务 {func.__qualname__} 将在 {time}秒后({run_time}) 执行')
    func = self.schedule_decorator(func)
    if inspect.isawaitable(func):
      func = functools.partial(self.loop.create_task, func)
    self.loop.call_later(time, func)

  def schedule_delete_messages(
    self,
    time: int,
    entity: 'hints.EntityLike',
    message_ids: 'typing.Union[hints.MessageIDLike, typing.Sequence[hints.MessageIDLike]]',
    *,
    revoke: bool = True,
  ):
    """
    计划删除消息

    Arguments
      time (`int`):
        延迟时间

      entity (`hints.EntityLike`):
        指定实体 一般为 peer

      message_ids (`typing.Union[hints.MessageIDLike, typing.Sequence[hints.MessageIDLike]]`):
        消息id列表

      revoke (`bool`):
        是否为对方也删除, 默认为 True
    """
    async def d(entity, message_ids, *, revoke=revoke):
      try:
        await self.delete_messages(
          entity,
          message_ids,
          revoke=revoke,
        )
      except errors.MessageDeleteForbiddenError:
        logger.warn(
          '计划任务 Bot.delete_messages 遇到错误 MessageDeleteForbiddenError', exc_info=1
        )
    self.schedule(
      time,
      d(
        entity,
        message_ids,
        revoke=revoke,
      ),
    )