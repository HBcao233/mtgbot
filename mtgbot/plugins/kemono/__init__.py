from telethon import types, Button
import re
import traceback
import os
import asyncio

import config
import util
from util.log import logger
from util.progress import Progress
from plugin import handler
from .data_source import parse_msg, parse_page


bot = config.bot
_pattern = re.compile(r"^/?(?:kid(?:@%s)?)? ?(?:(?:https://)?kemono\.(?:party|su)/)?([a-z]+)(?:(?:/user)?/(\d+))?(?:/post)?/(\d+)|^/kid" % bot.me.username).match
@handler('kid',
  pattern=_pattern,
  info="kenomo爬取 /kid <url>"
)
async def _kid(event, text):
  if event.message.photo or event.message.video:
    return
  match = event.pattern_match
  if not (_kid := match.group(3)):
    return await event.reply(
      "用法: /kid <kemono_url>"
    )
  options = util.string.Options(text, nocache=(), mark=('遮罩', 'spoiler'))
  source = match.group(1)
  uid = match.group(2)
  kid = f'https://kemono.su/{source}'
  if uid: kid += f'/user/{uid}'
  kid += f'/post/{_kid}' 
  mid = await event.reply("请等待...")
  
  r = await util.get(kid)
  if r.status_code != 200:
    return await event.reply('请求失败')
  try:
    title, user_name, user_url, attachments, files = parse_msg(kid, r.text)
  except Exception as e:
    logger.warning(traceback.format_exc())
    return await mid.edit(str(e))
  
  # uid = user_url.split('/')[-1]
  # if source == 'fanbox' and len(files) > 1:
  #  files = files[1:]
  if len(files) > 10:
    key = f'kemono_{source}_{_kid}'
    with util.Data('urls') as data:
      if not (url := data[key]) or nocache:
        url = await parse_page(title, files, options.nocache)
    
    msg = (
      f'标题: {title}\n'
      f'作者: <a href="{user_url}">{user_name}</a>\n'
      f'预览: {url}\n'
      f'原链接: {kid}'
    )
    if attachments:
      msg += '\n' + attachments
    await bot.send_file(
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
    return await mid.delete()
  
  bar = Progress(mid, total=len(files), prefix='图片下载中...')
  msg = (
    f'<a href="{kid}">{title}</a> - '
    f'<a href="{user_url}">{user_name}</a>'
  )
  if attachments:
    msg += '\n' + attachments
  
  data = util.Photos()
  async def get_media(i):
    nonlocal files, data, options
    key = f'kemono_{source}_{_kid}_p{i}'
    if (file_id := data[key]):
      return util.media.file_id_to_media(file_id, options.mark)
    url = files[i]['thumbnail']
    ext = os.path.splitext(url)[-1]
    if ext == '.gif':
      url = files[i]['url']
    img = await util.getImg(url, saveas=key, ext=True)
    await bar.add(1)
    return await util.media.file_to_media(img, options.mark)
  
  bar.set_prefix('发送中...')
  tasks = [get_media(i) for i in range(len(files))]
  medias = await asyncio.gather(*tasks)
  async with bot.action(event.peer_id, 'photo'):
    res = await bot.send_file(
      event.peer_id,
      medias,
      caption=msg,
      parse_mode='html',
      reply_to=event.message,
      progress_callback=bar.update
    )
  await mid.delete()
  with data:
    for i, ai in enumerate(res):
      key = f'kemono_{source}_{_kid}_p{i}'
      data[key] = ai
  
  message_id_bytes = res[0].id.to_bytes(4, 'big')
  sender_bytes = b'~' + event.sender_id.to_bytes(6, 'big', signed=True)
  await event.reply(
    '获取完成',
    buttons=[
      Button.inline('移除遮罩' if options.mark else '添加遮罩', b'mark_' + message_id_bytes + sender_bytes),
    ]
  )