from telethon import types, utils
import os
import cv2
import time 
import numpy as np
import asyncio

import config
from .log import logger
from .file import getCache


def videoInfo(path):
  cap = cv2.VideoCapture(path)
  rate = cap.get(5)
  frame_count = cap.get(7)
  duration = round(frame_count / rate, 2)
  width = cap.get(3)
  height = cap.get(4)
  cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
  ret, img = cap.read()
  cap.release()
  img = getPhotoThumbnail(img)
  thumbnail = img2bytes(img, 'jpg')
  return open(path, 'rb'), duration, width, height, thumbnail


def img2bytes(img, ext):
  if '.' not in ext:
    ext = '.' + ext
  return cv2.imencode(ext, img)[1].tobytes()
  
  
def getPhotoThumbnail(path, saveas=None) -> cv2.Mat:
  return resizePhoto(path, 320, saveas=saveas)
  
  
def resizePhoto(path, maxSize=2560, size=None, saveas=None) -> cv2.Mat:
  if isinstance(path, str):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
  else:
    img = path
  h, w, channels = img.shape
  if size is None:
    if w > maxSize or h > maxSize:
      if w >= h:
        size = (maxSize, int(maxSize * h / w))
      elif h > w:
        size = (int(maxSize * w / h), maxSize)
  if size is not None: 
    img = cv2.resize(img, size)
  if channels == 4:
    white = np.zeros(img.shape, dtype='uint8') 
    img = cv2.add(img, white)
  if saveas is not None:
    cv2.imwrite(saveas, img)
  return img


async def ffmpeg(
  command: list[str], 
  progress_callback: callable = None
):
  '''Run a ffmpeg command
  
  Arguments
    command (list[str]): a command 
    progress_callback (callable, optional): a update function for progress
    
  Returns
    returncode (int): command returncode
    stdout (str): command stdout (decoded)
    
  Examples
    bar = 
    returncode, stdout = await ffmpeg(['ffmpeg', input, 'output.mp4', '-y'], bar.update)
    if returncode != 0:
      logger.warning(stdout)
  '''
  if 'ffmpeg' not in command:
    raise ValueError('Not a ffmpeg command')
  command = command.copy()
  command.extend(['-hide_banner', '-loglevel', 'verbose'])
  if progress_callback is None:
    p = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    returncode = await p.wait()
    return returncode, (await p.stdout.read()).decode()
    
  input_path = command[command.index('-i') + 1]
  cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', '-i', input_path]
  p = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  await p.wait()
  full_time = round(float((await p.stdout.read()).decode().strip()), 2)
  
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
      t = progress_callback(time, full_time)
      if inspect.isawaitable(t):
        await t
  return proc.returncode, '\n'.join(stdout)
  

async def video2mp4(path, progress_callback=None):
  _path, _name = os.path.split(path)
  _name, _ = os.path.splitext(path)
  output = os.path.join(_path, _name + '_mp4.mp4')
  command = [
    'ffmpeg', '-i', path, 
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-pix_fmt', 'yuv420p', 
    '-y', output,
    '-hide_banner', '-loglevel', 'verbose'
  ]
  returncode, stdout = await ffmpeg(command, progress_callback=progress_callback)
  if returncode != 0:
    logger.warning(stdout)
    return path
  return output
  
  
def message_media_to_media(message_media, spoiler: bool = False):
  media = utils.get_input_media(message_media)
  media.spoiler = spoiler
  return media
  
def message_to_media(message: types.Message, spoiler: bool = False):
  return message_media_to_media(message.media, spoiler)
  
def file_id_to_media(file_id, spoiler: bool = False):
  media = utils.resolve_bot_file_id(file_id)
  media = utils.get_input_media(media)
  media.spoiler = spoiler
  return media

async def file_to_media(
  path, spoiler=False, *,
  force_document=False, 
  file_size=None,
  progress_callback=None,
  attributes=None, 
  thumb=None,
  allow_cache=True, 
  voice_note=False, 
  video_note=False,
  supports_streaming=True, 
  mime_type=None, 
  as_image=None,
  ttl=None, 
  nosound_video=True,
):
  if os.path.splitext(path)[-1] == '.mp4':
    video, duration, w, h, thumb = videoInfo(path)
    media = types.InputMediaUploadedDocument(
      file=await config.bot.upload_file(video),
      mime_type='video/mp4',
      attributes=[
        types.DocumentAttributeVideo(
          duration=duration,
          w=int(w), h=int(h),
          supports_streaming=supports_streaming,
        ),
        types.DocumentAttributeFilename(os.path.split(path)[-1])
      ],
      nosound_video=nosound_video,
      spoiler=spoiler,
      thumb=await config.bot.upload_file(thumb),
      force_file=force_document,
      ttl_seconds=ttl,
    )
    return media
    
  input_file, media, as_image = await config.bot._file_to_media(
    path, 
    force_document=force_document, 
    file_size=file_size,
    progress_callback=progress_callback,
    attributes=attributes, thumb=thumb,
    allow_cache=allow_cache, 
    voice_note=voice_note, 
    video_note=video_note,
    supports_streaming=supports_streaming, 
    mime_type=mime_type, 
    as_image=as_image,
    ttl=ttl, 
    nosound_video=nosound_video,
  )
  media.spoiler = spoiler
  return media
