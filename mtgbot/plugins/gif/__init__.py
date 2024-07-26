from telethon import types
import os.path 

import config
import util
from util import logger
from plugin import handler
from .data_source import video2gif, tgs2gif, getLottiePath, video2ext


@handler('gif', info="视频转gif")
async def _gif(event):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  logger.info(reply_message)
  mime_type = reply_message.media.document.mime_type
  if mime_type == 'image/gif':
    return await event.reply('该消息已经是 gif 格式了')
  if 'video' not in mime_type and mime_type != 'application/x-tgsticker':
    return await event.reply('该消息不包含视频或动态贴纸')
  for i in v.attributes:
    if isinstance(i, types.DocumentAttributeVideo):
      break
  if i.duration > 60:
    await event.reply('这个视频太长了')
  
  mid = await event.reply('转换中...')
  
  data = util.Documents()
  document_id = reply_message.media.document.id
  if (document := data[document_id]) and len(document) == 4 and document[3] == 'image/gif':
    file=types.Document(
      id=document[0],
      access_hash=document[1],
      date=None,
      mime_type='image/gif',
      size=0,
      thumbs=None,
      dc_id=document[2],
      attributes=[types.DocumentAttributeAnimated()],
      file_reference=b''
    )
  else:
    img = util.getCache(document_id)
    if not os.path.isfile(img):
      await reply_message.download_media(file=img)
    
    if mime_type == 'application/x-tgsticker':
      lottiepath = getLottiePath()
      if lottiepath is None:
        return await mid.edit('暂不支持动态贴纸转换')
      res = await tgs2gif(lottiepath, img)
    else:
      res = await video2gif(img)
    if not res:
      return await mid.edit('转换失败')
      
    document = open(res, 'rb')
    file = await config.bot.upload_file(document)
  
  mid = await mid.edit('发送中...')
  res = await event.reply(
    file=file,
    force_document=True,
    attributes=[types.DocumentAttributeAnimated()],
  )
  await mid.delete()
  with data:
    v = res.media.document
    data[document_id] = [v.id, v.access_hash, v.dc_id, v.mime_type]
  
  
async def _video_convert(event, ext='mp4'):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  logger.info(reply_message)
  mime_type = reply_message.media.document.mime_type
  if 'video' not in mime_type and mime_type not in ['application/x-tgsticker', 'image/gif']:
    return await event.reply('该消息不包含视频或动态贴纸')
  if mime_type == 'video/' + ext:
    return await event.reply(f'该消息已经是 {ext} 格式了')
  
  mid = await event.reply('转换中...')
  
  data = util.Videos()
  document_id = reply_message.media.document.id
  
  if (document := data[document_id]) and len(document) == 7 and document[3] == 'image/gif':
    file=types.Document(
      id=document[0],
      access_hash=document[1],
      date=None,
      mime_type='video/mp4',
      size=0,
      thumbs=None,
      dc_id=document[2],
      attributes=[types.DocumentAttributeVideo(duration=document[4], w=int(document[5]), h=int(document[6]), supports_streaming=True)],
      file_reference=b''
    )
  else:
    img = util.getCache(document_id)
    if not os.path.isfile(img):
      await reply_message.download_media(file=img)
    
    if mime_type == 'application/x-tgsticker':
      lottiepath = getLottiePath()
      if lottiepath is None:
        return await mid.edit('暂不支持动态贴纸转换')
      img = await tgs2gif(lottiepath, img)
      if not img:
        return await mid.edit('转换失败')
     
    res = await video2ext(img, 'mp4')
    if not res:
      return await mid.edit('转换失败')
    
    document, duration, w, h, thumb = util.videoInfo(res)
    document = await config.bot.upload_file(document)
    thumb = await config.bot.upload_file(thumb)
    file = types.InputMediaUploadedDocument(
      file=document,
      mime_type='video/' + ext, 
      attributes=[types.DocumentAttributeVideo(duration=int(duration), w=int(w), h=int(h), supports_streaming=True)],
      thumb=thumb,
    )
  
  mid = await mid.edit('发送中...')
  res = await event.reply(file=file)
  await mid.delete()
  with data:
    v = res.media.document
    for i in v.attributes:
      if isinstance(i, types.DocumentAttributeVideo):
        break
    data[document_id] = [v.id, v.access_hash, v.dc_id, v.mime_type, i.duration, i.w, i.h]


@handler('mp4', info="动图转mp4")
async def _mp4(event):
  await _video_convert(event, 'mp4')
  
  
@handler('webm', info='视频转webm')
async def _webm(event):
  await _video_convert(event, 'webm')
  