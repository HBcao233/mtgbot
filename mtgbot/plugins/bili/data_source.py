import asyncio
import httpx
from functools import cmp_to_key
import base64
import gzip
import struct

import util
from util.log import logger
from .auth import headers, getMixinKey, wbi


qn = 64


def _cmp(x, y):
  if x['id'] > qn:
    return 1
  if y['id'] > qn:
    return -1
  if x['id'] == y['id'] == qn:
    if x['codecid'] == 12:
      return -1
    if y['codecid'] == 12:
      return 1
    return 0
  if x['id'] < y['id']:
    return 1
  if x['id'] > y['id']:
    return -1
  return 0
  

async def get_bili(bvid, aid):
  r = await util.get(
    'https://api.bilibili.com/x/web-interface/view', 
    params={ 'aid': aid, 'bvid': bvid },
    headers=headers,
  )
  res = r.json()
  if res['code'] in [-404, 62002, 62004]:
    return '视频不存在'
  elif res['code'] != 0:
    return '请求失败'
  return res['data']


def parse_msg(res, p=1):
  aid = res['aid']
  bvid = res['bvid']
  cid = res['cid']
  p_url = ''
  p_tip = ''
  if p > 1:
    p_url = '?p=' + str(p)
    p_tip = ' P' + str(p)
    for i in res['pages']:
      if i['page'] == p:
        cid = i['cid']
  title = (
    res['title']
    .replace('&', '&gt;')
    .replace('<', '&lt;')
    .replace('>', '&gt;')
  )
  msg = (
    f"<a href=\"https://www.bilibili.com/video/{bvid}{p_url}\">{title}{p_tip}</a> - "
    f"<a href=\"https://space.bilibili.com/{res['owner']['mid']}\">{res['owner']['name']}</a>"
  )
  return bvid, aid, cid, title, msg
  
  
async def get_video(bvid, aid, cid):
  video_url = None
  audio_url = None
  videos, audios = await _get_video(aid, cid)
  if audios is None:
    video_url = videos
  else:
    videos = sorted(videos, key=cmp_to_key(_cmp))
    logger.info(f"qn: {videos[0]['id']}, codecid: {videos[0]['codecid']}")
    video_url = videos[0]['base_url']
    for i in audios:
      if i['id'] == 30216:
        audio_url = i['base_url']
        break
  
  result = await asyncio.gather(
    util.getImg(
      video_url,
      headers=dict(**headers, Referer=f'https://www.bilibili.com/video/{bvid}'),
    ), 
    util.getImg(
      audio_url,
      headers=dict(**headers, Referer=f'https://www.bilibili.com/video/{bvid}'),
    ),
  ) 
  path = util.getCache(f'{bvid}.mp4')
  command = ['ffmpeg', '-i', result[0]]
  if result[1] != '':
    command.extend(['-i', result[1]])
  command.extend(['-c:v', 'copy', '-c:a', 'copy', '-y', path])
  logger.info(f'{command = }')
  proc = await asyncio.create_subprocess_exec(
    *command,
    stdout=asyncio.subprocess.PIPE, 
    stderr=asyncio.subprocess.PIPE
  )
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.warning(stderr.decode('utf8'))
  
  return path


async def _get_video(aid, cid):
  url = 'https://api.bilibili.com/x/player/wbi/playurl'
  mixin_key = await getMixinKey()
  params = {
    'fnver': 0,
    'fnval': 16,
    'qn': qn,
    'avid': aid,
    'cid': cid,
  }
  headers = {
    'Referer': 'https://www.bilibili.com',
  }
  r = await util.get(
    url,
    params=wbi(mixin_key, params),
    headers=headers,
  )
  # logger.info(r.text)
  res = r.json()['data']
  if 'dash' in res:
    return res['dash']['video'], res['dash']['audio']
  return res['durl'][0]['url'], None
  