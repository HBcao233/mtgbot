from telethon import events, types, functions, utils, errors, Button
import asyncio
import inspect
import ast
import time

import config
import util
from plugin import load_plugins, handler, Scope
from util.log import logger
from util.data import MessageData
from bot import Bot
import filters


if __name__ == '__main__':
  if len(config.token) < 36 or ':' not in config.token:
    raise ValueError('请提供正确的 bot token')
  if not config.api_id or not config.api_hash:
    raise ValueError('请提供正确的 api_id 和 api_hash')
  logger.info(
    f'当前 bot_token={config.token.split(":")[0] + "*" * 35}, api_id={config.api_id}, proxy={config.proxy}'
  )

  try:
    __builtins__.bot = config.bot = Bot(
      util.getFile('bot.session'),
      config.api_id,
      config.api_hash,
      proxy=config.proxy,
    ).start(bot_token=config.token)
  except ConnectionError:
    logger.critical('连接错误', exc_info=1)
    exit(1)


@handler('start')
async def start(event, text):
  if text == '':
    for i in bot.list_event_handlers():
      if getattr(i[1], 'pattern', None):
        p = i[1].pattern.__self__.pattern
        if p.startswith('^/help') or p.startswith('/help'):
          await i[0](event)
          break


@handler('cancel', info='取消当前正在进行的任务')
async def _cancel(event):
  f = True

  for i in bot._event_handler_tasks:
    _locals = inspect.getargvalues(i.get_coro().cr_frame).locals

    c = _locals.get('callback', None)
    _event = _locals.get('event', None)
    cmd_tip = ''
    for cmd in config.commands:
      if c is cmd.func:
        cmd_tip = f'(命令 "{cmd.cmd}"({_event.chat_id}-{_event.sender_id}))'
        break
    module_name = inspect.getmodule(c).__name__
    if module_name != '__main__' and event.sender_id == _event.sender_id:
      logger.info(f'取消任务 {i.get_name()} {cmd_tip}')
      i.cancel()
      f = False
  if f:
    return await event.respond('当前没有任务正在进行中')
  await event.respond('已取消所有进行中的任务')


@handler(
  'settings',
  enable=(lambda: len(config.settings) > 0),
  info='设置',
  scope=Scope.private(),
  filter=filters.PRIVATE,
)
async def _settings(event):
  buttons = []
  index = 0
  for i in config.settings:
    if index == len(buttons):
      buttons.append([])
    buttons[index].append(Button.inline(i.text, i.data))
    if len(buttons[index]) == 2:
      index += 1

  buttons.append([Button.inline('关闭面板', data=b'delete')])
  caption = config.env.get('settings_caption', '')
  if caption:
    caption = ast.parse(r'"""' + caption + '"""').body[0].value.value
  else:
    caption = '设置小派魔的运行参数'
  await event.reply(
    caption,
    buttons=buttons,
  )


async def _delete_button(event):
  chat_id = event.chat_id
  match = event.pattern_match
  sender_id = None
  if t := match.group(1):
    sender_id = int.from_bytes(t, 'big')
  if sender_id and event.sender_id and sender_id != event.sender_id:
    participant = await bot.get_permissions(chat_id, event.sender_id)
    if not participant.delete_messages:
      return await event.answer('只有消息发送者可以修改', alert=True)
  await event.delete()


async def _add_message(event):
  """
  添加消息, util.data.MessageData 数据来源
  """
  MessageData.add_message(
    utils.get_peer_id(event.message.peer_id),
    event.message.id,
    getattr(event.message, 'grouped_id', None),
  )


async def _global_inline_query(event):
  """
  plugin.InlineCommand 处理
  """
  res = []
  for i in config.inlines:
    if i.pattern is None or (match := i.pattern(event.text)):
      if match:
        event.pattern_match = match
      try:
        r = await i.func(event)
      except Exception:
        logger.error(
          f'InlineCommand "{i.func.__module__}.{i.func.__qualname__}" 获取失败',
          exc_info=1,
        )
      else:
        if isinstance(r, list):
          res.extend(r)
  if res:
    await event.answer(res)


async def _init():
  """
  初始化
  """
  start_time = time.perf_counter()
  await bot(
    functions.bots.ResetBotCommandsRequest(
      scope=types.BotCommandScopeDefault(),
      lang_code='zh',
    )
  )
  await bot(
    functions.bots.ResetBotCommandsRequest(
      scope=types.BotCommandScopeUsers(),
      lang_code='zh',
    )
  )

  try:
    commands: dict[Scope, set[tuple[str, str]]] = {}
    for i in config.commands:
      if not util.bool_or_callable(i.enable):
        continue
      bot.add_event_handler(i.func, events.NewMessage(pattern=i.pattern, **i.kwargs))
      if i.info != '' and util.bool_or_callable(i.show_info):
        for s in i.scope:  # 遍历 ScopeList 中的 Scope
          if s not in commands:
            commands[s] = set()
          commands[s].add((i.cmd, i.info))
  except Exception:
    logger.critical(f'{i.func.__module__}.{i} 初始化失败', exc_info=1)
    exit(1)

  for k in commands:
    if k.type != types.BotCommandScopeDefault:
      commands[k].update(commands[Scope.all()])

  logger.debug(
    '{\n'
    + ('\n'.join([f'  {k}: {str([i[0] for i in v])},' for k, v in commands.items()]))
    + '\n}'
  )

  data = util.data.Settings()
  old_peer = data.get('scope_peer', {})
  new_peer = {}
  for scope, v in commands.items():
    if scope.type == types.BotCommandScopePeer:
      new_peer[str(scope.chat_id)] = [i[0] for i in v]

  logger.debug(f'old_peer: {old_peer}')
  logger.debug(f'new_peer: {new_peer}')
  for k, v in old_peer.items():
    need_reset = False
    if k not in new_peer.keys():
      need_reset = True
    else:
      for i in v:
        if i not in new_peer[k]:
          need_reset = True
    if need_reset:
      logger.info(f'重置 ScopePeer({k}) ')
      try:
        await bot(
          functions.bots.ResetBotCommandsRequest(
            scope=types.BotCommandScopePeer(peer=await bot.get_input_entity(int(k))),
            lang_code='zh',
          )
        )
        for i in MessageData.iter_chats():
          if i < 0:
            await bot(
              functions.bots.ResetBotCommandsRequest(
                scope=types.BotCommandScopePeerUser(
                  await bot.get_input_entity(i), await bot.get_input_entity(int(k))
                ),
                lang_code='zh',
              )
            )
      except errors.ChannelPrivateError:
        pass

  with data:
    data['scope_peer'] = new_peer

  for k, v in commands.items():
    await bot(
      functions.bots.SetBotCommandsRequest(
        scope=await k.to_command_scope(),
        lang_code='zh',
        commands=[types.BotCommand(*i) for i in v],
      )
    )

  logger.info(f'初始化完成, 用时: {time.perf_counter() - start_time}s')


if __name__ == '__main__':
  bot.add_event_handler(
    _delete_button, events.CallbackQuery(pattern=rb'delete(?:~([\x00-\xff]{6,6}))?$')
  )
  bot.add_event_handler(_add_message, events.NewMessage)
  bot.add_event_handler(_global_inline_query, events.InlineQuery)

  start_time = time.perf_counter()
  load_plugins()
  logger.info(f'插件载入完成, 用时: {time.perf_counter() - start_time}s')
  bot.loop.create_task(_init())
  try:
    bot.run_until_disconnected()
  except asyncio.exceptions.CancelledError:
    pass
  except KeyboardInterrupt:
    pass
