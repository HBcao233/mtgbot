import logging
import sys
import io
import os
import re
import time
import config
from datetime import datetime
from logging.handlers import BaseRotatingHandler
from zoneinfo import ZoneInfo 


__all__ = ['logger', 'default_handler', 'file_handler']

#: 时区字符串
tz = config.env.get('TZ', '') or 'Asia/Shanghai'
#: 时区对象
timezone = ZoneInfo(tz)
#: 是否启用文件日志处理器
enable_file_handler = True
#: logs 文件夹路径
logs_dir = os.path.join(config.botHome, 'logs/')
if not os.path.isdir(logs_dir):
  try:
    os.mkdir(logs_dir)
  except FileNotFoundError:
    print('Warning: logs 文件夹创建失败')
    enable_file_handler = False

# 设置其他库的logger 日志等级
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('telethon.client.users').setLevel(logging.ERROR)
logging.getLogger('telethon.client.updates').setLevel(logging.ERROR)
logging.getLogger('telethon.network.mtprotosender').setLevel(logging.ERROR)
logging.getLogger('telethon.extensions.messagepacker').setLevel(logging.ERROR)


def tz_converter(self, what):
  """
  时区转换器
  """
  now = datetime.now(timezone)
  return now.timetuple()


logging.Formatter.converter = tz_converter


class MainFormatter(logging.Formatter):
  """
  主要日志格式化器
  """
  
  def format(self, record):
    """
    日志格式化
    设置正确的 module, 给日志登记添加颜色
    """
    path = os.path.splitext(record.pathname)[0]
    path = re.sub(r'/[^/]+?(/\.\.)+', '', path)
    for i in sys.path:
      if not i:
        continue
      path = path.replace(i, '')
    record.module = path.strip('/').replace('/', '.')
    record.levelname = ['\033[35m', '\033[32m', '\033[33m', '\033[31m', '\033[31;47m'][int(record.levelno / 10 - 1)] + record.levelname + '\033[0m'
    return super().format(record)

#: 主要日志格式
main_format = (
  '[%(asctime)s][%(name)s<%(module)s:%(lineno)d>][%(levelname)s]: %(message)s'
)
main_formater = MainFormatter(main_format)
logging.basicConfig(
  format=main_format,
  level=logging.INFO,
)


def default_handler_filter(record):
  """
  默认日志处理器的过滤器
  过滤 debug日志
  """
  if record.levelno == 10:
    return False
  return True


def file_handler_filter(record):
  """
  普通文件日志处理器的过滤器
  过滤 debug 日志
  过滤 mtgbot.plugin.load 的日志
  """
  if record.levelno == 10:
    return False
  if record.name == 'mtgbot.plugin.load' and record.levelno == 20:
    return False
  return True


def debug_handler_filter(record):
  """
  debug文件日志处理器的过滤器

  只显示debug日志
  """
  if record.levelno == 10:
    return True
  return False


class TimedHandler(BaseRotatingHandler):
  """
  按时间分块文件处理器
  """
  def __init__(self, name='', backupCount=30):
    if not name:
      self.base_name = '.log'
    else:
      self.base_name = '.' + name + '.log'

    now = datetime.now(timezone)
    filename = os.path.join(logs_dir, now.strftime('%Y-%m-%d') + self.base_name)
    BaseRotatingHandler.__init__(self, filename, 'a', encoding=io.text_encoding('utf-8'), delay=False, errors=None)
    
    self.backupCount = backupCount
    self.match = re.compile(
      r'^\d{4}-\d{2}-\d{2}' + re.escape(self.base_name) + r'$', re.ASCII
    ).match
    
    if os.path.exists(filename):
      t = int(os.stat(filename).st_mtime)
    else:
      t = int(time.time())
    self.rolloverAt = self.computeRollover(t)

  def computeRollover(self, currentTime):
    t = datetime.fromtimestamp(currentTime + 24 * 3600)
    return int(t.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

  def shouldRollover(self, record):
    t = int(time.time())
    if t < self.rolloverAt:
      return False
    return True
    
  def getFilesToDelete(self):
    result = []
    for i in os.listdir(logs_dir):
      if self.match(i):
        result.append(os.path.join(path, i))

    if len(result) < self.backupCount:
      result = []
    else:
      result.sort()
      result = result[:len(result) - self.backupCount]
    return result

  def doRollover(self):
    currentTime = int(time.time())
    now = datetime.now(timezone)
    filename = os.path.join(logs_dir, now.strftime('%Y-%m-%d') + self.base_name)
    if os.path.exists(filename):
      return

    if self.stream:
      self.stream.close()
      self.stream = None
    self.baseFilename = filename
    if self.backupCount > 0:
      for s in self.getFilesToDelete():
        os.remove(s)
    self.stream = self._open()
    self.rolloverAt = self.computeRollover(currentTime)


#: 默认日志处理器
default_handler = logging.StreamHandler()
default_handler.setFormatter(main_formater)
default_handler.setLevel(logging.INFO)
default_handler.addFilter(default_handler_filter)

#: 文件日志处理器
file_handler: TimedHandler
#: debug 文件日志处理器
debug_handler: TimedHandler
if enable_file_handler:
  file_handler = TimedHandler()
  file_handler.setFormatter(main_formater)
  file_handler.setLevel(logging.INFO)
  file_handler.addFilter(file_handler_filter)

  debug_handler: TimedHandler = TimedHandler('debug')
  debug_handler.setFormatter(main_formater)
  debug_handler.setLevel(logging.DEBUG)
  debug_handler.addFilter(debug_handler_filter)

#: 全局 logger 日志记录器
logger = logging.getLogger('mtgbot')
logger.setLevel(logging.INFO)
root_logger = logging.getLogger('root')
if not root_logger.handlers:
  # 输出日志到命令行/docker logs
  root_logger.handlers = []
  root_logger.addHandler(default_handler)

  # 输出至 logs 文件夹
  if enable_file_handler:
    root_logger.addHandler(file_handler)
    root_logger.addHandler(debug_handler)
