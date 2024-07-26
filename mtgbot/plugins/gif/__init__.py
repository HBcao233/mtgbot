from telethon import types
import os.path 

import config
import util
from util import logger
from plugin import handler
from .data_source import video2gif, tgs2gif, getLottiePath


@handler('gif', info="视频转gif")
async def _gif(event):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  logger.info(reply_message)
  mime_type = reply_message.media.document.mime_type
  if 'video' not in mime_type and mime_type != 'application/x-tgsticker':
    return await event.reply('该消息不包含视频或动态贴纸')
  
  mid = await event.reply('转换中')
  
  data = util.Documents()
  document_id = reply_message.media.document.id
  if (document := data[document_id]):
    file=types.Document(
      id=document[0],
      access_hash=document[1],
      date=None,
      mime_type='',
      size=0,
      thumbs=None,
      dc_id=document[2],
      attributes=[types.DocumentAttributeAnimated()],
      file_reference=b''
    )
  else:
    img = util.getCache(document_id)
    if os.path.isfile(img):
      await reply_message.download_media(file=img)
    
    if mime_type == 'application/x-tgsticker':
      lottiepath = getLottiePath()
      if lottiepath is None:
        return await mid.edit('暂不支持动态贴纸转换')
      res = await tgs2gif(lottiepath, document_id)
    else:
      res = await video2gif(document_id)
    if not res:
      return await mid.edit('转换失败')
      
    document = open(res, 'rb')
    file = await config.bot.upload_file(document)
  
  await mid.delete()
  res = await event.reply(
    file=file,
    force_document=True,
    attributes=[types.DocumentAttributeAnimated()],
  )
  with data:
    v = res.media.document
    data[document_id] = [v.id, v.access_hash, v.dc_id]
  