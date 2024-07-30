from telethon import events, utils
import re 

import config
import util
from util.log import logger
from plugin import handler


bot = config.bot
@handler('mark', 
  info='给回复媒体添加遮罩',
  pattern=re.compile('^/(mark|spoiler)')
)
async def _mark(event, spoiler=True):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  if reply_message.media is None:
    return await event.respond('回复的信息没有媒体')
    
  if reply_message.grouped_id is None:
    if (
      getattr(reply_message.media, 'spoiler', False) is spoiler
    ):
      return await event.respond('该媒体已经有遮罩了' if spoiler else '该媒体没有遮罩')
    media = utils.get_input_media(reply_message.media)
    media.spoiler = spoiler
    caption = reply_message.text
  else:
    ids = util.data.MessageData.get_group(reply_message.grouped_id)
    logger.info(ids)
    messages = await bot.get_messages(reply_message.peer_id, ids=ids)
    logger.info(messages)
    if (
      (spoiler and all(getattr(i.media, 'spoiler', False) for i in messages)) or 
      (not spoiler and not any(getattr(i.media, 'spoiler', False) for i in messages))
    ):
      return await event.respond('这组媒体都有遮罩' if spoiler else '这组媒体都没有遮罩')
    
    media = list(override_spoiler(messages, spoiler))
    caption = [i.text for i in messages]
    
  await bot.send_file(reply_message.peer_id, media, caption=caption)
  raise events.StopPropagation
  
  
@handler(
  'unmark', 
  info='去掉回复媒体的遮罩',
  pattern=re.compile(r'^/(unmark|unspoiler)'),
)
async def _unmark(event):
  return await _mark(event, False)
    
  
@bot.on(events.CallbackQuery(
  pattern=re.compile(b'mark_')
))
async def _event():
  pass
  
  
def override_spoiler(messages, spoiler: bool):
  for i, ai in enumerate(messages):
    media = utils.get_input_media(ai.media)
    media.spoiler = spoiler
    yield media
