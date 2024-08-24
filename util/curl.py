import urllib.parse
import httpx
import re, os, logging
from typing import Union

import config
from .string import randStr
from .string import md5sum
from .file import getCache


logger = logging.getLogger('mtgbot.curl')


def logless(t):
  if len(t) > 40:
    t = t[:20] + '{...}' + t[-20:]
  return t


class Client(httpx.AsyncClient):
  def __init__(self, 
    *, 
    proxy=True, 
    headers=None,
    follow_redirects=True, 
    timeout=None,
    **kwargs
  ):
    if headers is None:
      headers = {}
    if timeout is None:
      timeout = httpx.Timeout(connect=None, read=None, write=None, pool=None)
    super().__init__(
      proxies=config.proxies if proxy else None, 
      verify=False, 
      follow_redirects=follow_redirects,
      headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
        **headers,
      },
      timeout=timeout,
      **kwargs
    )
    
  def build_request(self,
    method, url, *, 
    headers=None, 
    **kwargs
  ):
    p = urllib.parse.urlparse(url)
    if headers is None:
      headers = {}
    return super().build_request(
      method, url, headers={
       'Referer': p.scheme + '://' + p.netloc + '/',
       'host': p.netloc,
       **headers,
      },
      **kwargs
    )

  
async def request(
  method, url, *, 
  proxy=False, 
  follow_redirects=True, 
  timeout=None,
  **kwargs
):
  async with Client(proxy=proxy, follow_redirects=follow_redirects, timeout=timeout) as client:
    r = await client.request(method, url, **kwargs)
    log = logger.info
    if r.status_code != 200:
      log = logger.warning
    if url != 'https://telegra.ph/upload':
      log(f"{method} {logless(url)} code: {r.status_code}")
    return r

async def get(url, **kwargs):
  return await request("GET", url, **kwargs)


async def post(url, **kwargs):
  return await request(
    "POST", url, **kwargs
  )
  

async def getImg(
  url, *, cache=True, path=None, headers=None, rand=False, ext: Union[bool, str]=False, saveas=None, proxy=True, follow_redirects=True, timeout=None,  **kwargs
) -> str:
  """
  获取下载广义上的图片，可以为任意文件

  Args:
      url: 图片url，或图片bytes
      proxy: 是否使用代理
      path: 保存路径 
      headers: 指定headers，如 p站图片需要{"Referer": "https://www.pixiv.net"}
      rand: 是否在文件结尾加入随机字符串bytes
      ext: 自动从url中获取文件后缀名
      saveas: 重命名

  Returns:
      str: 图片路径
  """
  if url is None or url == '': 
    return ''
  b = isinstance(url, bytes)
  
  if not b and url.find("file://") >= 0:
    if path is None:
      path = url[7:]
    if rand:
      with open(path, "ab") as f:
        f.write(randStr().encode())
    return path

  if b:
    if path is None:
      md5 = md5sum(byte=url)
      path = getCache(md5)
    with open(path, "wb") as f:
        f.write(url)

    if rand:
      with open(path, "ab") as f:
        f.write(randStr().encode())

    logger.info(f"bytes转图片成功: {path}")
    return path
  
  f = ''
  ex = ''
  if ext is True and '.' in url:
    ex = url.split(".")[-1]
    ex = re.sub(r"(\?.*)?(#.*)?(:.*)?", "", ex)
    ex = '.' + ex
  elif type(ext) == str:
    ex = ext if ext.startswith('.') else '.' +  ext
  
  if not saveas:
    f = md5sum(url)
  else:
    arr = os.path.splitext(saveas)
    f = arr[0]
    if not ex:
      ex = '.' + arr[1]
    
  if path is None:
    path = getCache(f + ex)
  
  if not os.path.isfile(path) or not cache:
    logger.info(f"尝试获取图片 {logless(url)}, saveas {os.path.basename(path)}")
    try:
      async with Client(
        proxy=proxy,
        http2=True,
        follow_redirects=follow_redirects,
        timeout=timeout,
      ) as client:
        async with client.stream(
          'GET', url=url, headers=headers,
          **kwargs
        ) as r:
          with open(path, "wb") as f:
            async for chunk in r.aiter_raw():
              f.write(chunk)
    except:
      os.remove(path)
      raise

    if rand:
      with open(path, "ab") as f:
        f.write(randStr().encode())

  logger.info(f"获取图片成功: {path}")
  return path
