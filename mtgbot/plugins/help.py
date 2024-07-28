from telethon import events

import config
from plugin import handler


@handler('help', info='介绍与帮助')
async def help(event):
  await event.respond('Hi! 这里是小派魔!')
  raise events.StopPropagation
  