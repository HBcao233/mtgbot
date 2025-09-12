from telethon import events, Button
from plugin import Command
import psutil
import time

from util.log import logger


@Command('help', info='介绍与帮助')
async def help(event):
  text = f"""<b>Hi! 这里是小派魔!</b>
指令列表:
\u25c6 常规
\u25cf /ping
{'\u3000' * 3}查看小派魔是否存活
\u25cf /status
{'\u3000' * 3}查看小派魔运行状态
\u25cf /roll
{'\u3000' * 3}发动吧命运之骰
\u25cf /chat
{'\u3000' * 3}与小派魔对话
\u25cf /clear
{'\u3000' * 3}清除对话上下文
\u25cf /help
{'\u3000' * 3}显示此帮助

\u25c6 游戏
\u25cf /lighton
{'\u3000' * 3}点灯游戏

\u25c6 更多爬虫解析等功能仅限私聊使用"""

  if event.is_private:
    text = f"""<b>Hi! 这里是小派魔!</b>
指令列表:
\u25c6 常规
\u25cf /ping
{'\u3000' * 3}查看小派魔是否存活
\u25cf /status
{'\u3000' * 3}查看小派魔运行状态
\u25cf /roll
{'\u3000' * 3}发动吧命运之骰
\u25cf /chat
{'\u3000' * 3}与小派魔对话
\u25cf /clear
{'\u3000' * 3}清除对话上下文
\u25cf /settings
{'\u3000' * 3}小派魔设置
\u25cf /help
{'\u3000' * 3}显示此帮助

\u25c6 爬虫
\u25c6 发送url自动解析可爬取内容
\u25cf /pid
{'\u3000' * 3}获取p站作品
{'\u3000' * 3}( 类似 @Pixiv_bot )
\u25cf /tid
{'\u3000' * 3}获取推文
{'\u3000' * 3}( 类似 @twitter_loli_bot )
\u25cf /bill
{'\u3000' * 3}获取b站视频
{'\u3000' * 3}( 类似 @bilifeedbot )
\u25cf /douyin
{'\u3000' * 3}抖音视频解析
\u25cf /eid
{'\u3000' * 3}获取e站本子
\u25cf /nid
{'\u3000' * 3}获取n站本子
\u25cf /kid
{'\u3000' * 3}获取k站图片
\u25cf /misskey
{'\u3000' * 3}获取misskey作品
\u25cf /fanbox
{'\u3000' * 3}获取fanbox作品

\u25c6 音乐解析
\u25cf /qqmusic
{'\u3000' * 3}QQ音乐解析
\u25cf /qqmusic_search
{'\u3000' * 3}QQ音乐搜索
\u25cf /163music
{'\u3000' * 3}网易云音乐解析
\u25cf /163music_search
{'\u3000' * 3}网易云音乐搜索

\u25c6 游戏
\u25cf /lighton
{'\u3000' * 3}点灯游戏

对小派魔有任何建议或意见欢迎前往 <a href="https://t.me/HBcaoHouse">🍀派魔喵の家🍥</a> 私聊或评论喵！"""

  m = await event.reply(
    text,
    buttons=Button.url('源代码', 'https://github.com/HBcao233/mtgbot'),
    parse_mode='html',
  )
  if not m.is_private:
    bot.schedule_delete_messages(30, m.peer_id, [m.id, event.message.id])
  raise events.StopPropagation


@Command('ping', info='查看小派魔是否存活')
async def ping(event):
  m = await event.reply('小派魔存活中')
  if not m.is_private:
    bot.schedule_delete_messages(5, m.peer_id, [m.id, event.message.id])


@Command('status', info='查看小派魔服务器运行状态')
async def server_status(event):
  try:
    # 获取CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)

    # 获取内存使用情况
    mem = psutil.virtual_memory()
    mem_used = round(mem.used / (1024**2), 2)  # 转换为MB
    mem_total = round(mem.total / (1024**2), 2)
    mem_percent = mem.percent

    # 获取磁盘使用情况(使用根目录)
    disk = psutil.disk_usage('/')
    disk_used = round(disk.used / (1024**2), 2)
    disk_total = round(disk.total / (1024**2), 2)
    disk_percent = disk.percent

    # 获取系统启动时间
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime = str(time.strftime('%H小时%M分钟%S秒', time.gmtime(uptime_seconds)))

    # 构建回复消息
    reply_msg = (
      '**服务器状态**:\n'
      f'- **CPU使用率**: {cpu_percent}%\n'
      f'- **内存使用**: {mem_used}MB/{mem_total}MB ({mem_percent}%)\n'
      f'- **磁盘使用**: {disk_used}MB/{disk_total}MB ({disk_percent}%)\n'
      f'- **运行时长**: {uptime}\n'
    )

    m = await event.reply(reply_msg)
    if not m.is_private:
      bot.schedule_delete_messages(30, m.peer_id, [m.id, event.message.id])
  except Exception as e:
    logger.warn('获取服务器状态时出错', exc_info=1)
    m = await event.reply(f'获取服务器状态时出错: {e}')
    if not m.is_private:
      bot.schedule_delete_messages(5, m.peer_id, [m.id, event.message.id])
