import re
import asyncio
import util
import config
import os.path
from util import logger

PHPSESSID = config.env.get('pixiv_PHPSESSID', '')
headers = {
  'cookie': f'PHPSESSID={PHPSESSID};'
}

def parsePidMsg(res, hide=False):
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
  msg = prop
  msg += f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">{res['illustTitle']}</a> - <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>"
  if not hide:
    comment = res["illustComment"]
    comment = (
        comment.replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
        .replace(' target="_blank"', "")
    )
    comment = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', comment)
    if len(comment) > 400:
        comment = re.sub(r'<[^/]+[^<]*(<[^>]*)?$', '', comment[:200])
        comment = re.sub(r'\n$','',comment)
        comment = comment + '\n......'
    if comment != '':
        comment = ':\n' + comment
    msg += comment
  
  return msg


async def getAnime(pid):
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
  