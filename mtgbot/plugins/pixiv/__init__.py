from telethon import events
import re 

import config
import util
from util.log import logger
from plugin import handler


bot = config.bot
_p = r'(?:^|^(?:pid|PID) ?|(?:https?://)?(?:www\.)?(?:pixiv\.net/(?:member_illust\.php\?.*illust_id=|artworks/|i/)))(\d{6,12})(?:[^0-9].*)?$'
_pattern = re.compile(_p)
_group_pattern = re.compile(_p.replace(r'(?:^|', r'^(?:'))
@handler('pixiv', 
  pattern=_pattern.search,
  info='获取p站作品 /pid <url/pid> [hide] [mark]',
)
async def _pixiv(event):
  message = event.message
  if message.is_private:
    match = event.pattern_match
  else:
    match = _group_pattern.search(text)
  if not match:
    return event.reply(
      "用法: /pid <url/pid> [hide/省略] [mark/遮罩] [origin/原图]\n"
        "url/pid: p站链接或pid\n"
        "[hide/省略]: 省略图片说明\n"
        "[mark/遮罩]: 给图片添加遮罩\n"
        "[origin/原图]: 发送原图\n"
        "私聊小派魔时可以省略/tid，直接发送<url/pid>哦\n",
    )
    
  pid = match.group(1)
  tid = match.group(1)
  options = util.string.Options(text, hide=('简略', '省略'), mark=('spoiler', '遮罩'), origin='原图')
  logger.info(f"{pid = }, {options = }")
    
  
  raise events.StopPropagation
  
  