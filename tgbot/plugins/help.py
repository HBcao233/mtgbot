from telethon import events, Button
from plugin import handler


@handler('help', info='介绍与帮助')
async def help(event):
  text = f'''\u250c{"\u2500" * 15}\u2510
\u2502<b>Hi! 这里是小派魔!</b>{" "*25} \u2502
\u251c{"\u2500" * 15}\u2524
\u251c指令列表{"\u2500" * 11}\u2524
\u251c常规{"\u2500" * 13}\u2524
\u2502 /help{" " * 44}\u2502
\u2502{" "*8}显示此帮助{" "*28}\u2502
\u2502 /ping{" "*44}\u2502
\u2502{" "*8}查看小派魔是否存活{" "*14}\u2502
\u2502 /status{" "*41}\u2502
\u2502{" "*8}查看小派魔运行状态{" "*14}\u2502
\u2502 /settings{" "*39}\u2502
\u2502{" "*8}小派魔设置{" "*27}\u2502
\u2502 /roll{" "*45}\u2502
\u2502{" "*8}发动吧命运之骰{" "*20}\u2502
\u2502 /chat{" "*44}\u2502
\u2502{" "*8}与小派魔对话{" "*24}\u2502
\u2502 /clear{" "*43}\u2502
\u2502{" "*8}清除对话上下文{" "*20}\u2502
\u251c爬虫{"\u2500"*13}\u2524
\u2502发送url自动解析可爬取内容{" "*10}\u2502
\u2502 /pid{" "*45}\u2502
\u2502{" "*8}获取p站作品{" "*25}\u2502
\u2502{" "*8}( 类似 @Pixiv_bot ){" "*15}\u2502
\u2502 /tid{" "*46}\u2502
\u2502{" "*8}获取推文{" "*31}\u2502
\u2502{" "*8}( 类似 @twitter_loli_bot ){" "*5}\u2502
\u2502 /bill{" "*45}\u2502
\u2502{" "*8}获取b站视频{" "*25}\u2502
\u2502{" "*8}( 类似 @bilifeedbot ){" "*11}\u2502
\u2502 /douyin{" "*41}\u2502
\u2502{" "*8}抖音视频解析{" "*25}\u2502
\u2502 /eid{" "*46}\u2502
\u2502{" "*8}获取e站本子{" "*25}\u2502
\u2502 /nid{" "*45}\u2502
\u2502{" "*8}获取n站本子{" "*25}\u2502
\u2502 /kid{" "*45}\u2502
\u2502{" "*8}获取k站图片{" "*25}\u2502
\u2502 /misskey{" "*38}\u2502
\u2502{" "*8}获取misskey{" "*25}\u2502
\u2502 /fanbox{" "*40}\u2502
\u2502{" "*8}获取fanbox作品{" "*20}\u2502
\u251c音乐{"\u2500"*13}\u2524
\u2502 /qqmusic{" "*38}\u2502
\u2502{" "*8}QQ音乐解析{" "*26}\u2502
\u2502 /qqmusic_search{" "*26}\u2502
\u2502{" "*8}QQ音乐搜索{" "*26}\u2502
\u2502 /163music{" "*36}\u2502
\u2502{" "*8}网易云音乐解析{" "*21}\u2502
\u2502 /163music_search{" "*24}\u2502
\u2502{" "*8}网易云音乐搜索{" "*21}\u2502
\u251c游戏{"\u2500"*13}\u2524
\u2502 /lighton{" "*40}\u2502
\u2502{" "*8}点灯游戏{" "*31}\u2502
\u2514{"\u2500" * 15}\u2518'''
  
  await event.reply(
    text,
    buttons=Button.url('源代码', 'https://github.com/HBcao233/mtgbot'),
    parse_mode='html',
  )
  raise events.StopPropagation


@handler('ping', info='查看小派魔是否存活')
async def ping(event):
  await event.reply('小派魔存活中')


@handler('status', info='查看小派魔服务器运行状态')
async def server_status(event):
  import psutil
  import time
  import platform

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

    # 获取系统信息
    def get_system_info():
      try:
        # Linux系统获取发行版信息
        if platform.system() == 'Linux':
          # 尝试读取/etc/os-release文件
          try:
            with open('/etc/os-release') as f:
              os_info = {}
              for line in f:
                if '=' in line:
                  k, v = line.strip().split('=', 1)
                  os_info[k] = v.strip('"')
            return f'{os_info.get("PRETTY_NAME", "Linux")} {platform.release()}'
          except Exception:
            # 如果读取失败，使用platform信息
            return f'Linux {platform.release()}'
        else:
          # 非Linux系统
          return f'{platform.system()} {platform.release()} {platform.version()}'
      except Exception:
        return f'{platform.system()} {platform.release()}'

    # 构建回复消息
    reply_msg = (
      '**服务器状态**:\n'
      f'- **CPU使用率**: {cpu_percent}%\n'
      f'- **内存使用**: {mem_used}MB/{mem_total}MB ({mem_percent}%)\n'
      f'- **磁盘使用**: {disk_used}MB/{disk_total}MB ({disk_percent}%)\n'
      f'- **运行时长**: {uptime}\n'
      f'- **系统信息**: {get_system_info()}'
    )

    await event.reply(reply_msg)

  except Exception as e:
    await event.reply(f'获取服务器状态时出错: {str(e)}')
