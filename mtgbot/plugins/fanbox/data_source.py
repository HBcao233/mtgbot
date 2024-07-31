import traceback
import re
import util
from util import logger


class PluginException(Exception):
  pass


async def get_post(pid):
  try:
    headers={
      'origin': 'https://www.fanbox.cc',
      'referer': 'https://www.fanbox.cc/',
    }
    url = f"https://api.fanbox.cc/post.info?postId={pid}"
    r = await util.get(url, headers=headers)
  except Exception:
    logger.error(traceback.format_exc())
    raise PluginException('连接错误')
  res = r.json()
  if res.get("error", None):
    logger.error(r.text)
    raise PluginException(res["error"])
  return res['body']
  
  
def parse_msg(res, hide=False):
  pid = res["id"]
  title = res['title']
  creatorId = res['creatorId']
  uid = res['user']['userId']
  username = res['user']['name']
  msg = f"<a href=\"https://{creatorId}.fanbox.cc/posts/{pid}\">{title}</a> - <a href=\"https://{creatorId}.fanbox.cc\">{username}</a>"
  
  body = res.get('body', None) if res.get('body', None) else {}
  if hide:
    return msg
  text = (
    body.get('text', '')
    .replace("<br />", "\n")
    .replace("<br/>", "\n")
    .replace("<br>", "\n")
    .replace(' target="_blank"', "")
  )
  if not text and body.get('blocks', []):
    length = 0
    texts = [i['text'] for i in body['blocks'] if i['type'] == 'p']
    index = 0
    while (l := length + len(texts[index])) < 400:
      index += 1
      length = l
    text = '\n'.join(texts[:index])
    if index < len(texts) - 1:
      text += '\n......'
  text = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', text)
  if text:
    msg += ': \n' + text
  return msg


def parse_medias(res):
  medias = []
  body = res.get('body', None) if res.get('body', None) else {}
  for i in body.get('images', []) + list(body.get('imageMap', {}).values()):
    media = {
      'type': 'image',
      'ext': i['extension'],
      'name': i['id'],
      'url': i['originalUrl'],
      'thumbnail': i['thumbnailUrl'],
    }
    medias.append(media)
  return medias