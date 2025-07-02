from telethon.events.common import EventCommon
import ujson as json
import inspect

import util
import config
from util.log import logger


async def createPage(title, content):
  _author_name = config.telegraph_author_name
  _author_url = config.telegraph_author_url
  with util.data.Settings() as data:
    if (
      data['telegraph'] is not None
      and (
        data['telegraph'].get('author_name', None)
        or data['telegraph'].get('author_url', None)
      )
      and (
        len(data['telegraph']['author_name'].keys()) > 0
        or len(data['telegraph']['author_url'].keys()) > 0
      )
    ):
      if data['telegraph'].get('author_name', None) is None:
        data['telegraph']['author_name'] = {}
      if data['telegraph'].get('author_url', None) is None:
        data['telegraph']['author_url'] = {}

      chat_id = None
      for i in inspect.stack():
        if chat_id:
          break
        for j in i.frame.f_locals.values():
          if isinstance(j, EventCommon):
            chat_id = j.chat_id
            break

      logger.debug(chat_id)
      if chat_id:
        if str(chat_id) in data['telegraph']['author_name']:
          _author_name = data['telegraph']['author_name'][str(chat_id)]
        if str(chat_id) in data['telegraph']['author_url']:
          _author_url = data['telegraph']['author_url'][str(chat_id)]

  if not isinstance(content, str):
    content = json.dumps(content)
  # logger.info(content)
  r = await util.post(
    'https://api.telegra.ph/createPage',
    data={
      'title': title,
      'content': content,
      'access_token': config.telegraph_access_token,
      'author_name': _author_name,
      'author_url': _author_url,
    },
  )
  if r.status_code != 200:
    return {'code': 1, 'message': '请求失败'}
  res = r.json()
  if not res['ok']:
    logger.warn(res)
    return {'code': 1, 'message': res['error']}
  return res['result']['url']


async def getPageList():
  try:
    r = await util.post(
      'https://api.telegra.ph/getPageList',
      data={
        'access_token': config.telegraph_access_token,
        'limit': 200,
      },
    )
    return r.json()['result']['pages']
  except Exception:
    return []
