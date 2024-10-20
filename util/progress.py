from telethon import custom, errors
import math
import time
from typing import Union

from .log import logger


class Progress:
  """进度条

  Arguments
    mid (Message <telethon.tl.custom.message.Message>): 用于进度条显示的 Message
    total (int | float): 总数，将会以 p/total 计算当前进度百分比
    prefix (str): 进度条前显示的字符

  Attributes
    chars (list[str]): 一个由全角空格及八分之一至完整方块共9个UTF-8字符组成的列表
    p (int): 当前进度

  Example
    mid = event.reply('请等待...')
    bar = Progress(mid)
    for i in range(100)
      bar.update(i+1)
      await asyncio.sleep(1)

    bar.set_prefix('发送中...')
    async with bot.action(event.chat_id, 'video'):
      await bot.send_file(
        event.chat_id,
        media,
        reply_to=event.message,
        progress_callback=bar.update,
      )

    command = ['ffmpeg', ...]
    returncode, stdout = util.ffmpeg(command, bar.update)
  """

  chars = [
    '\u3000',  # 全角空格
    '\u258f',
    '\u258e',
    '\u258d',
    '\u258c',
    '\u258b',
    '\u258a',
    '\u2589',
    '\u2588',
  ]

  def __init__(
    self,
    mid: custom.Message,
    total: Union[int, float] = 100,
    prefix: str = '',
    percent=True,
  ):
    self.mid = mid
    self.p = 0
    self.set_total(total)
    self.set_prefix(prefix if prefix else mid.message)
    self.percent = percent
    self.wait_until = 0

  def set_prefix(self, prefix=''):
    if not prefix.endswith('\n'):
      prefix += '\n'
    self.prefix = prefix

  def set_total(self, total=100):
    self.total = total

  async def update(self, p=0, total=None):
    if total is None:
      total = self.total
    if time.time() - self.wait_until <= 1:
      return

    self.p = p

    x = math.floor(104 * p / total)
    text = '['
    text += self.chars[8] * (x // 8)
    text += self.chars[x % 8]
    text += self.chars[0] * (13 - x // 8)

    if self.percent:
      precent = f'{p / total * 100:.2f}'.rstrip('0').rstrip('.') + '%'
    else:
      precent = f'{p} / {total}'
    text += f'] {precent}'

    try:
      await self.mid.edit(self.prefix + text)
    except (errors.MessageNotModifiedError, errors.MessageIdInvalidError):
      pass
    except errors.FloodWaitError as e:
      logger.warning('遇到 FloodWaitError, 等待 %s 秒', e.seconds)
      self.wait_until = time.time() + e.seconds
    except Exception:
      logger.error('', exc_info=1)
    self.wait_until = time.time()

  async def add(self, p=1, total=None):
    self.p += p
    await self.update(self.p, total)
