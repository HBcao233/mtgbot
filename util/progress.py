from telethon import custom
import math 
import traceback
import asyncio
import subprocess
from typing import Union 

import config
from .log import logger


class Progress:
  '''进度条
  
  Arguments
    mid (Message <telethon.tl.custom.message.Message>): 用于进度条显示的 Message
    total (int | float): 总数，将会以 p/total 计算当前进度百分比
    prefix (str): 进度条前显示的字符
    
  Attributes
    bar (list[str]): 一个由全角空格及八分之一至完整方块共9个UTF-8字符组成的列表
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
  '''
  bar = ['\u3000', '\u258f', '\u258e', '\u258d', '\u258c', '\u258b', '\u258a', '\u2589', '\u2588']
  
  def __init__(self, 
    mid: custom.Message, 
    total: Union[int, float] = 100, 
    prefix: str = '', 
  ):
    self.mid = mid
    self.p = 0
    self.total = total
    self.set_prefix(prefix if prefix else mid.message)
    
  def set_prefix(self, prefix=''):
    if not prefix.endswith('\n'):
      prefix += '\n'
    self.prefix = prefix
    
  async def update(self, p=0, total=None):
    if total is None:
      total = self.total
    x = math.floor(104 * p / total)
    text = '[' 
    text += self.bar[8] * (x // 8)
    text += self.bar[x % 8]
    text += self.bar[0] * (13 - x // 8)
    precent = f'{p / total * 100:.2f}'.rstrip("0").rstrip(".")
    text += f'] {precent}%' 
    try:
      await self.mid.edit(self.prefix + text)
      self.p = p
    except:
      logger.warning(traceback.format_exc())
    
  async def add(self, p=1):
    self.p += p
    try:
      await self.update(self.p)
    except:
      logger.warning(traceback.format_exc())
    
    
class FFmpegProgress(Progress):
  async def run(self, command):
    logger.warning('DeprecationWarning: Call to deprecated class util.progress.FFmpegProgress, and please use function util.ffmpeg instead')
    command.extend(['-hide_banner', '-loglevel', 'verbose'])
    input_path = command[command.index('-i') + 1]
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', '-i', input_path]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    full_time = round(float(p.stdout.read().strip()), 2)
    
    def to_seconds(lis, s=0):
      if len(lis) > 0:
        return to_seconds(lis, s * 60 + round(float(lis.pop(0)), 2))
      else:
        return s
        
    proc = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = []
    while line := (await proc.stdout.read(100)).decode():
      stdout.append(line.strip())
      if 'time=' in line:
        for i in line.strip('\n').split():
          if 'time=' in i:
            time = to_seconds(i[5:].split(':'))
            break
        await self.update(int(time / full_time *100))
    return proc.returncode, '\n'.join(stdout)
        