import math 
import traceback
import asyncio

from util.log import logger


class Progress:
  bar = ['\u3000', '\u258f', '\u258e', '\u258d', '\u258c', '\u258b', '\u258a', '\u2589', '\u2588']
  
  def __init__(self, bot, mid, total=100, prefix=''):
    self.bot = bot
    self.mid = mid
    self.p = 0
    self.total = total
    self.task = None
    self.loop = asyncio.get_event_loop()
    self.set_prefix(prefix)
    
  def set_prefix(self, prefix=''):
    if not prefix.endswith('\n'):
      prefix += '\n'
    self.prefix = prefix
    
  def update(self, p=0):
    if self.task is not None:
      self.task.cancel()
      self.task = None
    x = math.floor(104 * p / self.total)
    text = '[' 
    text += self.bar[8] * (x // 8)
    text += self.bar[x % 8]
    text += self.bar[0] * ((104 - x) // 8)
    precent = f'{p / self.total * 100:.2f}'.rstrip("0").rstrip(".")
    text += f'] {precent}%' 
    try:
      self.task = self.loop.create_task(self.bot.edit_message_text(
        chat_id=self.mid.chat.id,
        message_id=self.mid.message_id,
        text=self.prefix + text,
      ))
      self.p = p
    except:
      logger.warning(traceback.format_exc())
    
  def add(self, p=1):
    self.p += p
    try:
      self.update(self.p)
    except:
      logger.warning(traceback.format_exc())
    