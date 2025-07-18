from telethon import types, utils
from typing import Any
import os
import cv2
import numpy as np
import asyncio
import inspect
import mimetypes

import config
from .log import logger


def videoInfo(path: str) -> tuple[Any, int, int, int, bytes]:
  """
  获取视频信息

  Arguments
    path (`str`):
      文件路径

  Returns
    `tuple`

    - `file object`: 文件对象
    - `int`: 视频时长
    - `int`: 视频宽度
    - `int`: 视频高度
    - `bytes`: 视频缩略图
  """
  cap = cv2.VideoCapture(path)
  rate = cap.get(5)
  if rate == 0:
    raise ValueError('Input path not a video file.')
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
  """
  cv2 图片转 bytes
  """
  if '.' not in ext:
    ext = '.' + ext
  return cv2.imencode(ext, img)[1].tobytes()


def getPhotoThumbnail(path, saveas=None) -> cv2.Mat:
  """
  将图片 resize 为最大宽高320的图片
  """
  return resizePhoto(path, 320, saveas=saveas)


def resizePhoto(path, maxSize=2560, size=None, saveas=None) -> cv2.Mat:
  """
  resize cv2图片
  """
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


async def ffmpeg(command: list[str], progress_callback: callable = None):
  """
  运行 ffmpeg 命令

  Arguments
    command (list[str]):
      命令空格分割列表

    progress_callback (callable, optional):
      进度回调函数

  Returns
    returncode (int):
      命令返回值 returncode

    stdout (str):
      命令行输出 (已解码)

  Examples
    .. code-block:: python

      mid = event.reply('请等待...')
      bar = Progress(mid)
      returncode, stdout = await ffmpeg(['ffmpeg', input, 'output.mp4', '-y'], bar.update)
      if returncode != 0:
        logger.warning(stdout)
  """
  if 'ffmpeg' not in command:
    raise ValueError('Not a ffmpeg command')
  command = command.copy()
  command.extend(['-hide_banner', '-loglevel', 'verbose'])
  if progress_callback is None:
    p = await asyncio.create_subprocess_exec(
      *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    returncode = await p.wait()
    return returncode, (await p.stdout.read()).decode()

  input_path = command[command.index('-i') + 1]
  cmd = [
    'ffprobe',
    '-v',
    'error',
    '-show_entries',
    'format=duration',
    '-of',
    'default=noprint_wrappers=1:nokey=1',
    '-i',
    input_path,
  ]
  p = await asyncio.create_subprocess_exec(
    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
  )
  await p.wait()
  full_time = round(float((await p.stdout.read()).decode().strip()), 2)

  def to_seconds(lis, s=0):
    if len(lis) == 0:
      return s
    else:
      t = lis.pop(0)
      if t == '':
        return s
      return to_seconds(lis, s * 60 + round(float(t), 2))

  proc = await asyncio.create_subprocess_exec(
    *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
  )
  stdout = []
  aline_before = ''
  while line := (await proc.stdout.read(100)).decode():
    line = line.strip()
    if '\n' not in line:
      aline = aline_before + line
      aline_before = ''
    else:
      arr = line.split('\n')
      aline = aline_before + arr[0]
      aline_before = arr[1]
    if all(i not in aline for i in ['frame=', 'dropping frame']):
      stdout.append(aline)

    if 'time=' in line:
      for i in line.strip('\n').split():
        if 'time=' in i:
          time = to_seconds(i[5:].split(':'))
          break
      if time != 0:
        func = progress_callback(time, full_time)
        if inspect.isawaitable(func):
          await func
  await proc.wait()
  return proc.returncode, '\n'.join(stdout)


async def video2mp4(path, progress_callback=None):
  """
  视频转 mp4
  """
  _path, _name = os.path.split(path)
  _name, _ = os.path.splitext(path)
  output = os.path.join(_path, _name + '_mp4.mp4')
  command = [
    'ffmpeg',
    '-i',
    path,
    '-c:v',
    'copy',
    '-c:a',
    'copy',
    '-pix_fmt',
    'yuv420p',
    '-y',
    output,
    '-hide_banner',
    '-loglevel',
    'verbose',
  ]
  returncode, stdout = await ffmpeg(command, progress_callback=progress_callback)
  if returncode != 0:
    logger.warning(stdout)
    return path
  return output


def message_media_to_media(message_media, spoiler: bool = False):
  """
  Media 转 MessageMedia, 覆盖 spoiler
  """
  media = utils.get_input_media(message_media)
  media.spoiler = spoiler
  return media


def message_to_media(message: types.Message, spoiler: bool = False):
  """
  Message 转 MessageMedia, 覆盖 spoiler
  """
  return message_media_to_media(message.media, spoiler)


def file_id_to_media(file_id, spoiler: bool = False):
  """
  file_id 转 MessageMedia, 覆盖 spoiler
  """
  media = utils.resolve_bot_file_id(file_id)
  media = utils.get_input_media(media)
  media.spoiler = spoiler
  return media


async def file_to_media(
  path,
  spoiler=False,
  *,
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
  """
  文件路径转 MessageMedia, 覆盖 spoiler

  .. note::
    参数说明详见 `send_file <https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.uploads.UploadMethods.send_file>`_

  Arguments
    path (`str`):
      文件路径

    spoiler (`bool`):
      是否遮罩

    force_document (`bool`):
      图片等强制以文件形式发送

    file_size (`int`):
      文件大小

    progress_callback (`callable`):
      进度回调函数

    attributes (`list`):
      文件属性

    thumb (`str` | `bytes` | `filw`):
      JPEG 缩略图, 最大宽高必须小于 320, 大小最大 20KB

    allow_cache (`bool`):
      允许缓存

    voice_note (`bool`):
      是否作为语音留言发送

    video_note (`bool`):
      是否作为视频留言发送

    supports_streaming (`bool`):
      是否支持流媒体

    mime_type (`str`):
      指定文件 mime_type

    as_image (`bool`):
      强制作为图片

    ttl (`int`):
      文件的生存时间（也称为“自毁定时器”或“自毁媒体”）。如果设置了，文件只能在短时间内查看，然后它们就会自动从消息历史记录中消失。

      范围: 1 ~ 60

      并非所有媒体都可以使用这个参数, 如文本文件, 对它们使用将报错 TtlMediaInvalidError.

    nosound_video (`bool`):
      将无音轨视频发送成 gif还是视频.

      - ``False``: Telegram 中将显示为 gif
      - ``True``: Telegram 中将显示为视频
  """
  _ext = os.path.splitext(path)[-1].lower()
  if _ext in ['.mp4', '.webm', '.avi', '.mov']:
    mime_type = mimetypes.guess_type(f'x{_ext}')[0]
    video, duration, w, h, thumb = videoInfo(path)
    media = types.InputMediaUploadedDocument(
      file=await config.bot.upload_file(
        video,
        progress_callback=progress_callback,
      ),
      mime_type=mime_type,
      attributes=[
        types.DocumentAttributeVideo(
          duration=duration,
          w=int(w),
          h=int(h),
          supports_streaming=supports_streaming,
        ),
        types.DocumentAttributeFilename(os.path.basename(path)),
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
    attributes=attributes,
    thumb=thumb,
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
