from telethon import events, Button

import config
from plugin import handler


@handler('help', info='介绍与帮助')
async def help(event):
  await event.reply(
    "Hi! 这里是小派魔! \n"
    "指令列表: \n"
    "/pid <url/pid>: 获取p站作品 (类似 @Pixiv_bot\n"
    "/tid <url/tid>: 获取推文 (类似 @TwPicBot\n"
    "/bill <url/aid/bvid>: 获取b站视频 (类似 @bilifeedbot\n"
    "/eid <url>: e站爬取\n"
    "/kid <url>: kemono爬取\n"
    "/roll [min=0][ -~/][max=9]: 返回一个min~max的随机数（默认0-9）\n",
    buttons=Button.url('源代码', 'https://github.com/HBcao233/mtgbot')
  )
  raise events.StopPropagation
  