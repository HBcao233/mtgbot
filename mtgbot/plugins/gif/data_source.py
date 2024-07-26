import asyncio
import subprocess
import os.path

import util
from util.log import logger


pipe_kwargs = dict(
  stdout=asyncio.subprocess.PIPE,
  stderr=asyncio.subprocess.PIPE
)


async def video2gif(document_id, event, mid):
  palette = util.getCache(str(document_id) + '_palette.png')
  command = [
    'ffmpeg', 
    '-i', util.getCache(document_id), 
    '-vf', 'palettegen', 
    palette, '-y'
  ]
  proc = await asyncio.create_subprocess_exec(*command, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False

  output = util.getCache(str(document_id) + '.gif')
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
  
  
async def tgs2gif(lottiepath, document_id):
  img = util.getCache(document_id)
  json_output = util.getCache(str(document_id) + '.json')
  output = util.getCache(str(document_id) + '.gif') 
  logger.info('%s, %s, %s', img, json_output, output)
  
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
  