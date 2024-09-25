import httpx
import re
import os
import logging
import time
from typing import Union
from stat import ST_MTIME
import mimetypes

import config
from .string import randStr
from .string import md5sum
from .file import getCache, _getFile


logger = logging.getLogger('mtgbot.curl')
# 文件过期时间
outdated_time = 3600 * 24 * 3

mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/jpeg', '.jpeg')
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/bmp', '.bmp')
mimetypes.add_type('image/x-tga', '.tga')
mimetypes.add_type('image/tiff', '.tiff')
mimetypes.add_type('image/vnd.adobe.photoshop', '.psd')

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('video/avi', '.avi')

mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/m4a', '.m4a')
mimetypes.add_type('audio/aac', '.aac')
mimetypes.add_type('audio/ogg', '.ogg')
mimetypes.add_type('audio/flac', '.flac')

mimetypes.add_type('application/x-tgsticker', '.tgs')


def logless(t):
  if len(t) > 40:
    t = t[:20] + '....' + t[-20:]
  return t


def clean_outdated_file():
  for i in os.listdir(getCache('.')):
    f = getCache(i)
    if os.path.isfile(f) and time.time() - os.stat(f)[ST_MTIME] > outdated_time:
      logger.info(f'清理过期缓存文件 {i}')
      os.remove(f)


def getPath(url=None, ext=None, saveas=None, mime_type=None):
  _path = ''
  if saveas and '/' in saveas:
    _path, saveas = os.path.split(saveas)
  _name = ''
  _ext = ''
  if ext is True:
    if mime_type is not None:
      _ext = mimetypes.guess_extension(mime_type)
    elif url is not None:
      mime_type = mimetypes.guess_type(url)[0]
      _ext = mimetypes.guess_extension(mime_type)
  elif isinstance(ext, str):
    _ext = ext if ext.startswith('.') else '.' + ext

  if saveas:
    arr = os.path.splitext(saveas)
    _name = arr[0]
    if not _ext:
      _ext = '.' + arr[1]

  if not _name:
    _name = md5sum(url)

  if _path and _ext:
    path = _getFile(_path, _name + _ext)
  else:
    path = getCache(_name + _ext)
  return path


class Client(httpx.AsyncClient):
  def __init__(
    self, *, proxy=True, headers=None, follow_redirects=True, timeout=None, **kwargs
  ):
    """
    Args:
      proxy: 是否使用代理
      headers: 指定headers，如 p站图片需要{"Referer": "https://www.pixiv.net"}
      follow_redirects: 是否跟踪重定向, 默认为 True
      timeout: 默认为无限制
    """
    if headers is None:
      headers = {}
    if timeout is None:
      timeout = httpx.Timeout(connect=None, read=None, write=None, pool=None)
    _headers = httpx.Headers(
      {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62',
      }
    )
    _headers.update(headers)
    super().__init__(
      proxies=config.proxies if proxy else None,
      verify=False,
      follow_redirects=follow_redirects,
      headers=_headers,
      timeout=timeout,
      **kwargs,
    )

  """
  def build_request(self,
    method, url, 
    *, 
    headers=None, 
    **kwargs
  ):
    p = urllib.parse.urlparse(url)
    if headers is None:
      headers = {}
    _headers = httpx.Headers({
     'host': p.netloc,
     'origin': p.scheme + '://' + p.netloc,
    })
    _headers.update(headers)
    return super().build_request(
      method, url, headers=_headers,
      **kwargs
    )
  """

  async def getImg(
    self,
    url: str,
    *,
    ext: Union[bool, str] = False,
    saveas: str = None,
    nocache: bool = False,
    rand: bool = False,
    **kwargs,
  ) -> str:
    """
    流式GET 请求下载文件, 返回下载文件路径

    Args:
      url: 文件url
      ext: (优先级大于saveas)
        为True时: 自动从url中获取文件后缀名
        为str时: 指定后缀
      saveas: 指定下载文件名或路径
      nocache: 是否不使用缓存, 默认为 False
      rand: 是否在文件结尾加入随机字符串bytes

    Returns:
      str: 文件路径
    """
    if url is None or url == '':
      return ''

    try:
      async with self.stream('GET', url=url, **kwargs) as r:
        r.raise_for_status()
        path = getPath(url, ext, saveas, r.headers['content-type'])
        if nocache or not os.path.isfile(path):
          with open(path, 'wb') as f:
            async for chunk in r.aiter_raw():
              f.write(chunk)
    except Exception:
      os.remove(path)
      raise

    if rand:
      with open(path, 'ab') as f:
        f.write(randStr().encode())

    clean_outdated_file()
    return path


async def request(
  method, url, *, proxy=False, follow_redirects=True, timeout=None, **kwargs
):
  async with Client(
    proxy=proxy, follow_redirects=follow_redirects, timeout=timeout
  ) as client:
    r = await client.request(method, url, **kwargs)
    log = logger.info
    if r.status_code != 200:
      log = logger.warning
    if url != 'https://telegra.ph/upload':
      log(f'{method} {logless(url)} code: {r.status_code}')
    return r


async def get(url, **kwargs):
  return await request('GET', url, **kwargs)


async def post(url, **kwargs):
  return await request('POST', url, **kwargs)


async def getImg(
  url,
  *,
  ext: Union[bool, str] = False,
  saveas: str = None,
  nocache: bool = True,
  rand: bool = False,
  proxy=False,
  follow_redirects=True,
  timeout=None,
  **kwargs,
) -> str:
  async with Client(
    proxy=proxy, follow_redirects=follow_redirects, timeout=timeout
  ) as client:
    return await client.getImg(
      url, ext=ext, saveas=saveas, nocache=nocache, rand=rand, **kwargs
    )


postimg_pattern = re.compile(r'<input id="code_direct".*?value="(.*?)"')


async def postimg_upload(
  file,
  client=None,
  *,
  proxy=False,
  follow_redirects=True,
  timeout=None,
):
  flag = False
  if client is None:
    flag = True
    client = Client(proxy=proxy, follow_redirects=follow_redirects, timeout=timeout)
  try:
    r = await client.post(
      'https://postimages.org/json/rr',
      files={'file': file},
      data={
        'gallery': '',
        'optsize': 0,
        'expire': 0,
        'numfiles': 1,
        'upload_session': str(time.time()),
      },
      headers={
        'referer': 'https://postimages.org/',
        'origin': 'https://postimages.org',
      },
    )
    r.raise_for_status()
    res = r.json()
    r = await client.get(res['url'])
    match = postimg_pattern.search(r.text)
    return match.group(1)
  finally:
    if flag:
      await client.aclose()
