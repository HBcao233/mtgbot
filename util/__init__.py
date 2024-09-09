from .log import logger
from . import string, file, media, data, curl, telegraph
from .string import (
  randStr,
  md5sum,
)

from .file import (
  getFile,
  getResource,
  getDataFile,
  getCache,
  getWorkFile,
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
  MessageData,
)

from .curl import request, get, post, getImg

__all__ = [
  'logger',
  'string',
  'file',
  'media',
  'data',
  'curl',
  'telegraph',
  'randStr',
  'md5sum',
  'getFile',
  'getResource',
  'getDataFile',
  'getCache',
  'getWorkFile',
  'videoInfo',
  'resizePhoto',
  'img2bytes',
  'getPhotoThumbnail',
  'getData',
  'setData',
  'Data',
  'Photos',
  'Videos',
  'Documents',
  'Animations',
  'MessageData',
  'request',
  'get',
  'post',
  'getImg',
  'bool_or_callable',
]


def bool_or_callable(obj) -> bool:
  if callable(obj):
    return bool(obj())
  return bool(obj)
