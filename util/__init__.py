# 从子模块中导入部分常用命令，方便调用
from . import string, file, media, data, curl, telegraph

from .base import get_blacklist
from .log import logger, tz, timezone
from .string import (
  randStr,
  md5sum,
)

from .file import (
  getFile,
  getResourceFile,
  getResource,
  getDataFile,
  getCacheFile,
  getCache,
)

from .media import (
  videoInfo,
  resizePhoto,
  img2bytes,
  getPhotoThumbnail,
)

from .data import (
  getData,
  setData,
  Data,
  Photos,
  Videos,
  Documents,
  Animations,
  Audios,
  MessageData,
)

from .curl import (
  request,
  get,
  post,
  getImg,
  Client,
)

__all__ = [
  # base 
  'get_blacklist',
  # log
  'logger',
  'tz',
  'timezone',
  #
  'string',
  'file',
  'media',
  'data',
  'curl',
  'telegraph',
  'randStr',
  'md5sum',
  # file
  'getFile',
  'getResourceFile',
  'getResource',
  'getDataFile',
  'getCacheFile',
  'getCache',
  # media
  'videoInfo',
  'resizePhoto',
  'img2bytes',
  'getPhotoThumbnail',
  # data
  'getData',
  'setData',
  'Data',
  'Photos',
  'Videos',
  'Documents',
  'Animations',
  'Audios',
  'MessageData',
  # curl
  'request',
  'get',
  'post',
  'getImg',
  'Client',
  'bool_or_callable',
]


def bool_or_callable(obj) -> bool:
  """
  计算 obj 的布尔值, 如果 obj 为 callable, 则调用后再求布尔值
  """
  if callable(obj):
    return bool(obj())
  return bool(obj)
