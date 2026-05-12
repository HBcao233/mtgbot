from telethon import errors, functions, types
import os
import tomllib

import config
import util
from plugin import Scope
from util.data import MessageData
from util.log import logger


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
      {_k: normalize_value(_k, _v) for _k, _v in i.items()}
      for i in v
      if filter_none_cmd(i, k)
    ]
    for k, v in c.items()
  }
  c['NoScopePeer'] = [i for i in c['NoScopePeer'] if filter_peer(i)]
  c['NoScopePeerUser'] = [i for i in c['NoScopePeerUser'] if filter_peer_user(i)]
  c['NoScopePeerAdmins'] = [i for i in c['NoScopePeerAdmins'] if filter_peer_admins(i)]
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


def fc_peer(k, v, c):
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


def fc_peer_user(k, v, c):
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
      commands[k] = fc_peer(k, v, c)
    elif k.type == types.BotCommandScopePeerUser:
      commands[k] = fc_peer_user(k, v, c)
    elif k.type == types.BotCommandScopePeerAdmins:
      commands[k] = fc_peeradmins(k, v, c)
  return commands


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
      except (errors.ChannelPrivateError, ValueError):
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
