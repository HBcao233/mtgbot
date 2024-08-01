from telethon import events, errors, types, Button
import re
import os.path
import traceback
import asyncio
from datetime import datetime
import ujson as json 

import config
import util
from util.log import logger
from plugin import handler
from .data_source import PluginException, get_post, parse_msg, parse_medias


bot = config.bot
_pattern = re.compile(r'(?:^/?fanbox(?:@%s)? |(?:https?://)?(?:(?:[a-z0-9]+\.)?fanbox\.cc/)(?:[@a-z0-9]+/)?(?:posts/)?)(\d+)|^/fanbox' % bot.me.username).match
@handler('fanbox', 
  pattern=_pattern,
  info="获取fanbox作品 /fanbox <url/postId> [hide] [mark]"
)
async def _fanbox(event, text):
  if event.message.photo or event.message.video:
    return
  match = event.pattern_match
  if not (pid := match.group(1)):
    return await event.reply(
      "用法: /fanbox <url/postId> [hide/简略] [mark/遮罩] [origin/原图]\n"
      "url/postId: fanbox链接或postId\n"
    )
  
  options = util.string.Options(text, hide=('简略', '省略'), mark=('spoiler', '遮罩'), origin='原图')
  mid = await event.reply("请等待...")
  
  try:
    res = await get_post(pid)
  except PluginException as e:
    return await mid.edit('错误: ' + str(e))
  logger.info(json.dumps(res))
  msg = parse_msg(res, options.hide)
  medias = parse_medias(res)
  if res['coverImageUrl']:
    img = await util.getImg(res['coverImageUrl'], ext=True)
    await bot.send_file(
      event.peer_id,
      img,
      caption=msg,
      reply_to=event.message,
      parse_mode='HTML',
    )
    await mid.delete()
    mid = await event.reply("请等待...")
  elif len(medias) == 0:
    return await mid.edit(msg, parse_mode='HTML')
  
  if res['feeRequired'] > 0:
    return await mid.edit(
      f"该投稿为付费内容 ({res['feeRequired']}日圓)"
    )
  
  try:
    if len(medias) < 11: 
      res = await send_photos(event, medias, msg, options)
      await mid.delete()
    else:
      url, msg = await get_telegraph(res, medias)
      await mid.delete()
      return await bot.send_file(
        event.peer_id,
        text=msg,
        parse_mode='HTML',
        reply_to=event.message,
        file=types.InputMediaWebPage(
          url=url,
          force_large_media=True,
          optional=True,
        ),
      )
  except PluginException as e:
    return mid.edit(str(e))
  
  if options.origin: 
    return
  message_id_bytes = res[0].id.to_bytes(4, 'big')
  sender_bytes = b'~' + event.sender_id.to_bytes(6, 'big', signed=True)
  pid_bytes = int(pid).to_bytes(4, 'big')
  await event.reply(
    '获取完成',
    buttons=[[
      Button.inline('移除遮罩' if options.mark else '添加遮罩', b'mark_' + message_id_bytes + sender_bytes),
      Button.inline('详细描述' if options.hide else '简略描述', b'fanbox_' + message_id_bytes + b'_' + pid_bytes + sender_bytes),
    ], 
    [Button.inline('获取原图', b'fanboxori_' + pid_bytes)],
    ]
  )


_button_pattern = re.compile(rb'fanbox_([\x00-\xff]{4,4})_([\x00-\xff]{4,4})(?:~([\x00-\xff]{6,6}))?$').match
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
  try:
    res = await get_post(pid)
  except PluginException as e:
    return await mid.edit('错误: ' + str(e))
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
  
  
_ori_pattern = re.compile(rb'fanboxori_([\x00-\xff]{4,4})$').match
@bot.on(events.CallbackQuery(
  pattern=_ori_pattern
))
async def _(event):
  peer = event.query.peer
  match = event.pattern_match
  pid = int.from_bytes(match.group(1), 'big')
  message = await event.get_message()
  try:
    await event.edit(buttons=message.buttons[:-1])
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
  text = f'/fanbox {pid} origin {hide}'
  event.pattern_match = _pattern(text)
  await _fanbox(event, text)
  

async def send_photos(event, medias, msg, options):
  data = util.Documents() if options.origin else util.Photos()
  
  async def get_img(i):
    nonlocal medias, data, options
    url = medias[i]['url']
    name = medias[i]['name']
    ext = medias[i]['ext']
    if not options.origin:
      url = medias[i]['thumbnail']
      name += '_thumbnail'
    if (file_id := data[name]):
      return util.media.file_id_to_media(file_id, options.mark)
      
    try:
      headers={
        'origin': 'https://www.fanbox.cc',
        'referer': 'https://www.fanbox.cc/',
      }
      img = await util.getImg(url, saveas=name, ext=ext, headers=headers)
      return await util.media.file_to_media(
        img, options.mark,
        force_document=options.origin,
      )
    except Exception:
      logger.error(traceback.format_exc())
      raise PluginException('图片获取失败')
      
  tasks = [get_img(i) for i in range(len(medias))]
  result = await asyncio.gather(*tasks)
  async with bot.action(event.peer_id, 'photo'):
    m = await bot.send_file(
      event.peer_id,
      result if len(result) > 0 else None,
      reply_to=event.message,
      caption=msg,
      parse_mode='html'
    )
  with data:
    for i in range(len(medias)):
      name = medias[i]['name']
      if not options.origin:
        name += '_thumbnail'
      data[name] = m[i]
  return m
        

async def get_telegraph(res, medias):
  data = util.Data('urls')
  now = datetime.now()
  pid = res['id']
  key = f'{pid}_{now:%m-%d}'
  if not (url := data[key]):
    content = []
    for i in medias:
      content.append({
        'tag': 'img',
        'attrs': {
          'src': i['url'],
        },
      })
   
    url = await util.telegraph.createPage(f"[fanbox] {pid} {res['title']}", content)
    with data:
      data[key] = url
    
  msg = (
    f"标题: {res['title']}\n"
    f"预览: {url}\n"
    f"作者: <a href=\"https://{res['creatorId']}.fanbox.cc/\">{res['user']['name']}</a>\n"
    f"数量: {len(medias)}\n"
    f"原链接: https://{res['creatorId']}.fanbox.cc/posts/{pid}"
  )
  return url, msg
  