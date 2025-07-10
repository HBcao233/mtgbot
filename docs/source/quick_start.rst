
快速上手
========

上手 mtgbot 只需两步

1. 创建 xxxbot/.env 

2. 使用 tgbot脚本 或 Docker  启动bot

创建 .env
---------

创建 ``xxxbot/.env``, 例如:

.. code-block:: text
  
  # Bot Token, get it by chating with @BotFather
  token = 1234567890:abcdefghijklmnopqrstuvwxzyABCDEFGHIJ
  debug = 0
  # 时区
  TZ = "Asia/Shanghai"
  
  # 公用api, 如果遇到 ApiIdPublishedFloodError 无法登录请修改为自己在 my.telegram.org 申请到的 api
  api_id = 4
  api_hash = 014b35b6184100b085b0d0572f9b5103
  
  # settings命令提示信息
  settings_caption = 设置小派魔的运行参数
  
  # http / socks5
  proxy_type = http
  proxy_host = localhost
  proxy_port = 
  proxy_username = 
  proxy_password =
  
  telegraph_author_name = 小派魔
  telegraph_author_url = https://t.me/hbcao1bot
  # 请参考 https://telegra.ph/api 来获取 
  telegraph_access_token = 


tgbot 脚本运行 (推荐)
----------------------
运行 ``tgbot.sh/tgbot.ps1 start xxxbot`` 即可 

Linux
~~~~~~

.. code-block:: bash
  
  :linenos:
  # 启动 bot
  tgbot.sh start <botname>
  # 停止
  tgbot.sh stop <botname>
  # 重启
  tgbot.sh restart <botname>
  # 查看所有bot运行状态
  tgbot.sh status
  # 查看bot日志
  tgbot.sh log
  # 快捷 ps
  tgbot.sh ps
  # 特别的, bash脚本无参数运行时可进行选择
  tgbot.sh

Windows
~~~~~~~

需要安装 Powershell 7

.. code-block:: bat
  :linenos:
  
  # 启动 bot
  tgbot.ps1 start <botname>
  # 停止
  tgbot.ps1 stop <botname>
  # 重启
  tgbot.ps1 restart <botname>
  # 查看所有bot运行状态
  tgbot.ps1 status
  # 查看bot日志
  tgbot.ps1 log


Docker 运行 (备选)
------------------
1. 修改 ``docker-compose.yml``

.. code-block:: yaml
  
  version: '3'

  services:
    tgbot:
      container_name: xxxbot
      volumes:
        - .:/xxxbot
      env_file:
        - xxxbot/.env
      environment:
        BOT_HOME: xxxbot
        TZ: Asia/Shanghai
  
      build: .
      stop_signal: SIGINT

2. 使用 docker-compose 命令运行

.. code-block:: bash 
  :linenos:
  
  # 构建镜像并运行
  docker-compose build && docker-compose up -d

.. important:: 
  如果只修改 python 代码可以直接 docker restart 重启 
  
  如果修改了 .env, requirements.txt 或 libs 文件夹等 docker 加载内容
  
  则需要进入项目目录 docker compose build && docker compose up -d 重新构建镜像

3. docker 常用命令

.. code-block:: bash
  :linenos:
  
  # 重启
  docker restart <container_name>
  # 查看运行日志
  docker logs <container_name> --tail 50


python 直接运行 (不推荐)
------------------------

.. code-block:: bash 
  :linenos:
  
  python main.py xxxbot
