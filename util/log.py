import logging
import sys
import os
import re
import time
import config
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from zoneinfo import ZoneInfo 


__all__ = ['logger', 'default_handler', 'file_handler']

tz = config.env.get('TZ', '') or 'Asia/Shanghai'
timezone = ZoneInfo(tz)
flag = True
logs_dir = os.path.join(config.botHome, 'logs/')
if not os.path.isdir(logs_dir):
  try:
    os.mkdir(logs_dir)
  except FileNotFoundError:
    print('Warning: logs 文件夹创建失败')
    flag = False

logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('telethon.client.users').setLevel(logging.ERROR)
logging.getLogger('telethon.client.updates').setLevel(logging.ERROR)
logging.getLogger('telethon.network.mtprotosender').setLevel(logging.ERROR)
logging.getLogger('telethon.extensions.messagepacker').setLevel(logging.ERROR)


def tz_converter(sec, what):
  now = datetime.now(timezone)
  return now.timetuple()


logging.Formatter.converter = tz_converter


main_format = (
  '[%(asctime)s][%(name)s<%(module)s:%(lineno)d>][%(levelname)s]: %(message)s'
)
main_formater = logging.Formatter(main_format)
main_level = logging.INFO if not config.debug else logging.DEBUG
logging.basicConfig(
  format=main_format,
  level=main_level,
)


def default_handler_filter(record):
  if record.levelno == 10:
    return False
  return True


def file_handler_filter(record):
  if record.levelno == 10:
    return False
  if record.name == 'mtgbot.plugin.load' and record.levelno == 20:
    return False
  return True


def debug_handler_filter(record):
  if record.levelno == 10:
    return True
  return False


class TimedHandler(TimedRotatingFileHandler):
  def __init__(self, name='', backupCount=30, encoding='utf-8', errors=None):
    if not name:
      self.base_name = '.log'
    else:
      self.base_name = '.' + name + '.log'
    suffix = '%Y-%m-%d'  # 不能含有 .

    currentTime = int(time.time())
    timeTuple = time.localtime(currentTime)
    filename = time.strftime(suffix, timeTuple) + self.base_name

    super().__init__(
      os.path.join(logs_dir, filename),
      'MIDNIGHT',
      1,
      backupCount,
      encoding=encoding,
      delay=False,
      utc=False,
      atTime=None,
      errors=errors,
    )

    self.suffix = suffix
    self.extMatch = re.compile(
      r'^\d{4}-\d{2}-\d{2}' + re.escape(self.base_name) + r'$', re.ASCII
    )

  def namer(
    self, default_name
  ):  # default_name = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
    path, filename = os.path.split(default_name)
    return os.path.join(path, filename.split('.')[-1] + self.base_name)

  def rotator(self, source, dest):
    self.baseFilename = os.path.abspath(os.fspath(dest))


#: logging.StreamHandler: 默认日志处理器
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(main_formater)
default_handler.setLevel(main_level)
default_handler.addFilter(default_handler_filter)

#: 文件日志处理器
file_handler: TimedHandler
if flag:
  file_handler = TimedHandler()
  file_handler.setFormatter(main_formater)
  file_handler.setLevel(main_level)
  file_handler.addFilter(file_handler_filter)

#: debug 文件日志处理器
debug_handler: TimedHandler

if config.debug:
  debug_handler = TimedHandler('debug')
  debug_handler.setFormatter(main_formater)
  debug_handler.setLevel(main_level)
  debug_handler.addFilter(debug_handler_filter)

#: 全局 logger 日志记录器
logger = logging.getLogger('mtgbot')
logger.setLevel(main_level)
root_logger = logging.getLogger('root')
if not logger.handlers:
  # 输出日志到命令行/docker logs
  root_logger.handlers = []
  root_logger.addHandler(default_handler)

  # 输出至 logs 文件夹
  if flag:
    root_logger.addHandler(file_handler)
  if config.debug:
    root_logger.addHandler(debug_handler)
