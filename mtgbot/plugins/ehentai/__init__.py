from telethon import types
import re
import traceback
import asyncio
from bs4 import BeautifulSoup
import ujson as json
from datetime import datetime

import config
import util
from util.log import logger
from plugin import handler
from .data_source import headers, parseEidSMsg, parseEidGMsg, parsePage
from util.progress import Progress


bot = config.bot
_pattern = re.compile(r'^/?(?:eid)? ?(?:https?://)?(e[x-])hentai\.org/([sg])/([0-9a-z]+)/([0-9a-z-]+)|^/eid').match
@handler('eid',
  pattern=_pattern,
  info="e站爬取 /eid <url> [hide] [mark]"
)
async def eid(event, text):
  if event.message.photo or event.message.video:
    return
  match = event.pattern_match
  arr = [match.group(i) for i in range(1, 5)]
  if arr[1] not in ['s', 'g']:
    return await event.reply("请输入e站 url")
  
  options = util.string.Options(text, nocache=())
  
  # 单页图片
  if arr[1] == "s":
    r = await util.get(text, headers=headers)
    html = r.text
    if "Your IP address has been" in html:
      return await event.reply("梯子IP被禁，请联系管理员更换梯子")
    if "Not Found" in html:
      return await event.reply("页面不存在")

    msg, url = parseEidSMsg(text, html)
    async with bot.action(event.peer_id, 'photo'):
      img = await util.getImg(url, proxy=True, headers=headers)
      await bot.send_file(
        event.peer_id,
        img,
        caption=msg,
        reply_to=event.message,
      )

  # 画廊
  if arr[1] == "g":
    mid = await event.reply("请等待...")
    r = await util.get(text, params={'p': 0}, headers=headers)
    html0 = r.text
    if "Your IP address has been" in html0:
      return await mid.edit("IP被禁")
    if "Not Found" in html0:
      return await mid.edit("页面不存在")
    
    soup = BeautifulSoup(html0, "html.parser")
    title, num, magnets = await parseEidGMsg(text, soup)
    logger.info(title)
    if not title:
      return await mid.edit('获取失败')
    
    now = datetime.now()
    key = '/'.join(arr) + f'_{now:%m-%d}'
    logger.info(key)
    with util.Data('urls') as data:
      if not (url := data[key]) or options.nocache:
        bar = Progress(mid)
        url = await parsePage(text, soup, title, num, options.nocache, bar)
        if not url:
          return await mid.edit('获取失败')
        data[key] = url
    
    msg = (
      f'标题: <code>{title}</code>\n'
      f'预览: <a href="{url}">{url}</a>\n'
      f"数量: {num}\n" 
      f"原链接: {text}"
    )
    if len(magnets) > 0:
      msg += "\n磁力链："
    for i in magnets:
      msg += f"\n· <code>{i}</code>"
    
    await bot.send_file(
      event.peer_id,
      caption=msg,
      reply_to=event.message,
      parse_mode="HTML",
      file=types.InputMediaWebPage(
        url=url,
        force_large_media=True,
        optional=True,
      ),
    )
    await mid.delete()
