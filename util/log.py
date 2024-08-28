import logging
import sys, os, re, time
import config
from logging.handlers import TimedRotatingFileHandler

__all__ = ["logger"]

logs_dir = os.path.join(config.botRoot, 'logs/')
if not os.path.isdir(logs_dir):
  os.mkdir(logs_dir)


class TimedHandler(TimedRotatingFileHandler):
  def __init__(self, 
    backupCount=30,
    encoding=None, delay=False,
    errors=None
  ):
    suffix = "%Y-%m-%d.log"
    t = int(time.time())
    timeTuple = time.localtime(t)
    filename = time.strftime(suffix, timeTuple)
    filename = os.path.join(logs_dir, filename)
    super().__init__(filename, 'MIDNIGHT', 1, backupCount, encoding=encoding, delay=delay, utc=False, atTime=None, errors=errors)
    self.suffix = suffix
    self.extMatch = re.compile(r"(?<=\.)\d{4}-\d{2}-\d{2}\.log$", re.ASCII)
  
  def namer(self, name):
    _path, _name = os.path.split(name)
    if name.count('.') <= 1:
      return name
    _name = _name[_name.index('.log.')+5:]
    return os.path.join(_path, _name)


logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("telethon.client.updates").setLevel(logging.ERROR)
logging.getLogger("telethon.network.mtprotosender").setLevel(logging.ERROR)
logging.getLogger("telethon.extensions.messagepacker").setLevel(logging.ERROR)


logging.basicConfig(
  format="[%(asctime)s %(name)s] %(levelname)s: %(message)s", 
  level=logging.INFO if not config.debug else logging.DEBUG
)

logger = logging.getLogger("mtgbot")
logger.propagate = False
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(
  logging.Formatter("[%(asctime)s %(name)s] %(levelname)s: %(message)s")
)
file_handler = TimedHandler()
file_handler.setFormatter(
  logging.Formatter("[%(asctime)s %(name)s] %(levelname)s: %(message)s")
)
if not logger.handlers:
  # 输出日志到命令行/docker logs
  logger.addHandler(default_handler)
  # 输出至 logs 文件夹
  logger.addHandler(file_handler)
