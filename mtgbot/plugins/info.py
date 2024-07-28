from telethon import events

import config
from util.log import logger
from plugin import handler


@handler('info')
async def _(event):
  msg = event.message
  if (reply_message := await event.message.get_reply_message()):
    msg = reply_message
  logger.info(msg)
  raise events.StopPropagation
  