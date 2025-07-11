<p align="center">
  <img src="https://avatars.githubusercontent.com/u/41500176?v=4&w=3840&q=75" alt="" width="100">
</p>
<div align="center">

# mtgbot

</div>
<p align="center">
  <a href="https://github.com/HBcao233/mtgbot-plugins">Plugins</a>
  ◆
  <a href="https://deepwiki.com/HBcao233/mtgbot">DeepWiki</a>
  ◆
  <a href="https://mtgbot.readthedocs.io">文档</a>
  <br/>
  <a href="https://docs.telethon.dev">Telethon 文档</a>
  ◆
  <a href="https://tl.telethon.dev">Telethon API</a>
</p>
<p align="center">
  <a href="https://raw.githubusercontent.com/hbcao233/mtgbot/main/LICENSE">
    <img src="https://img.shields.io/github/license/hbcao233/mtgbot" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/python-3.9+-blue?logo=python&logoColor=edb641" alt="python-3.9+">
</p>

一个基于 [Telethon](https://github.com/LonamiWebs/Telethon) 的、轻量化的 Telegram 机器人框架。 致力于用最简单的方式开发复杂机器人

是否厌倦了繁文缛节的 Nonebot 2, 是否看不惯反人类的依赖注入机制, 来试试轻量化的机器人框架 Mtgbot 吧

根目录下 tgbot 和 tgbot2 文件夹为两个机器人实例, 将 .env.example 改为 .env 并填写 token 即可使用

一个机器人实例最少由文件夹及 .env 文件以及 plugins 插件目录构成
&#x2500;
```
mtgbot
├─bot_name1
　　├─plugins: 插件目录
　　├─.env: 机器人配置
　　├─data: 数据目录, 运行后自动创建
　　　　├─cache: 缓存文件目录
　　　　├─messages.db: 接受到的消息id SQLite数据库
　　├─logs 日志目录, 运行后自动创建
　　├─bot.session: bot 会话文件
　　├─scopes.toml: [可选] Scopes配置
├─bot_name2
　　├─plugins: 插件目录
　　├─.env: 机器人配置
├─libs: 修改的依赖库
├─util: 一些工具方法
├─bot.py: TelegramClient子类Bot
├─main.py: 入口文件
├─requirement.txt: 依赖信息
├─tgbot.sh: bash管理脚本
├─tgbot.ps1: Powershell 7管理脚本
├─config.py:  配置实现, 一般情况下不作修改
├─plugin.py: 插件实现
```

### 基于本框架的插件 
* [mtgbot-plugins](https://github.com/HBcao233/mtgbot-plugins)

### demo
* [@hbcao4bot](https://t.me/hbcao4bot)
* [@hbcao2bot](https://t.me/hbcao2bot)

## 使用 Usage
Docker 运行
```
# 1.克隆仓库或手动下载
git clone https://github.com/HBcao233/mtgbot
# 2.进入仓库根目录
cd mtgbot
# 3.修改 mtgbot/tgbot/.env 文件, 填入机器人 token

# 4.构建 docker 镜像
docker compose build
# 5.创建容器并运行
docker compose up -d
# docker-compose.yml 中包含了两个机器人 tgbot 和 tgbot2, 将会一同创建并运行, 有需要可自行更改

# 重启
docker restart <容器名>
docker restart mtgbot
docker restart tgbot2

注意，
如果只修改py代码可以直接 docker restart 重启
如果修改了 .env, requirement.txt 或 libs 文件夹等, 
则需要进入项目目录 docker compose build && docker compose up -d 重新构建镜像

# 查看运行日志
docker logs mtgbot --tail 50
```

启动脚本运行
```
# 查看包安装目录 (显示信息中的 Location 项)
pip show telethon
# 复制覆盖 telethon 依赖库, 修改部分文件以实现如 解析<blockquote expandable></blockquote> 等功能
cp -r libs/telethon <site-package-location>


# 参数运行 tgbot.sh 可以选择操作
tgbot.sh [status|start|restart|stop|log|ps] [botname]

# 需要 Powershell 7 
tgbot.ps1 <start|restart|stop|status|log>
```

## 开发 Development
一个最简单 Hello World 插件 belike

更多指南详见 <a href="https://mtgbot.readthedocs.io">文档</a>
```
from plugin import Command

@Command('hello', info='Hello World!')
async def _hello(event):
  await event.reply('Hello World!')
```


## 依赖 Dependencies
* [Telethon](https://github.com/LonamiWebs/Telethon)
* [httpx](https://github.com/encode/httpx)
* [rlottie-python](https://github.com/laggykiller/rlottie-python)
* [ffmpeg](https://github.com/ffmpeg/ffmpeg)
* [opencv-python](https://github.com/opencv/opencv-python)
* [moviepy](https://github.com/Zulko/moviepy)