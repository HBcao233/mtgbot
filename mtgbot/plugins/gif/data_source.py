import os
import traceback
from rlottie_python import LottieAnimation

import util
from util.log import logger
from util.progress import FFmpegProgress

  
async def video2gif(img, mid):
  _path, name = os.path.split(img)
  _name, _ext = os.path.splitext(name)
  
  d = os.path.join(_path, _name)
  if not os.path.isdir(d):
    os.mkdir(d)
  pngs = os.path.join(d, '%03d.png')
  output = os.path.join(_path, _name + '.gif')
  
  cv = 'h264'
  if _ext == '.webm':
    cv = 'libvpx-vp9'
  command = [
    'ffmpeg', '-c:v', cv, '-i', img, 
    '-vf', 'scale=480:-1:flags=lanczos,pad=480:ih:(ow-iw)/2:(oh-ih)/2:00000000',
    '-y', pngs
  ]
  bar = FFmpegProgress(mid)
  bar.set_prefix('转换中(1/2)...')
  returncode, stdout = await bar.run(command)
  if returncode != 0: 
    logger.error(stdout)
    return False
  command = [
    'ffmpeg', '-i', pngs, 
    '-lavfi', '[0:v]split[s0][s1];[s0]palettegen=reserve_transparent=on:transparency_color=00000000[p];[s1][p]paletteuse',
    output, '-y'
  ]
  bar.set_prefix('转换中(2/2)...')
  returncode, stdout = await bar.run(command)
  if returncode != 0: 
    logger.error(stdout)
    return False
  
  try:
    for i in os.listdir(d):
      os.remove(os.path.join(d, i))
    os.rmdir(d)
  except:
    logger.warning(traceback.format_exc())
  return output
  
  
async def tgs2ext(img, ext='gif'):
  _path, name = os.path.split(img)
  _name, _ = os.path.splitext(name)
  output = os.path.join(_path, _name + '.' + ext)
  anim = LottieAnimation.from_tgs(img)
  anim.save_animation(output)
  return output
  
  
async def video2ext(img, ext, mid):
  _path, name = os.path.split(img)
  _name, _ = os.path.splitext(name)
  output = os.path.join(_path, _name + '.' + ext)
  
  command = ['ffmpeg', '-i', img, output, '-pix_fmt', 'yuv420p', '-y']
  bar = FFmpegProgress(mid)
  bar.set_prefix('转换中...')
  returncode, stdout = await bar.run(command)
  if returncode != 0:
    logger.warning(stdout.decode())
    return False
  return output
  