import asyncio
import ujson as json

import util
import config
from util.log import logger


async def createPage(title, content):
  if type(content) != str:
    content = json.dumps(content)
  r = await util.post(
    'https://api.telegra.ph/createPage', 
    data={
      'title': title,
      'content': content,
      'access_token': config.telegraph_access_token,
      'author_name': config.telegraph_author_name,
      'author_url': config.telegraph_author_url,
    },
  )
  logger.info(r.text)
  if r.status_code != 200:
    return False
  res = r.json()
  if not res['ok']:
    return False
  return res['result']['url']
  
async def getPageList():
  try:
    r = await util.post(
      'https://api.telegra.ph/getPageList', 
      data={
        'access_token': config.telegraph_access_token,
        'limit': 200,
      }
    )
    return r.json()['result']['pages']
  except:
    return []
  