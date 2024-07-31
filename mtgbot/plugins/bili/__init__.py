from telethon import Button
import re 

import config
import util
from util.log import logger
from plugin import handler
from .data_source import headers, get_bili, parse_msg, get_video


bot = config.bot
_pattern = re.compile(r"(?:^|^(?:/?bili(?:@%s)?) ?|(?:https?://)?bilibili\.com/video/)(av\d{1,11}|BV[0-9a-zA-Z]{8,12})|(?:b23\.tv\\?/((?![0-9]{7,7})[0-9a-zA-Z]{7,7}))|^/bili$" % bot).search
@handler(
  'bili',
  pattern=_pattern,
  info='av号或bv号获取视频',
)
async def _(event, text):
  if not event.message.is_private and not _group_pattern(text):
    return
  if event.message.photo or event.message.video:
    return
  match = event.pattern_match
  if match.group(1) is None and match.group(2) is None:
    return await event.reply(
      "用法: /bill <aid/bvid>", 
    )
  options = util.string.Options(text, nocache=(), mark=('spoiler', '遮罩'))
  
  flag = False
  if match.group(2):
    r = await util.get(
      'https://b23.tv/'+ match.group(2),
      follow_redirects=True,
      headers=headers,
    )
    text = str(r.url)
    match = _pattern(text.split('?')[0])
    flag = True
    
  p = 1
  g = match.group(1)
  aid = ''
  bvid = ''
  if 'av' in g:
    aid = g.replace('av', '')
  else:
    bvid = g
    
  if (match1 := re.search(r'(?:\?|&)p=(\d+)', text)):
    if (_p := int(match1.group(1))) > 1:
      p = _p 
      
  if flag:
    await event.reply(
      f'https://www.bilibili.com/video/{bvid}' + ('?p=' + str(p) if p>1 else ''), 
    )
    
  mid = await event.reply("请等待...")
  res = await get_bili(bvid, aid)
  if isinstance(res, str):
    return await mid.edit('视频不存在')
  bvid, aid, cid, title, msg = parse_msg(res, p)
  logger.info(f'{bvid} av{aid} P{p} cid: {cid}')
  
  data = util.Videos()
  key = bvid
  if p > 1:
    key += '_p' + str(p)
  if (file_id := data.get(key, None)) or options.nocache:
    media = util.media.file_id_to_media(file_id, options.mark)
  else:
    file = await get_video(bvid, aid, cid)
    media = await util.media.file_to_media(file, options.mark)
  
  await mid.delete()
  
  async with bot.action(event.chat_id, 'video'):
    
    res = await bot.send_file(
      event.chat_id,
      media,
      reply_to=event.message,
      caption=msg,
      parse_mode='HTML',
    )
  message_id_bytes = res.id.to_bytes(4, 'big')
  sender_bytes = b'~' + event.sender_id.to_bytes(6, 'big', signed=True)
  await res.edit(buttons=Button.inline('移除遮罩' if options.mark else '添加遮罩', b'mark_' + message_id_bytes + sender_bytes))
  with data:
    data[key] = res
 