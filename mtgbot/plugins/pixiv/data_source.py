import re
import asyncio
import os.path
from datetime import datetime
import config

import util
from util.log import logger


PHPSESSID = config.env.get('pixiv_PHPSESSID', '')
headers = {
  'cookie': f'PHPSESSID={PHPSESSID};'
}


async def get_pixiv(pid):
  try:
    url = f"https://www.pixiv.net/ajax/illust/{pid}"
    r = await util.get(url, headers=dict(**headers, referer=f'https://www.pixiv.net/artworks/{pid}'))
  except Exception:
    return '连接超时'
  res = r.json()
  if 'error' in res and res["error"]:
    logger.error(r.text)
    return '错误: ' + res["message"]
  return res['body']


def parse_msg(res, hide=False):
  pid = res["illustId"]
  
  '''tags = []
  for i in res["tags"]["tags"]:
      tags.append("#" + i["tag"])
      if "translation" in i.keys():
          tags.append("#" + i["translation"]["en"])
  tags = (
      json.dumps(tags, ensure_ascii=False)
      .replace('"', "")
      .replace("[", "")
      .replace("]", "")
  )'''

  props = []
  if res["tags"]["tags"][0]["tag"] == "R-18":
      props.append('#NSFW')
  if res["tags"]["tags"][0]["tag"] == "R-18G":
      props.append('#R18G')
      props.append('#NSFW')
  if res['illustType'] == 2:
    props.append('#动图')
  if res['aiType'] == 2:
      props.append('#AI生成')
  prop = ' '.join(props)
  if prop != '':
      prop += '\n'
  
  #t = dateutil.parser.parse(res["createDate"]) + datetime.timedelta(hours=8)
  msg = prop + f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">{res['illustTitle']}</a> - <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>"
  if not hide:
    comment = res["illustComment"]
    comment = (
      comment
      .replace("<br />", "\n")
      .replace("<br/>", "\n")
      .replace("<br>", "\n")
      .replace(' target="_blank"', "")
    )
    comment = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', comment)
    if len(comment) > 400:
      comment = re.sub(r'<[^/]+[^<]*(<[^>]*)?$', '', comment[:400])
      comment = re.sub(r'\n$','',comment)
      comment = comment + '\n......'
    if comment != '':
      comment = ':\n' + comment
      msg += comment
  
  return msg


async def get_anime(pid):
  name = f'{pid}_ugoira'
  url = f"https://www.pixiv.net/ajax/illust/{pid}/ugoira_meta"
  r = await util.get(url, headers=headers)
  res = r.json()['body']
  frames = res['frames']
  if not os.path.isdir(util.getCache(name+"/")):
    zi = await util.getImg(
      res['src'], 
      saveas=name, 
      ext='zip',
      headers=headers,
    )
    proc = await asyncio.create_subprocess_exec(
      'unzip', '-o', '-d', util.getCache(name+"/"), zi, 
      stdout=asyncio.subprocess.PIPE, 
      stdin=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
    )
    await proc.wait()
  
  f = frames[0]['file']
  f, ext = os.path.splitext(f)
  rate = str(round(1000 / frames[0]['delay'], 2))
  img = util.getCache(f'{pid}.mp4')
  command = [
    'ffmpeg', '-framerate', rate, '-loop', '0', '-f', 'image2',
    '-i', util.getCache(name + f'/%{len(f)}d{ext}'), 
    '-r', rate, '-c:v', 'h264', '-pix_fmt', 'yuv420p', '-vf', "pad=ceil(iw/2)*2:ceil(ih/2)*2", '-y', img
  ]
  # logger.info(f'command: {command}')
  proc = await asyncio.create_subprocess_exec(
    *command,
    stdout=asyncio.subprocess.PIPE, 
    stdin=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
  )
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.warning(stderr.decode('utf8'))
    return False
  
  logger.info(f'生成动图成功: {img}')
  return img
  
  
async def get_telegraph(res):
  data = util.Data('urls')
  now = datetime.now()
  pid = res['illustId']
  key = f'{pid}-{now:%m-%d}'
  if not (url := data[key]):
    imgUrl = res["urls"]["original"].replace('i.pximg.net', 'i.pixiv.re')
    content = []
    for i in range(res['pageCount']):
      content.append({
        'tag': 'img',
        'attrs': {
          'src': imgUrl.replace("_p0", f"_p{i}"),
        },
      })
   
    url = await util.telegraph.createPage(f"[pixiv] {pid} {res['illustTitle']}", content)
    with data:
      data[key] = url
    
  msg = (
    f"标题: {res['illustTitle']}\n"
    f"预览: {url}\n"
    f"作者: <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>\n"
    f"数量: {res['pageCount']}\n"
    f"原链接: https://www.pixiv.net/artworks/{pid}"
  )
  return url, msg
  