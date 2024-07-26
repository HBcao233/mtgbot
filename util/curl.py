import urllib.parse
import httpx
import os.path
from typing import Union
import re

import config
from .log import logger
from .string import randStr
from .string import md5sum
from .file import getCache


async def request(
    method, url, *, params=None, data=None, proxy=False, headers=None, **kwargs
):
  p = urllib.parse.urlparse(url)
  _headers = {
     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
     'Referer': p.scheme + '://' + p.netloc + '/',
     'host': p.netloc,
  }
  headers = dict(_headers, **headers) if headers else None
  client = httpx.AsyncClient(
      proxies=config.proxies if proxy else None, 
      verify=False
  )
  # logger.info(headers)
  
  r = await client.request(
    method, url=url, headers=headers, data=data, params=params, 
    timeout=httpx.Timeout(connect=None, read=None, write=None, pool=None),
    **kwargs
  )
  
  if params is None: params = dict()
  if type(params) == dict: params = urllib.parse.urlencode(params)
  params = params.strip()
  if params != '':
    if '?' in url:
      url += '&' + params
    else:
      url += '?' + params
  if r.status_code == 302:
    url = r.headers['Location']
    if 'http' not in url: url = p.scheme + '://' + p.netloc + '/' + url
    r = await client.request(
      method, url=url, headers=headers, data=data, 
      timeout=httpx.Timeout(connect=None, read=None, write=None, pool=None),
      **kwargs
    )
  t = logger.info
  if r.status_code != 200:
    t = logger.warning
  if url != 'https://telegra.ph/upload':
    t(f"{method} {url} code: {r.status_code}")
  await client.aclose()
  return r


async def get(url, *, proxy=False, headers=None, params=None, data=None, **kwargs):
  return await request(
      "GET", url, params=params, data=data, proxy=proxy, headers=headers, **kwargs
  )


async def post(url, *, proxy=False, headers=None, params=None, data=None, **kwargs):
  return await request(
      "POST", url, params=params, data=data, proxy=proxy, headers=headers, **kwargs
  )
  

async def getImg(
    url, *, proxy=True, cache=True, path=None, headers=None, rand=False, ext: Union[bool, str]=False, saveas=None, **kwargs
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
    else:
      f = ''
      ex = ''
      if ext is True and '.' in url:
        ex = url.split(".")[-1]
        ex = re.sub(r"(\?.*)?(#.*)?(:.*)?", "", ex)
        ex = '.' + ex
      elif type(ext) == str:
        ex = '.' + ext if not ext.startswith('.') else ext
      
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
        logger.info(f"尝试获取图片 {url}, proxy: {proxy}, headers: {headers} , saveas {os.path.basename(path)}")
        p = urllib.parse.urlparse(url)
        _headers = {
          "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
          'Referer': p.scheme + '://' + p.netloc + '/',
          'host': p.netloc,
        }
        headers = dict(_headers, **headers) if headers else None
        try:
          async with httpx.AsyncClient(
            proxies=config.proxies if proxy else None, 
            verify=False,
            timeout=httpx.Timeout(connect=None, read=None, write=None, pool=None),
            http2=True,
          ) as client:
            async with client.stream(
              'GET', url=url, headers=headers,
            ) as r:
              with open(path, "wb") as f:
                async for chunk in r.aiter_raw():
                  f.write(chunk)
        except:
          os.remove(path)
          return False

        if rand:
          with open(path, "ab") as f:
              f.write(randStr().encode())

      logger.info(f"获取图片成功: {path}")
      return path
        