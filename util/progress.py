import math 
import traceback
import asyncio
import subprocess

import config
from util.log import logger


class Progress:
  bar = ['\u3000', '\u258f', '\u258e', '\u258d', '\u258c', '\u258b', '\u258a', '\u2589', '\u2588']
  
  def __init__(self, mid, total=100, prefix=''):
    self.mid = mid
    self.p = 0
    self.total = total
    self.loop = config.bot.loop
    asyncio.set_event_loop(self.loop)
    self.task = None
    self.set_prefix(prefix if prefix else mid.message)
    
  def set_prefix(self, prefix=''):
    if not prefix.endswith('\n'):
      prefix += '\n'
    self.prefix = prefix
    
  async def update(self, p=0):
    if self.task is not None:
      self.task.cancel()
      self.task = None
    x = math.floor(104 * p / self.total)
    text = '[' 
    text += self.bar[8] * (x // 8)
    text += self.bar[x % 8]
    text += self.bar[0] * (13 - x // 8)
    precent = f'{p / self.total * 100:.2f}'.rstrip("0").rstrip(".")
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
    while line := (await proc.stdout.read(100)).decode():
      if 'time=' in line:
        for i in line.strip('\n').split():
          if 'time=' in i:
            time = to_seconds(i[5:].split(':'))
            break
        await self.update(int(time / full_time *100))
    
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout
        