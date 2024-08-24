import logging
import sys
import config

__all__ = ["logger"]

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
if not logger.handlers:
  logger.addHandler(default_handler)
