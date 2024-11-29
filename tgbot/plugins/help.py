from telethon import events, Button
from plugin import handler


@handler('help', info='介绍与帮助')
async def help(event):
  text = [
    'Hi! 这里是小派魔! ',
    '指令列表: ',
    '· /pid <url/pid>: 获取p站作品 (类似 @Pixiv_bot',
    '· /tid <url/tid>: 获取推文 (类似 @TwPicBot',
    '· /bill <url/aid/bvid>: 获取b站视频 (类似 @bilifeedbot',
    '· /eid <url>: e站爬取',
    '· /kid <url>: kemono爬取',
    '· /roll [min=0][ -~/][max=9]: 返回一个min~max的随机数（默认0-9）',
  ]
  if event.is_private:
    text.extend(
      [
        '· /settings: 参数设置',
        '· 收到图片后选择合并图片按钮, 可合并多张图片或创建Telegraph (建议先 /settings 设置 Telegraph 作者)',
      ]
    )
  await event.reply(
    '\n'.join(text),
    buttons=Button.url('源代码', 'https://github.com/HBcao233/mtgbot'),
  )
  raise events.StopPropagation


@handler('ping', info='查看小派魔是否存活')
async def ping(event):
  await event.reply('小派魔存活中')
