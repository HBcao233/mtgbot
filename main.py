import builtins
import asyncio
import time
import importlib

import config
import util
from plugin import load_plugins
from util.log import logger
from bot import Bot


#: Bot: Bot (`TelegramClient <https://docs.telethon.dev/en/stable/modules/client.html#telethon-client>`_ 子类) 实例, 注入 builtins
bot: Bot


if __name__ == '__main__':
  if len(config.token) < 36 or ':' not in config.token:
    raise ValueError('请提供正确的 bot token')
  if not config.api_id or not config.api_hash:
    raise ValueError('请提供正确的 api_id 和 api_hash')
  logger.info(
    f'当前 bot_token={config.token.split(":")[0] + "*" * 35}, api_id={config.api_id}, proxy={config.proxy}'
  )

  try:
    # 创建 bot
    bot: Bot = Bot(
      util.getFile('bot.session'),
      config.api_id,
      config.api_hash,
      proxy=config.proxy,
    ).start(bot_token=config.token)
    config.bot = bot
    # 将bot变量添加到 builtin 方便使用
    builtins.bot = bot
  except ConnectionError:
    logger.critical('连接错误', exc_info=1)
    exit(1)

  start_time = time.perf_counter()
  # 加载内部模块
  config.internal = importlib.import_module('internal')
  # 加载插件
  load_plugins()
  logger.info(f'插件载入完成, 用时: {time.perf_counter() - start_time}s')
  # 初始化
  bot.loop.create_task(config.internal._init())
  
  for i in bot.start_funcs:
    try:
      bot.loop.create_task(i())
    except Exception as e:
      logger.exception('创建启动函数错误')
  
  try:
    bot.run_until_disconnected()
  except asyncio.exceptions.CancelledError:
    pass
  except KeyboardInterrupt:
    pass
