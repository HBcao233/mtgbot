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
    '. /status 查看服务器运行状态',
    '. /status 查看小派魔是否还活着',
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
        mem_used = round(mem.used / (1024 ** 2), 2)  # 转换为MB
        mem_total = round(mem.total / (1024 ** 2), 2)
        mem_percent = mem.percent
        
        # 获取磁盘使用情况(使用根目录)
        disk = psutil.disk_usage('/')
        disk_used = round(disk.used / (1024 ** 2), 2)
        disk_total = round(disk.total / (1024 ** 2), 2)
        disk_percent = disk.percent
        
        # 获取系统启动时间
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime = str(time.strftime("%H小时%M分钟%S秒", time.gmtime(uptime_seconds)))
        
        # 获取系统信息
        def get_system_info():
            try:
                # Linux系统获取发行版信息
                if platform.system() == "Linux":
                    # 尝试读取/etc/os-release文件
                    try:
                        with open('/etc/os-release') as f:
                            os_info = {}
                            for line in f:
                                if '=' in line:
                                    k, v = line.strip().split('=', 1)
                                    os_info[k] = v.strip('"')
                        return f"{os_info.get('PRETTY_NAME', 'Linux')} {platform.release()}"
                    except:
                        # 如果读取失败，使用platform信息
                        return f"Linux {platform.release()}"
                else:
                    # 非Linux系统
                    return f"{platform.system()} {platform.release()} {platform.version()}"
            except:
                return f"{platform.system()} {platform.release()}"
        
        # 构建回复消息
        reply_msg = (
            "🖥️ 服务器状态:\n"
            f"⚡ CPU使用率: {cpu_percent}%\n"
            f"💾 内存使用: {mem_used}MB/{mem_total}MB ({mem_percent}%)\n"
            f"💽 磁盘使用: {disk_used}MB/{disk_total}MB ({disk_percent}%)\n"
            f"⏱️ 运行时长: {uptime}\n"
            f"🐧 系统信息: {get_system_info()}"
        )
        
        await event.reply(reply_msg)
    
    except Exception as e:
        await event.reply(f"获取服务器状态时出错: {str(e)}")
