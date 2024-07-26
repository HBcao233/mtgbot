import logging
import sys


logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("telethon.network.mtprotosender").setLevel(logging.ERROR)


logging.basicConfig(
    format="[%(asctime)s %(name)s] %(levelname)s: %(message)s", level=logging.INFO
)

logger = logging.getLogger("mtgbot")
# logger.info("tgbot启动")
logger.propagate = False
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(
    logging.Formatter("[%(asctime)s %(name)s] %(levelname)s: %(message)s")
)
if not logger.handlers:
    logger.addHandler(default_handler)

__all__ = [
    "logger",
]
