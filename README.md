# tgbot
一个基于 telethon 的 Telegram 机器人框架

* 解析 pixiv.net, x.com, e-hentai.org, exhentai.org, kemono.su 图片/视频等发送至 tg
* 转换动图和视频, 动态贴纸
* 传话来者的消息给主人

demo: [@hbcao1bot](https://t.me/hbcao1bot)
demo: [@hbcao2bot](https://t.me/hbcao2bot)

旧仓库: 
* https://github.com/HBcao233/tgbot
* https://github.com/HBcao233/tgbot2

其他插件: https://github.com/HBcao233/mtgbot-plugins

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
```

## 依赖 Dependencies
* [Telethon](https://github.com/LonamiWebs/Telethon)
* [httpx](https://github.com/encode/httpx)
* [lottie2gif](https://github.com/rroy233/lottie2gif)
