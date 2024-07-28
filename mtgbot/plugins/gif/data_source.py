import asyncio
import subprocess
import os.path

import util
from util.log import logger
from util.progress import FFmpegProgress


pipe_kwargs = dict(
  stdout=asyncio.subprocess.PIPE,
  stderr=asyncio.subprocess.PIPE
)
  
  
async def video2gif(img):
  _path, name = os.path.split(img)
  _name, _ = os.path.splitext(name)
  palette = os.path.join(_path, _name + '_palette.png')
  output = os.path.join(_path, _name + '.gif')
  
  command = [
    'ffmpeg', 
    '-i', img, 
    '-vf', 'palettegen', 
    palette, '-y'
  ]
  proc = await asyncio.create_subprocess_exec(*command, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False

  command = [
    'ffmpeg', 
    '-i', img,
    '-i', palette,
    '-filter_complex', 'paletteuse',
    output, '-y'
  ]
  proc = await asyncio.create_subprocess_exec(*command, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  return output
  
  
async def tgs2gif(lottiepath, img):
  _path, name = os.path.split(img)
  _name, _ = os.path.splitext(name)
  json_output = os.path.join(_path, _name + '.json')
  output = os.path.join(_path, _name + '.gif')
  
  proc = subprocess.Popen(['gzip', '-d', '-c'], stdin=open(img, 'rb'), stdout=open(json_output, 'wb'), stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  
  proc = await asyncio.create_subprocess_exec(lottiepath, json_output, '512x512', '00ffffff', **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  os.rename(json_output + '.gif', output)
  return output


def getLottiePath():
  ret = subprocess.Popen(['lottie2gif'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  if ret.returncode == 256:
    return 'lottie2gif'
  path = util.getWorkFile('lottie2gif')
  if os.path.isfile(path):
    return path
  return None
  
  
async def video2ext(img, ext, mid):
  _path, name = os.path.split(img)
  _name, _ = os.path.splitext(name)
  output = os.path.join(_path, _name + '.' + ext)
  
  command = ['ffmpeg', '-i', img, output, '-pix_fmt', 'yuv420p', '-y']
  bar = FFmpegProgress(mid)
  returncode, stdout = await bar.run(command)
  if returncode != 0:
    logger.warning(stdout.decode())
    return False
  return output
  