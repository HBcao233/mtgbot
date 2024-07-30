from telethon import events, types, utils, functions

import config
import util
from plugin import handler


bot = config.bot


@handler('unmark', info='去掉回复图片的遮罩')
async def _unmark(event):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  if reply_message.media is None:
    return await event.respond('回复的信息没有媒体')
  if reply_message.grouped_id is None:
    if getattr(reply_message.media, 'spoiler', False) is False:
      return await event.respond('媒体没有遮罩')
    reply_message.media.spoiler = False
    return await event.respond(reply_message)
  
  ids = util.data.MessageData.get_group(reply_message.grouped_id)
  messages = await bot.get_messages(reply_message.peer_id, ids=ids)
  if not any((getattr(i.media, 'spoiler', False) for i in messages)):
    return await event.respond('这组媒体没有遮罩')
  
  for i, ai in enumerate(messages):
    messages[i].media.spoiler = False
  medias = [types.InputSingleMedia(
    media=utils.get_input_media(ai.media),
    message=ai.message,
    entities=ai.entities,
  ) for i, ai in enumerate(messages)]
  
  await bot(functions.messages.SendMultiMediaRequest(
    peer=reply_message.peer_id, 
    multi_media=medias,
  ))
  raise events.StopPropagation


@handler('unspoiler')
async def _(event):
  return _unmark(event)
