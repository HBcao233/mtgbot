from telethon import events, utils
from telethon.custom import Button

import util
from plugin import handler


@handler('help', info='介绍与帮助')
async def help(event):
  peer_id = utils.get_peer_id(event.message.peer_id)
  chat = await bot.get_entity(event.message.peer_id)
  name = getattr(chat, 'first_name', None) or getattr(chat, 'title', None)
  if t := getattr(chat, 'last_name', None):
    name += ' ' + t

  await event.respond(
    (
      f'Hi, [{util.string.markdown_escape(name)}](tg://user?id={peer_id})! 这里是传话姬小派魔! \n'
      '发送任意内容，小派魔都会原话传达给主人～\n'
      'ps: 表情回应也可以转发哦～'
    ),
    buttons=Button.url('源代码', 'https://github.com/HBcao233/mtgbot'),
  )
  raise events.StopPropagation
