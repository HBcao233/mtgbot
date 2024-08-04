# tgbot
一个基于 telethon 的 Telegram 机器人框架

根目录下 mtgbot 和 tgbot2 文件夹为两个机器人实例, 每个实例需在 docker-compose.yml 中注册，并且文件夹下需要有  .env 文件以及 plugins 插件目录

### 基于本框架的插件 
* [mtgbot-plugins](https://github.com/HBcao233/mtgbot-plugins)

### demo
* [@hbcao1bot](https://t.me/hbcao1bot)
* [@hbcao2bot](https://t.me/hbcao2bot)

### 旧仓库
* [tgbot](https://github.com/HBcao233/tgbot)
* [tgbot1](https://github.com/HBcao233/tgbot2)
* [tgbot-plugins](https://github.com/HBcao233/tgbot-plugins)

## 使用 Usage
```
# 1.克隆仓库或手动下载
git clone https://github.com/HBcao233/mtgbot
# 2.进入仓库根目录
cd mtgbot
# 3.修改 mtgbot/.env 文件, 填入机器人 token

# 4.构建 docker 镜像
docker compose build
# 5.创建容器并运行
docker compose up -d
# docker-compose.yml 中包含了两个机器人 mtgbot 和 tgbot2, 将会一同创建并运行, 有需要可自行更改

# 重启
docker restart <容器名>
docker restart mtgbot
docker restart tgbot2

# 查看运行日志
docker logs mtgbot

注意，
如果只修改py代码可以直接 docker restart 重启
如果修改了 .env, requirement.txt 或 libs 文件夹等, 
则需要进入项目目录 docker compose build && docker compose up -d 重新构建镜像
```

## 依赖 Dependencies
* [Telethon](https://github.com/LonamiWebs/Telethon)
* [httpx](https://github.com/encode/httpx)
* [rlottie-python](https://github.com/laggykiller/rlottie-python)
* [ffmpeg](https://github.com/ffmpeg/ffmpeg)
* [opencv-python](https://github.com/opencv/opencv-python)
* [moviepy](https://github.com/Zulko/moviepy)