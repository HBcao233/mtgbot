from telethon import types, events, utils

import util
from plugin import Command
from util.log import logger


@Command('help', info='介绍与帮助')
async def help(event):
  peer_id = utils.get_peer_id(event.message.peer_id)
  chat = await bot.get_entity(event.message.peer_id)
  name = getattr(chat, 'first_name', None) or getattr(chat, 'title', None)
  if t := getattr(chat, 'last_name', None):
    name += ' ' + t

  await event.respond(
    (f'Hi, [{util.string.markdown_escape(name)}](tg://user?id={peer_id})! '),
    buttons=types.KeyboardButtonWebView('MOE', 'https://hbcaodog--moe-f.modal.run/'),
  )
  raise events.StopPropagation


@Command('ping', info='查看小派魔是否存活')
async def ping(event):
  await event.reply('小派魔存活中')
