from telethon import events, functions, types, utils
from dotenv import load_dotenv
import inspect
import importlib
import time
import os

import config
import filters
import util
from plugin import Command, Scope, reload_plugins
from util.data import MessageData
from util.log import logger
from .scope import (
  _reset_bot_scope,
  _load_scopes_config,
  _filter_scopes_config,
  _fill_commands,
)


@Command('start')
async def _start(event, text):
  """
  start命令, 如果存在help命令将自动触发

  :meta public:
  """
  logger.info(f'text: {text}')
  if text != '':
    return
  for i in event.client.list_event_handlers():
    if getattr(i[1], 'pattern', None):
      p = i[1].pattern.__self__.pattern
      if p.startswith('^/help') or p.startswith('/help'):
        await i[0](event)
        break


@Command(
  'cancel',
  info='取消当前正在进行的任务',
)
async def _cancel(event):
  """
  取消任务命令

  :meta public:
  """
  f = True

  for i in event.client._event_handler_tasks:
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


@Command(
  'reload',
  info='重载插件',
  scope=Scope.superadmin(),
  filter=filters.PRIVATE & filters.SUPERADMIN & filters.COMMAND,
)
async def _reload(event):
  """
  重载插件命令
  仅超管私聊可用

  :meta public:
  """
  load_dotenv(dotenv_path=config.env_path, verbose=True)
  config.env = os.environ
  config.superadmin = [int(x) for x in config.env.get('superadmin', '').split(',') if x]
  config.telegraph_author_name = config.env.get('telegraph_author_name', '')
  config.telegraph_author_url = config.env.get('telegraph_author_url', '')
  config.telegraph_access_token = config.env.get('telegraph_access_token', '')
  logger.info('.env 重载完成')

  config.commands = []
  config.inlines = []
  config.settings = []
  bot._event_builders = []
  start_time = time.perf_counter()
  importlib.reload(config.internal)
  reload_plugins()
  logger.info(f'插件重载完成, 用时: {time.perf_counter() - start_time}s')
  await _init()
  await event.reply('重载完成')


@bot.on(events.CallbackQuery(pattern=rb'delete(#?)(?:~([\x00-\xff]{6,8}))?$'))
async def delete_button(event):
  """
  删除消息按钮
  ~6字节有符号整数用于指定发送者
  """
  chat_id = event.chat_id
  sender_id = event.sender_id
  
  match = event.pattern_match
  need_admin = bool(match.group(1))
  if need_admin:
    sender_permissions = await bot.get_permissions(chat_id, event.sender_id)
    if not sender_permissions.is_admin:
      await event.answer('只有管理员可以点击该按钮', alert=True)
      return
  
  need_sender_id = None
  if t := match.group(2):
    need_sender_id = int.from_bytes(t, 'big', signed=True)

  if need_sender_id and sender_id and need_sender_id != sender_id:
    sender_permissions = await bot.get_permissions(chat_id, event.sender_id)
    if not sender_permissions.delete_messages:
      await event.answer('只有消息发送者可以修改', alert=True)
      return

  await event.answer()
  await event.delete()


@bot.on(events.NewMessage)
async def _add_message(event):
  """
  保存消息id, util.data.MessageData 的数据来源
  """
  MessageData.add_message(
    utils.get_peer_id(event.message.peer_id),
    event.message.id,
    getattr(event.message, 'grouped_id', None),
  )


@bot.on(events.InlineQuery)
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


async def _init_commands():
  """
  Command初始化
  注册命令，并将同一范围下所有命令整理为集合set

  :meta private:
  """
  commands = {}
  try:
    for i in config.commands:
      if not util.bool_or_callable(i.enable):
        continue
      bot.add_event_handler(i.func, events.NewMessage(pattern=i.pattern, **i.kwargs))
      if i.info != '' and util.bool_or_callable(i.show_info):
        for s in i.scope:  # 遍历 ScopeList 中的 Scope
          if s not in commands:
            commands[s] = set()
          commands[s].add((i.cmd, i.info))
    return commands
  except Exception:
    logger.critical(f'{i.func.__module__}.{i} 初始化失败', exc_info=1)
    exit(1)


async def _init():
  """
  初始化

  :meta private:
  """
  start_time = time.perf_counter()

  # 初始化 commands
  commands: dict[Scope, set[tuple[str, str]]] = await _init_commands()
  # 重置 scope
  await _reset_bot_scope(commands)

  # ---start--- 设置Scope ---start---
  scopes_config = _load_scopes_config()
  logger.info(f'读取到Scopes配置: {scopes_config}')
  # 命令补偿
  commands = _fill_commands(commands, scopes_config)
  # 命令过滤
  commands = _filter_scopes_config(commands, scopes_config)
  logger.debug(
    '{\n'
    + ('\n'.join([f'  {k}: {str([i[0] for i in v])},' for k, v in commands.items()]))
    + '\n}'
  )
  # 提交 scope
  for k, v in commands.items():
    try:
      await bot(
        functions.bots.SetBotCommandsRequest(
          scope=await k.to_command_scope(),
          lang_code='zh',
          commands=[types.BotCommand(*i) for i in v],
        )
      )
    except ValueError:
      logger.warning('scope 实体化失败, 可能是 bot 未加入群组', exc_info=1)
  # ---end--- 设置Scope ---end---
  logger.info(f'初始化完成, 用时: {time.perf_counter() - start_time}s')
