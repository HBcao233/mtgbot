from telethon import events, types, functions, utils, Button
import asyncio
import inspect

import config
import util
from plugin import load_plugins, handler, Scope
from util.log import logger
from util.data import MessageData
from bot import Bot


if len(config.token) < 36 or ':' not in config.token:
  raise ValueError('请提供正确的 bot token')
if not config.api_id or not config.api_hash:
  raise ValueError('请提供正确的 api_id 和 api_hash')
logger.info(
  f'当前 bot_token={config.token.split(":")[0]+"*"*35}, api_id={config.api_id}, proxy={config.proxy}'
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
  raise events.StopPropagation


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


@handler('settings', info='设置', show_info=(lambda: len(config.settings) > 0))
async def _settings(event):
  if not event.is_private:
    return
  buttons = []
  index = 0
  for i in config.settings:
    if index == len(buttons):
      buttons.append([])
    buttons[index].append(Button.inline(i.text, i.data))
    if len(buttons[index]) == 2:
      index += 1

  buttons.append([Button.inline('关闭面板', data=b'delete')])
  await event.reply(
    t if (t := config.env.get('settings_caption', '')) else '设置小派魔的运行参数',
    buttons=buttons,
  )


@bot.on(events.CallbackQuery(pattern=rb'delete(?:~([\x00-\xff]{6,6}))?$'))
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


@bot.on(events.NewMessage)
async def _(event):
  MessageData.add_message(
    utils.get_peer_id(event.message.peer_id),
    event.message.id,
    getattr(event.message, 'grouped_id', None),
  )


@bot.on(events.InlineQuery)
async def _(event):
  res = []
  for i in config.inlines:
    if i.pattern is None or (match := i.pattern(event.text)):
      if match:
        event.pattern_match = match
      try:
        r = await i.func(event)
      except Exception:
        logger.error(f'{i.func.__qualname__} InlineQuery 获取失败', exc_info=1)
      else:
        if isinstance(r, list):
          res.extend(r)
  if res:
    await event.answer(res)


async def init():
  await bot(
    functions.bots.ResetBotCommandsRequest(
      scope=types.BotCommandScopeDefault(),
      lang_code='zh',
    )
  )
  for i in MessageData.iter_chats():
    await bot(
      functions.bots.ResetBotCommandsRequest(
        scope=types.BotCommandScopePeer(peer=await bot.get_input_entity(i)),
        lang_code='zh',
      )
    )

  commands = {}
  for i in config.commands:
    _show_info = i.show_info
    if callable(_show_info):
      _show_info = _show_info()
    if i.info != '' and _show_info:
      for s in i.scope:
        if s not in commands:
          commands[s] = set()
        commands[s].add((i.cmd, i.info))
  for k in commands:
    if not isinstance(k.type, types.BotCommandScopeDefault):
      commands[k].update(commands[Scope.all()])

  # logger.info(json.dumps({k: str([i[0] for i in v]) for k,v in commands.items()}, indent=2, ensure_ascii=False))
  for k, v in commands.items():
    await bot(
      functions.bots.SetBotCommandsRequest(
        scope=await k.to_command_scope(),
        lang_code='zh',
        commands=[types.BotCommand(*i) for i in v],
      )
    )


if __name__ == '__main__':
  load_plugins()
  bot.loop.create_task(init())
  try:
    bot.run_until_disconnected()
  except asyncio.exceptions.CancelledError:
    pass
  except KeyboardInterrupt:
    pass
