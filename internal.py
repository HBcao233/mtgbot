from telethon import events, types, functions, utils, errors, Button
from dotenv import load_dotenv
import ast
import importlib
import inspect
import os
import tomllib
import time

import config
import util
import filters
from plugin import Command, Scope, reload_plugins
from util.log import logger
from util.data import MessageData


@Command('start')
async def _start(event, text):
  """
  start命令, 如果存在help命令将自动触发
  
  :meta public:
  """
  if text == '':
    for i in bot.list_event_handlers():
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


@Command(
  'settings',
  enable=(lambda: len(config.settings) > 0),
  info='设置',
  scope=Scope.private(),
  filter=filters.PRIVATE,
)
async def _settings(event):
  """
  机器人设置命令
  
  :meta public:
  """
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
  logger.info(f'.env 重载完成')

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


@bot.on(events.CallbackQuery(pattern=rb'delete(?:~([\x00-\xff]{6,6}))?$'))
async def _delete_button(event):
  """
  删除消息按钮 
  ~6字节整数用于指定发送者
  """
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


def normalize_value(k, v):
  """
  * all 统一为 all; 字符串,打散
  
  :meta private:
  """
  if k != 'cmd':
    if v == '*' or v == 'all':
      return 'all'
    return v
  if isinstance(v, list):
    return v
  if v == '*' or v == 'all':
    return 'all'
  return [i.strip() for i in v.split(',')]

def filter_none_cmd(i, k):
  """
  过滤config: 无效cmd
  
  :meta private:
  """
  if not i or not i.get('cmd'):
    logger.warning(f'{k}-{i}: cmd项为空, 已忽略')
    return False
  return True

def filter_peer(i):
  """
  过滤config: Peer 指定群聊
  
  :meta private:
  """
  if isinstance(i['chat_id'], int) and i['chat_id'] != 0:
    return True 
  logger.warning(f'NoScopePeer-{i}: chat_id 配置错误, 已忽略')
  return False

def filter_peer_user(i):
  """
  过滤config: PeerUser (指定群聊中的用户)
  
  :meta private:
  """
  if (
    isinstance(i['chat_id'], int)
    and isinstance(i['user_id'], int)
    and i['chat_id'] < 0
    and i['user_id'] > 0
  ):
    return True
  logger.warning(f'NoScopePeerUser-{i}: chat_id/user_id 配置错误, 已忽略')
  return False

def filter_peer_admins(i):
  """
  过滤config: PeerAdmins
  
  :meta private:
  """
  if isinstance(i['chat_id'], str) and i['chat_id'] == 'all':
    return True
  if isinstance(i['chat_id'], int) and i['chat_id'] < 0:
    return True
  logger.warning(f'NoScopePeerAdmins-{i}: chat_id 配置错误, 已忽略')
  return False

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
        _k: normalize_value(_k, _v)
        for _k, _v in i.items()
      }
      for i in v
      if filter_none_cmd(i, k)
    ]
    for k, v in c.items()
  }
  c['NoScopePeer'] = [i for i in c['NoScopePeer'] if filter_peer(i)]
  c['NoScopePeerUser'] = [i for i in c['NoScopePeerUser'] if filter_peer_user(i) ]
  c['NoScopePeerAdmins'] = [i for i in c['NoScopePeerAdmins'] if filter_peer_admins(i) ]
  return c
  

def fc_users(v, c):
  """
  过滤cmd: 所有私聊
  
  :meta private:
  """
  for i in c['NoScopeUsers']:
    if i['cmd'] == 'all':
      return set()
    v = {j for j in v if j[0] not in i['cmd']}
  return v

def fc_chats(v, c):
  """
  过滤cmd: 所有群聊
  
  :meta private:
  """
  for i in c['NoScopeChats']:
    if i['cmd'] == 'all':
      return set()
    v = {j for j in v if j[0] not in i['cmd']}
  return v

def fc_chatadmins(v, c):
  """
  过滤cmd: 所有群聊的管理员

  :meta private:
  """
  for i in c['NoScopeChatAdmins']:
    if i['cmd'] == 'all':
      return set()
    v = {j for j in v if j[0] not in i['cmd']}
  return v

def fc_peer(v, c):
  """
  过滤cmd: 指定频道/群聊/用户

  :meta private:
  """
  for i in c['NoScopePeer']:
    if i['chat_id'] == k.chat_id:
      if i['cmd'] == 'all':
        return set()
      v = {j for j in v if j[0] not in i['cmd']}
  return v

def fc_peer_user(v, c):
  """
  过滤cmd: 指定用户私聊

  :meta private:
  """
  for i in c['NoScopePeerUser']:
    if i['chat_id'] == k.chat_id and i['user_id'] == k.user_id:
      if i['cmd'] == 'all':
        return set()
      v = {j for j in v if j[0] not in i['cmd']}
  return v 

def fc_peeradmins(k, v, c):
  """
  过滤cmd: 指定群聊中的管理员

  :meta private:
  """
  for i in c['NoScopePeerAdmins']:
    if i['chat_id'] == k.chat_id:
      if i['cmd'] == 'all':
        return set()
      v = {j for j in v if j[0] not in i['cmd']}
  return

def _filter_scopes_config(commands, c):
  """
  使用 ScopesConfig 对命令进行过滤

  :meta private:
  """
  for k, v in commands.items():
    for i in c['NoScopeAll']:
      if i['cmd'] == 'all':
        return {}
      commands[k] = {j for j in v if j[0] not in i['cmd']}

    if k.type == types.BotCommandScopeUsers or (
      k.type == types.BotCommandScopePeer and k.chat_id > 0
    ):
      commands[k] = fc_users(commands[k], c)

    if k.type in (
      types.BotCommandScopeChats,
      types.BotCommandScopePeerUser,
      types.BotCommandScopeChatAdmins,
      types.BotCommandScopePeerAdmins,
    ) or (k.type == types.BotCommandScopePeer and k.chat_id < 0):
      commands[k] = fc_chats(commands[k], c)

    if k.type in (types.BotCommandScopeChatAdmins, types.BotCommandScopePeerAdmins):
      commands[k] = fc_chatadmins(v, c)

    if k.type == types.BotCommandScopePeer:
      commands[k] = fc_peer(v, c)
    elif k.type == types.BotCommandScopePeerUser:
      commands[k] = fc_peer_user(v, c)
    elif k.type == types.BotCommandScopePeerAdmins:
      commands[k] = fc_peeradmins(k, v, c)
  return commands


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

async def _reset_bot_scope(commands):
  """
  重置 bot scope
  
  :meta private:
  """
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
  # 对比改变部分进行按需重置
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

def _fill_commands(commands, scopes_config):
  """
  命令补偿，以便没有的范围可以进行过滤
  给每个范围添加 Scope.all() 的命令
  超级管理员添加 Scope.private() 的命令
  给群聊相关范围添加 Scope.chats() 的命令
  NoScope 配置中的聊天作命令补偿 以便过滤
  
  :meta private:
  """
  if commands.get(Scope.private()) is None:
    commands[Scope.private()] = commands[Scope.all()]

  # 超管私聊命令补偿
  for i in config.superadmin:
    commands[Scope.chat(i)].update(commands[Scope.private()])
  
  if commands.get(Scope.chats()) is None:
    commands[Scope.chats()] = commands[Scope.all()]
  if commands.get(Scope.chat_admins()) is None:
    commands[Scope.chat_admins()] = commands[Scope.chats()]
  
  for k in commands:
    if k.type in (
      types.BotCommandScopePeerUser,
      types.BotCommandScopeChatAdmins,
      types.BotCommandScopePeerAdmins,
    ) or (k.type == types.BotCommandScopePeer and k.chat_id < 0):
      commands[k].update(commands[Scope.chats()])
  
  # NoScope 配置中的聊天作命令补偿 以便过滤
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
  return commands


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
