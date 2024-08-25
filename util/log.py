import logging
import sys, os, re
import config
from logging.handlers import TimedRotatingFileHandler

__all__ = ["logger"]


logs_dir = os.path.join(config.botRoot, 'logs/')
if not os.path.isdir(logs_dir):
  os.mkdir(logs_dir)

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
file_handler = TimedRotatingFileHandler(filename=os.path.join(logs_dir, 'mtgbot.log'), when="MIDNIGHT", interval=1, backupCount=30)
file_handler.suffix = "%Y-%m-%d.log"
file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
file_handler.setFormatter(
  logging.Formatter("[%(asctime)s %(name)s] %(levelname)s: %(message)s")
)
if not logger.handlers:
  # 输出日志到命令行/docker logs
  logger.addHandler(default_handler)
  # 输出至 logs 文件夹
  logger.addHandler(file_handler)
