from telethon import events, types, functions, utils, errors, Button
import builtins
import asyncio
import inspect
import ast
import time
import os
import tomllib

import config
import util
from plugin import load_plugins, handler, Scope
from util.log import logger
from util.data import MessageData
from bot import Bot
import filters


#: Bot: Bot (`TelegramClient <https://docs.telethon.dev/en/stable/modules/client.html#telethon-client>`_ 子类) 实例, 注入 builtins
bot: Bot


if __name__ == '__main__':
  if len(config.token) < 36 or ':' not in config.token:
    raise ValueError('请提供正确的 bot token')
  if not config.api_id or not config.api_hash:
    raise ValueError('请提供正确的 api_id 和 api_hash')
  logger.info(
    f'当前 bot_token={config.token.split(":")[0] + "*" * 35}, api_id={config.api_id}, proxy={config.proxy}'
  )

  try:
    bot: Bot = Bot(
      util.getFile('bot.session'),
      config.api_id,
      config.api_hash,
      proxy=config.proxy,
    ).start(bot_token=config.token)
    config.bot = bot 
    builtins.bot = bot
  except ConnectionError:
    logger.critical('连接错误', exc_info=1)
    exit(1)


@handler('start')
async def _start(event, text):
  if text == '':
    for i in bot.list_event_handlers():
      if getattr(i[1], 'pattern', None):
        p = i[1].pattern.__self__.pattern
        if p.startswith('^/help') or p.startswith('/help'):
          await i[0](event)
          break


@handler(
  'cancel', 
  info='取消当前正在进行的任务',
)
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


def _load_scopes_config():
  """
  加载 Scopes配置
  
  :meta private:
  """
  path = util.getFile('', 'scopes.toml')
  c = {
    'NoScopeAll': [], 
    'NoScopeUsers': [],
    'NoScopeChats': [],
    'NoScopeChatAdmins': [],
    'NoScopePeer': [],
    'NoScopePeerUser': [],
    'NoScopePeerAdmins': [],
  }
  if not os.path.isfile(path):
    return c
  try:
    with open(path, 'rb') as f:
      c.update(tomllib.load(f))
  except Exception:
    logger.warning('Scopes Config 加载失败', exc_info=1)
    return c
  c = {
    k: [
      {
        _k: (
          (_v if _v != '*' else 'all') 
          if _k != 'cmd' else 
          (_v if isinstance(_v, list) else ([j.strip() for j in _v.split(',')] if _v != 'all' and _v != '*' else 'all'))
        )
        for _k, _v in i.items()
      }
      for i in v 
      if i != {} and (
        ('cmd' in i and i['cmd'] != '' and i['cmd'] != [])
        or logger.warning(f'{k}-{i}: cmd项为空, 已忽略') == 'x'
      )
    ]
    for k, v in c.items()
  }
  
  c['NoScopePeer'] = [
    i
    for i in c['NoScopePeer']
    if (
      (isinstance(i['chat_id'], int) and i['chat_id'] != 0)
      or logger.warning(f'NoScopePeer-{i}: chat_id 配置错误, 已忽略') == 'x'
    )
  ]
  c['NoScopePeerUser'] = [
    i
    for i in c['NoScopePeerUser']
    if (
      (isinstance(i['chat_id'], int) and isinstance(i['user_id'], int) and i['chat_id'] < 0 and i['user_id'] > 0)
      or logger.warning(f'NoScopePeerUser-{i}: chat_id/user_id 配置错误, 已忽略') == 'x'
    )
  ]
  c['NoScopePeerAdmins'] = [
    i
    for i in c['NoScopePeerAdmins']
    if (
      (
        (isinstance(i['chat_id'], str) and i['chat_id'] == 'all') or 
        (isinstance(i['chat_id'], int) and i['chat_id'] < 0)
      )
      or logger.warning(f'NoScopePeerAdmins-{i}: chat_id 配置错误, 已忽略') == 'x'
    )
  ]
  return c


def filter_scopes_config(commands, c):
  """
  使用 ScopesConfig 对命令进行过滤
  
  :meta private:
  """
  for k, v in commands.items():
    for i in c['NoScopeAll']:
      if i['cmd'] == 'all':
        return {}
      else:
        commands[k] = {j for j in v if j[0] not in i['cmd']}
    
    if k.type == types.BotCommandScopeUsers or (k.type == types.BotCommandScopePeer and k.chat_id > 0):
      for i in c['NoScopeUsers']:
        if i['cmd'] == 'all':
          commands[k] = set()
        else:
          commands[k] = {j for j in v if j[0] not in i['cmd']}
    
    if k.type in (types.BotCommandScopeChats, types.BotCommandScopePeerUser, types.BotCommandScopeChatAdmins, types.BotCommandScopePeerAdmins) or (k.type == types.BotCommandScopePeer and k.chat_id < 0):
      for i in c['NoScopeChats']:
        if i['cmd'] == 'all':
          commands[k] = set()
        else:
          commands[k] = {j for j in v if j[0] not in i['cmd']}
          
    if k.type in (types.BotCommandScopeChatAdmins, types.BotCommandScopePeerAdmins):
      for i in c['NoScopeChatAdmins']:
        if i['cmd'] == 'all':
          commands[k] = set()
        else:
          commands[k] = {j for j in v if j[0] not in i['cmd']}
          
    if k.type == types.BotCommandScopePeer:
      for i in c['NoScopePeer']:
        if i['chat_id'] == k.chat_id:
          if i['cmd'] == 'all':
            commands[k] = set()
          else:
            commands[k] = {j for j in v if j[0] not in i['cmd']}
    
    elif k.type == types.BotCommandScopePeerUser:
      for i in c['NoScopePeerUser']:
        if i['chat_id'] == k.chat_id and i['user_id'] == k.user_id:
          if i['cmd'] == 'all':
            commands[k] = set()
          else:
            commands[k] = {j for j in v if j[0] not in i['cmd']}
            
    elif k.type == types.BotCommandScopePeerAdmins:
      for i in c['NoScopePeerAdmins']:
        if i['chat_id'] == k.chat_id:
          if i['cmd'] == 'all':
            commands[k] = set()
          else:
            commands[k] = {j for j in v if j[0] not in i['cmd']}
  return commands


async def _init():
  """
  初始化
  """
  start_time = time.perf_counter()
  # ---start--- Command初始化 ---start---
  commands: dict[Scope, set[tuple[str, str]]] = {}
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
  except Exception:
    logger.critical(f'{i.func.__module__}.{i} 初始化失败', exc_info=1)
    exit(1)
  # ---end--- Command初始化 ---end---
  
  # ---start--- 重置Scope ---start---
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
  await bot(
    functions.bots.ResetBotCommandsRequest(
      scope=types.BotCommandScopeChats(),
      lang_code='zh',
    )
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
  # ---end--- 重置Scope ---end---
  
  # ---start--- 设置Scope ---start---
  scopes_config = _load_scopes_config()
  logger.info(f'读取到Scopes配置: {scopes_config}')
  
  if commands.get(Scope.private()) is None:
    commands[Scope.private()] = commands[Scope.all()]
  if commands.get(Scope.chats()) is None:
    commands[Scope.chats()] = commands[Scope.all()]
  if commands.get(Scope.chat_admins()) is None:
    commands[Scope.chat_admins()] = commands[Scope.all()]
  for k in commands:
    if k.type in (types.BotCommandScopePeerUser, types.BotCommandScopeChatAdmins, types.BotCommandScopePeerAdmins) or (k.type == types.BotCommandScopePeer and k.chat_id < 0):
      commands[k].update(commands[Scope.chats()])
  for i in scopes_config['NoScopePeer']:
    k = Scope.chat(i['chat_id'])
    if i['chat_id'] > 0:
      if k not in commands:
        commands[k] = commands[Scope.private()]
    else:
      if k not in commands:
        commands[k] = commands[Scope.chats()]
  for i in scopes_config['NoScopePeerUser']:
    k = Scope.chats(i['chat_id'], i['user_id'])
    if k not in commands:
      commands[k] = commands[Scope.chats()]
  for i in scopes_config['NoScopePeerAdmins']:
    k = Scope.chat_admins(i['chat_id'])
    if k not in commands:
      commands[k] = commands[Scope.chats()]
  # 给所有其他 Scope 添加 Scope.all() 的命令
  for k in commands:
    if k.type != types.BotCommandScopeDefault:
      commands[k].update(commands[Scope.all()])
      
  commands = filter_scopes_config(commands, scopes_config)
  logger.debug(
    '{\n'
    + ('\n'.join([f'  {k}: {str([i[0] for i in v])},' for k, v in commands.items()]))
    + '\n}'
  )
  
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
  