from telethon import types, events, utils

import util
from plugin import handler
from util.log import logger


@handler('help', info='介绍与帮助')
async def help(event):
  peer_id = utils.get_peer_id(event.message.peer_id)
  chat = await bot.get_entity(event.message.peer_id)
  name = getattr(chat, 'first_name', None) or getattr(chat, 'title', None)
  if t := getattr(chat, 'last_name', None):
    name += ' ' + t

  await event.respond(
    (
      f'Hi, [{util.string.markdown_escape(name)}](tg://user?id={peer_id})! '
    ),
    buttons=types.KeyboardButtonWebView('MOE', 'https://hbcaodog--moe-f.modal.run/'),
  )
  raise events.StopPropagation


@handler('ping', info='查看小派魔是否存活')
async def ping(event):
  await event.reply('小派魔存活中')


@handler('start')
async def _(event):
  text = event.message.message.replace('/start', '').strip()
  logger.info(text)
  if text.startswith('tests_bdsm_uid_'): 
    uid = text.replace('tests_bdsm_uid_', '')
    logger.info(uid)
    await event.respond(
      (
        '别人分享的 BDSM 紫评表'
      ),
      buttons=types.KeyboardButtonWebView('BDSM 紫评表', f'https://hbcaodog--moe-f.modal.run/tests/bdsm/?uid={uid}'),
    )
  elif text.startswith('tests_bdsm'): 
    await event.respond(
      (
        'BDSM 紫评表'
      ),
      buttons=types.KeyboardButtonWebView('BDSM 紫评表', f'https://hbcaodog--moe-f.modal.run/tests/bdsm/'),
    )
  