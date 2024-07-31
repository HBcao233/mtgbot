import urllib.parse
import hashlib
from functools import reduce
import time
import httpx

import util
import config

SESSDATA = config.env.get('bili_SESSDATA', '')
headers = {
  'cookie': f'SESSDATA={SESSDATA}'
}

async def getMixinKey():
  mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
  ]
  
  r = await util.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
  res = r.json()['data']['wbi_img']
  img_key = res['img_url'].rsplit('/', 1)[1].split('.')[0]
  sub_key = res['sub_url'].rsplit('/', 1)[1].split('.')[0]
  orig = img_key + sub_key
  return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]
 
    
def wbi(mixin_key, params=None):
  if params is None: params = dict()
  params['wts'] = round(time.time())
  params = dict(sorted(params.items()))  # 按照 key 重排参数
  # 过滤 value 中的 "!'()*" 字符
  params = {
      k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
      for k, v in params.items()
  }
  query = urllib.parse.urlencode(params)  # 序列化参数
  params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
  return params
  