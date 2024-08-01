from telethon import types, utils
import os
import cv2
import time 
import numpy as np

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
