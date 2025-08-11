import httpx
import os
import logging
import time
from typing import Union
from stat import ST_MTIME
import mimetypes
import inspect

import config
from .string import randStr
from .string import md5sum
from .file import getCache, _getFile


logger = logging.getLogger('mtgbot.curl')
# 文件过期时间
outdated_time = 3600 * 24 * 3

mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/bmp', '.bmp')
mimetypes.add_type('image/x-tga', '.tga')
mimetypes.add_type('image/tiff', '.tiff')
mimetypes.add_type('image/vnd.adobe.photoshop', '.psd')

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('video/avi', '.avi')

mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/m4a', '.m4a')
mimetypes.add_type('audio/aac', '.aac')
mimetypes.add_type('audio/ogg', '.ogg')
mimetypes.add_type('audio/flac', '.flac')

mimetypes.add_type('application/x-tgsticker', '.tgs')


def logless(t):
  """
  将字符串缩减至长度 40 以下
  """
  t = str(t)
  if len(t) > 40:
    t = t[:20] + '....' + t[-20:]
  return t


def clean_outdated_file():
  """
  清理过期缓存文件
  """
  for i in os.listdir(getCache('.')):
    f = getCache(i)
    if os.path.isfile(f) and time.time() - os.stat(f)[ST_MTIME] > outdated_time:
      logger.info(f'清理过期缓存文件 {i}')
      os.remove(f)


def getPath(url=None, ext=None, saveas=None, mime_type=None):
  """
  根据 url, ext, saveas, mime_type 获取保存路径
  """
  _path = ''
  if saveas and '/' in saveas:
    _path, saveas = os.path.split(saveas)
  _name = ''
  _ext = ''
  if ext is True or ext == 'auto':
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
  """
  httpx 异步客户端

  .. important::
    follow_redirects 默认值被设置为了 ``True``, 而 `httpx.AsyncClient` 默认值为 ``False``

  Arguments
    headers (`dict` | `httpx.Headers`):
      指定headers，如 p站图片需要{"Referer": "https://www.pixiv.net"}

    follow_redirects (`bool`):
      是否跟踪重定向, 默认为 True

    timeout (`int` | `httpx.Timeout`):
      默认为无限制

    kwargs:
      其他参数
  """

  def __init__(
    self, *, proxy=None, headers=None, follow_redirects=True, timeout=None, **kwargs
  ):
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
      proxy=proxy,
      verify=False,
      http2=True,
      follow_redirects=follow_redirects,
      headers=_headers,
      timeout=timeout,
      **kwargs,
    )

  '''
  def build_request(self,
    method, url, 
    *, 
    headers=None, 
    **kwargs
  ):
    """
    添加反向代理
    """
    if headers is None:
      headers = {}
    _headers = httpx.Headers(headers)
    
    url = httpx.URL(url)
    arr = ['i.pximg.net']
    if url.host in arr:
      _headers['upstream-host'] = url.host
      url = url.copy_with(host='fuck-cors.hbcaoqaq-1cd.workers.dev')
      if (v := headers.get('referer', None)):
        _headers.update({
          'real-referer': v,
        })
      if (v := headers.get('origin', None)):
        _headers.update({
          'real-origin': v,
        })
      
    return super().build_request(
      method, url, headers=_headers,
      **kwargs
    )
  '''

  async def getImg(
    self,
    url: str,
    *,
    ext: Union[bool, str] = False,
    saveas: str = None,
    nocache: bool = False,
    rand: bool = False,
    progress_callback: callable = None,
    **kwargs,
  ) -> str:
    """
    流式 GET 请求下载文件, 返回下载文件路径

    Arguments
      url (`str`):
        文件url

      ext (`bool` | `str`):
        (优先级大于saveas)
        为True/ 'auto' 时: 自动从url中获取文件后缀名
        为str时: 指定后缀

      saveas (`str`):
        指定下载文件名或路径

      nocache (`bool`):
        是否不使用缓存, 默认为 ``False``

      rand (`bool`):
        是否在文件结尾加入随机字符串bytes

    Returns
      str: 文件路径
    """
    if url is None or url == '':
      return ''

    path = None
    total = None
    try:
      async with self.stream('GET', url=url, **kwargs) as r:
        r.raise_for_status()
        if progress_callback:
          total = int(r.headers['Content-Length'])

        path = getPath(url, ext, saveas, r.headers['content-type'])
        if nocache or not os.path.isfile(path):
          with open(path, 'wb') as f:
            async for chunk in r.aiter_raw():
              f.write(chunk)
              if progress_callback:
                try:
                  func = progress_callback(r.num_bytes_downloaded, total)
                  if inspect.isawaitable(func):
                    await func
                except Exception:
                  logger.warning('更新进度条错误', exc_info=1)
    except Exception:
      if path and os.path.isfile(path):
        os.remove(path)
      raise

    if rand:
      with open(path, 'ab') as f:
        f.write(randStr().encode())

    clean_outdated_file()
    return path


async def request(
  method, url, *, proxy=None, follow_redirects=True, timeout=None, **kwargs
):
  """
  异步 client.request() 的简略写法
  """
  async with Client(
    proxy=proxy,
    follow_redirects=follow_redirects, 
    timeout=timeout,
  ) as client:
    r = await client.request(method, url, **kwargs)
    log = logger.info
    if r.status_code != 200:
      log = logger.warning
    if url != 'https://telegra.ph/upload':
      log(f'{method} {logless(url)} code: {r.status_code}')
    return r


async def get(url, **kwargs):
  """
  异步 client.get() 的简略写法
  """
  return await request('GET', url, **kwargs)


async def post(url, **kwargs):
  """
  异步 client.post() 的简略写法
  """
  return await request('POST', url, **kwargs)


async def getImg(
  url,
  *,
  ext: Union[bool, str] = False,
  saveas: str = None,
  nocache: bool = True,
  rand: bool = False,
  proxy=None,
  follow_redirects=True,
  timeout=None,
  **kwargs,
) -> str:
  """
  异步 client.getImg() 的简略写法
  """
  async with Client(
    proxy=proxy, follow_redirects=follow_redirects, timeout=timeout
  ) as client:
    logger.info(f'GET {logless(url)}')
    return await client.getImg(
      url, ext=ext, saveas=saveas, nocache=nocache, rand=rand, **kwargs
    )
