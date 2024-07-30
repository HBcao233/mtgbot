from telethon import events, types, functions, utils, Button
import re 
import os

import config
import util
from util.log import logger
from plugin import handler
from .data_source import headers, get_twitter, parseTidMsg, parseMedias


bot = config.bot
_p = r'(?:^|^(?:/?tid|Tid|TID) ?|(?:https?://)?(?:twitter|x|vxtwitter|fxtwitter)\.com/[a-zA-Z0-9_]+/status/)(\d{13,})(?:[^0-9].*)?$'
_pattern = re.compile(_p)
_group_pattern = re.compile(_p.replace(r'(?:^|', r'(?:'))
@handler(
  'tid', 
  pattern=_pattern.search,
  info='获取推文 /tid <url/tid> [hide] [mark]',
)
async def _tid(event, text):
  message = event.message
  if message.is_private:
    match = event.pattern_match
  else:
    match = _group_pattern.search(text)
  if not match:
    return event.reply('用法: /tid <url/tid> [hide] [mark] 获取推文\n  hide: 获取简略推文\n  mark: 添加遮罩')
  logger.info(match.group(0))
  tid = match.group(1)
  options = util.string.Options(text, hide=('简略', '省略'), mark=('spoiler', '遮罩'))
  logger.info(f"{tid = }, {options = }")
  
  res = await get_twitter(tid)
  if type(res) == str:
    return await event.reply(res)
  if 'tombstone' in res.keys():
    logger.info(json.dumps(res))
    return await event.reply(res['tombstone']['text']['text'])
  
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
        if not (add := photos[ai['md5']]):
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
        if not (add := videos.get(md5, None)):
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
  
  raise events.StopPropagation
  