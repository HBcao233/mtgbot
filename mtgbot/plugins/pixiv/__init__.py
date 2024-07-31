from telethon import utils, types, events, errors, Button
import re 
import traceback
import asyncio
import os 

import config
import util
from util.log import logger
from util.progress import Progress
from plugin import handler
from .data_source import headers, get_pixiv, parse_msg, get_anime, get_telegraph


bot = config.bot
_pattern = re.compile(r'(?:^|^(?:/?pid(?:@%s)?) ?|(?:https?://)?(?:www\.)?(?:pixiv\.net/(?:member_illust\.php\?.*illust_id=|artworks/|i/)))(\d{6,12})(?:[^0-9].*)?$|^/(?:pid)$' % bot.me.username).search
_group_pattern = re.compile(r'(?:^(?:/?pid(?:@%s)?) ?|(?:https?://)?(?:www\.)?(?:pixiv\.net/(?:member_illust\.php\?.*illust_id=|artworks/|i/)))(\d{6,12})(?:[^0-9].*)?$' % bot.me.username).search
@handler('pid', 
  pattern=_pattern,
  info='获取p站作品 /pid <url/pid> [hide] [mark]',
)
async def _pixiv(event, text):
  if not event.message.is_private and not _group_pattern(text):
    return
  if event.message.photo or event.message.video:
    return
  match = event.pattern_match
  if not (pid := match.group(1)):
    return await event.reply(
      "用法: /pid <url/pid> [options]\n"
      "获取p站图片\n"
      "- <url/pid>: p站链接或pid\n"
      "- [hide/省略]: 省略图片说明\n"
      "- [mark/遮罩]: 给图片添加遮罩\n"
      "- [origin/原图]: 发送原图\n"
    )
    
  options = util.string.Options(text, hide=('简略', '省略'), mark=('spoiler', '遮罩'), origin='原图')
  logger.info(f"{pid = }, {options = }")
    
  mid = await event.reply('请等待...')
  res = await get_pixiv(pid)
  if isinstance(res, str):
    return await event.reply(res)
  msg = parse_msg(res, options.hide)
  try:
    if res['illustType'] == 2:
      return await send_animation(event, pid, msg, mid)
    else:
      count = res["pageCount"]
      if count < 11:
        res = await send_photos(event, res, msg, options, mid)
      else:
        url, msg = await get_telegraph(res)
        await mid.delete()
        return await bot.send_file(
          event.peer_id,
          caption=msg,
          parse_mode='HTML',
          file=types.InputMediaWebPage(
            url=url,
            force_large_media=True,
            optional=True,
          ),
          reply_to=event.message,
        )
  except PluginException as e:
    return await mid.edit(str(e))
  except:
    logger.error(traceback.format_exc())
    return await mid.edit('发送失败')
    
  if options.origin: 
    return
  
  message_id_bytes = res[0].id.to_bytes(4, 'big')
  sender_bytes = b'~' + event.sender_id.to_bytes(6, 'big', signed=True)
  pid_bytes = int(pid).to_bytes(4, 'big')
  await event.reply(
    '获取完成',
    buttons=[[
      Button.inline('移除遮罩' if options.mark else '添加遮罩', b'mark_' + message_id_bytes + sender_bytes),
      Button.inline('详细描述' if options.hide else '简略描述', b'pid_' + message_id_bytes + b'_' + pid_bytes + sender_bytes),
    ], 
    [Button.inline('获取原图', b'pidori_' + pid_bytes)],
    ]
  )
  
  
_button_pattern = re.compile(rb'pid_([\x00-\xff]{4,4})_([\x00-\xff]{4,4})(?:~([\x00-\xff]{6,6}))?$').match
@bot.on(events.CallbackQuery(
  pattern=_button_pattern
))
async def _(event):
  peer = event.query.peer
  match = event.pattern_match
  message_id = int.from_bytes(match.group(1), 'big')
  pid = int.from_bytes(match.group(2), 'big')
  sender_id = None 
  if (t := match.group(3)):
    sender_id = int.from_bytes(t, 'big')
  logger.info(f'{message_id=}, {pid=}, {sender_id=}, {event.sender_id=}')
  
  if sender_id and event.sender_id and sender_id != event.sender_id:
    participant = await bot.get_permissions(peer, event.sender_id)
    if not participant.delete_messages:
      return await event.answer('只有消息发送者可以修改', alert=True)
  
  message = await bot.get_messages(peer, ids=message_id)
  if message is None:
    return await event.answer('消息被删除', alert=True)
    
  hide = '):\n' in message.text
  res = await get_pixiv(pid)
  if isinstance(res, str):
    return await event.answer(res, alert=True)
  msg = parse_msg(res, hide)
  try:
    await message.edit(msg, parse_mode='html')
  except errors.MessageNotModifiedError:
    logger.warning('MessageNotModifiedError')
      
  message = await event.get_message()
  buttons = message.buttons
  text = '详细描述' if hide else '简略描述'
  index = 0
  for i, ai in enumerate(buttons[0]):
    if _button_pattern(ai.data):
      index = i
      data = ai.data
      break
  buttons[0][index] = Button.inline(text, data)
  
  try:
    await event.edit(buttons=buttons)
  except errors.MessageNotModifiedError:
    logger.warning('MessageNotModifiedError')
  await event.answer()
  

_ori_pattern = re.compile(rb'pidori_([\x00-\xff]{4,4})$').match
@bot.on(events.CallbackQuery(
  pattern=_ori_pattern
))
async def _(event):
  peer = event.query.peer
  match = event.pattern_match
  pid = int.from_bytes(match.group(1), 'big')
  message = await event.get_message()
  try:
    await event.edit(buttons=message.buttons[0])
  except errors.MessageNotModifiedError:
    logger.warning('MessageNotModifiedError')
  
  hide = ''
  for i in message.buttons[0]:
    if i.text == '详细描述':
      hide = 'hide'
      break
    if i.text == '简略描述':
      break
  
  await event.answer()
  event.message = message
  event.peer_id = peer 
  text = f'/pid {pid} origin {hide}'
  event.pattern_match = _pattern(text)
  await _pixiv(event, text)
  

class PluginException(Exception):
  pass 


async def send_animation(event, pid, msg, mid):
  async with bot.action(event.peer_id, 'file'):
    data = util.Animations()
    mid.edit('生成动图中...')
    if not (file := data[pid]):
      file = await get_anime(pid)
      if not file:
        return await event.reply('生成动图失败')
    
    bar = Progress(mid, prefix=f"上传中...")
    res = await bot.send_file(
      event.peer_id,
      file,
      reply_to=event.message,
      caption=msg,
      parse_mode='html',
      force_document=False,
      attributes=[types.DocumentAttributeAnimated()],
      progress_callback=bar.update
    )
    with data:
      data[pid] = res
    await mid.delete()
  
  
async def send_photos(event, res, msg, options, mid):
  pid = res['illustId']
  imgUrl = res["urls"]["regular"]
  if options.origin:
    imgUrl = res["urls"]["original"]
  count = res["pageCount"]
  data = util.Documents() if options.origin else util.Photos()
  bar = Progress(
    mid, total=count,
    prefix=f"正在获取 p1 ~ {count}",
  )
  
  async def get_img(i):
    nonlocal options, data, bar
    url = imgUrl.replace("_p0", f"_p{i}")
    key = f"{pid}_p{i}"
    if not options.origin:
      key += '_regular'
    if (file_id := data[key]):
      return util.media.file_id_to_media(file_id, options.mark)
    
    try:
      media = await util.getImg(url, saveas=key, ext=True, headers=headers)
    except Exception:
      logger.error(traceback.format_exc())
      raise PluginException(f'p{i} 图片获取失败')
    await bar.add(1)
    return await util.media.file_to_media(
      media, options.mark, 
      force_document=options.origin,
    )
  
  tasks = [get_img(i) for i in range(count)]
  result = await asyncio.gather(*tasks)
  async with bot.action(event.peer_id, 'photo'):
    try:
      m = await bot.send_file(
        event.peer_id, 
        result,
        caption=msg,
        parse_mode='html',
        reply_to=event.message
      )
    except Exception:
      logger.error(traceback.format_exc())
      raise PluginException("发送失败")
    
  with data:
    for i in range(count):
      key = f"{pid}_p{i}"
      if not options.origin:
        key += '_regular'
      data[key] = m[i]
  await mid.delete()
  return m
