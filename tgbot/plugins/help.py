from telethon import events, Button
from plugin import handler, Scope
import config
import filters


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
  buttons = [[Button.url('源代码', 'https://github.com/HBcao233/mtgbot')]]
  if event.is_private:
    buttons.append([Button.inline('Donate', b'donate')])
  await event.reply(
    '\n'.join(text),
    buttons=buttons,
  )
  raise events.StopPropagation


@handler('ping', info='查看小派魔是否存活')
async def ping(event):
  await event.reply('小派魔存活中')


donate_config_keys = [
  'donate_patreon_url',
  'donate_afdian_url',
  'donate_alipay_url',
]


@handler(
  'donate',
  enable=any(config.env.get(i, '') for i in donate_config_keys),
  info='捐助小派魔',
  scope=Scope.private(),
  filter=filters.PRIVATE,
)
@bot.on(events.CallbackQuery(pattern=rb'donate$'))
async def donate(event):
  await event.respond(
    '小派魔的服务是免费提供的，但小派魔随时可能因无力支付高昂的服务器费用而停止服务。\n'
    '您可以 /help 获取源代码搭建您自己的小派魔机器人\n'
    '或者如果您财力雄厚的话，可以<b>无偿小额捐助</b>来帮助小派魔存活，我将不胜感激\n\n'
    "The bot's service is provided for free, but it MAY be suspended at any time due to high cost of server\n"
    'You can get the source code by /help to build your bot\n'
    "Or you can <b>generously donate a small amount</b> to help the bot alive, I'd be deeply grateful",
    parse_mode='html',
    buttons=[
      [Button.url(i.replace('donate_', '').replace('_url', '').capitalize(), t)]
      for i in donate_config_keys
      if (t := config.env.get(i, ''))
    ],
  )
  raise events.StopPropagation
