from telethon import events, types, functions, utils, Button
import re 
import os
import ujson as json 

import config
import util
from util.log import logger
from plugin import handler
from .data_source import headers, get_twitter, parseTidMsg, parseMedias


bot = config.bot
_pattern = re.compile(r'(?:^|^(?:/?tid(?:@%s)?) ?|(?:https?://)?(?:twitter|x|vxtwitter|fxtwitter)\.com/[a-zA-Z0-9_]+/status/)(\d{13,20})(?:[^0-9].*)?$|^/tid.*$' % bot.me.username).search
_group_pattern = re.compile(r'(?:^(?:/?tid(?:@%s)?) ?|(?:https?://)?(?:twitter|x|vxtwitter|fxtwitter)\.com/[a-zA-Z0-9_]+/status/)(\d{13,20})(?:[^0-9].*)?$' % bot.me.username).search
@handler(
  'tid', 
  pattern=_pattern,
  info='获取推文 /tid <url/tid> [hide] [mark]',
)
async def _tid(event, text):
  if not event.message.is_private and not _group_pattern(text):
    return
  match = event.pattern_match
  if match.group(1) is None:
    return await event.reply(
      '用法: /tid <url/tid> [options]:\n'
      '获取推文\n'
      '- <url/tid>: 推文链接或 status id\n'
      '- [hide/简略]: 获取简略推文\n'
      '- [mark/遮罩]: 添加遮罩'
    )
  
  tid = match.group(1)
  options = util.string.Options(text, hide=('简略', '省略'), mark=('spoiler', '遮罩'))
  logger.info(f"{tid = }, {options = }")
  
  res = await get_twitter(tid)
  if type(res) == str:
    return await event.reply(res)
  if 'tombstone' in res.keys():
    logger.info('tombstone: %s', json.dumps(res))
    return await event.reply(res['tombstone']['text']['text'].replace('了解更多', ''))
  
  msg, full_text, time = parseTidMsg(res) 
  msg = msg if not options.hide else 'https://x.com/i/status/' + tid
  tweet = res["legacy"]
  
  medias = parseMedias(tweet)
  if len(medias) == 0:
    return await event.reply(msg, parse_mode='HTML')
    
  async with bot.action(event.chat_id, 'photo'):
    ms = []
    photos = util.Photos()
    videos = util.Videos()
    for i, ai in enumerate(medias):
      if ai["type"] == "photo":
        if (add := photos[ai['md5']]):
          add = _deal_file_id(add, options.mark)
        else:
          img = await util.getImg(ai['url'], headers=headers, ext=True)
          file = await bot.upload_file(img)
          add = types.InputMediaUploadedPhoto(
            file=file,
            spoiler=options.mark,
          )
        ms.append(add)
      else:
        url = ai["url"]
        md5 = ai['md5']
        if (add := videos.get(md5, None)):
          add = _deal_file_id(add, options.mark)
        else:
          path = await util.getImg(url, headers=headers, ext="mp4")
          
          video, duration, w, h, thumb = util.videoInfo(path)
          video = await bot.upload_file(video)
          thumb = await bot.upload_file(thumb)
          add = types.InputMediaUploadedDocument(
            file=video,
            spoiler=options.mark,
            thumb=thumb,
            mime_type='video/mp4',
            nosound_video=True,
            attributes=[
              types.DocumentAttributeVideo(duration=duration, w=int(w), h=int(h), supports_streaming=True), 
            ]
          )
        ms.append(add)
        
  res = await bot.send_file(
    event.message.chat_id,
    file=ms,
    reply_to=event.message,
    caption=msg,
    parse_mode='HTML',
  )
  with photos:
    with videos:
      for i, ai in enumerate(res):
        t = photos if ai.photo else videos
        t[medias[i]['md5']] = ai 
  
  message_id_bytes = res[0].id.to_bytes(4, 'big')
  sender_bytes = b'~' + event.sender_id.to_bytes(6, 'big', signed=True)
  tid_bytes = int(tid).to_bytes(8, 'big')
  await event.reply(
    '获取完成',
    buttons=[
      Button.inline('移除遮罩' if options.mark else '添加遮罩', b'mark_' + message_id_bytes + sender_bytes),
      Button.inline('详细描述' if options.hide else '简略描述', b'tid_' + message_id_bytes + b'_' + tid_bytes + sender_bytes),
    ]
  )
  raise events.StopPropagation
  
  
_button_pattern = re.compile(rb'tid_([\x00-\xff]{4,4})_([\x00-\xff]{8,8})(?:~([\x00-\xff]{6,6}))?$').match
@bot.on(events.CallbackQuery(
  pattern=_button_pattern
))
async def _event(event):
  peer = event.query.peer
  match = event.pattern_match
  message_id = int.from_bytes(match.group(1), 'big')
  tid = int.from_bytes(match.group(2), 'big')
  sender_id = None 
  if (t := match.group(3)):
    sender_id = int.from_bytes(t, 'big')
  logger.info(f'{message_id=}, {tid=}, {sender_id=}, {event.sender_id=}')
  
  if sender_id and event.sender_id and sender_id != event.sender_id:
    participant = await bot.get_permissions(peer, event.sender_id)
    if not participant.delete_messages:
      return await event.answer('只有消息发送者可以修改', alert=True)
  
  message = await bot.get_messages(peer, ids=message_id)
  if message is None:
    return await event.answer('消息被删除', alert=True)
  hide = '年' in message.message
  msg = f'https://x.com/i/status/{tid}'
  if not hide:
    res = await get_twitter(tid)
    if type(res) == str or 'tombstone' in res:
      if type(res) != str:
        res = res['tombstone']['text']['text'].replace('了解更多', '')
      return await event.answer(res, alert=True)
    msg, _, _ = parseTidMsg(res)
  try:
    await message.edit(msg, parse_mode='html')
  except errors.MessageNotModifiedError:
    logger.warning('MessageNotModifiedError')
      
  message = await event.get_message()
  buttons = message.buttons[0]
  text = '详细描述' if hide else '简略描述'
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
  

def _deal_file_id(file_id, spoiler: bool):
  media = utils.resolve_bot_file_id(file_id)
  media = utils.get_input_media(media)
  media.spoiler = spoiler
  return media
          