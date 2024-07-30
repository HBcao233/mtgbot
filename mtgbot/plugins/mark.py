from telethon import events, utils, errors, Button
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
    media = override_message_spoiler(reply_message, spoiler)
    caption = reply_message.text
  else:
    ids = util.data.MessageData.get_group(reply_message.grouped_id)
    logger.info(ids)
    messages = await bot.get_messages(reply_message.peer_id, ids=ids)
    if (
      (spoiler and all(getattr(i.media, 'spoiler', False) for i in messages)) or 
      (not spoiler and not any(getattr(i.media, 'spoiler', False) for i in messages))
    ):
      return await event.respond('这组媒体都有遮罩' if spoiler else '这组媒体都没有遮罩')
    
    media = [override_message_spoiler(i, spoiler) for i in messages]
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
    

_button_pattern = re.compile(rb'mark_([\x00-\xff]{4,4})(?:~([\x00-\xff]{6,6}))?$').match
@bot.on(events.CallbackQuery(
  pattern=_button_pattern
))
async def _event(event):
  peer = event.query.peer
  
  match = event.pattern_match
  message_id = int.from_bytes(match.group(1), 'big')
  sender_id = None 
  if (t := match.group(2)):
    sender_id = int.from_bytes(t, 'big')
  logger.info(f'{message_id=}, {sender_id=}, {event.sender_id=}')
  
  if sender_id and event.sender_id and sender_id != event.sender_id:
    return await event.answer('只有消息发送者可以修改', alert=True)
  
  message = await bot.get_messages(peer, ids=message_id)
  if message is None:
    return await event.answer('消息被删除', alert=True)
  ids = [message_id]
  if message.grouped_id:
    ids = util.data.MessageData.get_group(message.grouped_id)
  
  messages = await bot.get_messages(peer, ids=ids)
  spoiler = not messages[0].media.spoiler
  for m in messages:
    file = override_message_spoiler(m, spoiler)
    try:
      await m.edit(file=file)
    except errors.MessageNotModifiedError:
      logger.warning('MessageNotModifiedError')
    
  message = await event.get_message()
  buttons = message.buttons[0]
  text = '移除遮罩' if spoiler else '添加遮罩'
  index = 0
  for i, ai in enumerate(buttons):
    if _button_pattern(ai.data):
      index = i
      data = ai.data
      break
  buttons[index] = Button.inline(text, data)
  
  try:
    await event.edit(buttons=buttons)
  except errors.MessageNotModifiedError:
    logger.warning('MessageNotModifiedError')
  await event.answer()
  
  
def override_message_spoiler(message, spoiler: bool):
  media = utils.get_input_media(message.media)
  media.spoiler = spoiler
  return media
  