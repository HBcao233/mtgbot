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
  if 'video' not in mime_type and mime_type != 'application/x-tgsticker':
    return await event.reply('该消息不包含视频或动态贴纸')
  
  attributes = reply_message.media.document. attributes
  a = None
  _ext = '.cache'
  for i in attributes:
    if isinstance(i, types.DocumentAttributeVideo):
      a = i
    if isinstance(i, types.DocumentAttributeFilename):
      _ext = os.path.splitext(i.file_name)[-1]
      
  if a.duration > 60:
    await event.reply('这个视频太长了')
  if mime_type == 'image/gif':
    return await event.reply('该消息已经是 gif 格式了')
    
  mid = await event.reply('转换中...')
  
  data = util.Documents()
  document_id = reply_message.media.document.id
  key = f'{document_id}_to_gif'
  if not (file := data[key]):
    img = util.getCache(str(document_id) + _ext)
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
      
    file = open(res, 'rb')
  
  mid = await mid.edit('发送中...')
  res = await event.reply(
    file=file,
    force_document=True,
    attributes=[types.DocumentAttributeAnimated()],
  )
  await mid.delete()
  with data:
    data[key] = res
  
  
async def _video_convert(event, ext='mp4'):
  if not (reply_message := await event.message.get_reply_message()):
    return await event.reply('请用命令回复一条消息')
  logger.info(reply_message)
  mime_type = reply_message.media.document.mime_type
  if 'video' not in mime_type and mime_type not in ['application/x-tgsticker', 'image/gif']:
    return await event.reply('该消息不包含视频或动态贴纸')
 
  attributes =reply_message.media.document.attributes
  is_sticker = False
  _ext = '.cache'
  for i in attributes:
    if isinstance(i, types.DocumentAttributeSticker):
      is_sticker = True
      break
    if isinstance(i, types.DocumentAttributeFilename):
        _ext = os.path.splitext(i.file_name)[-1]
        
  if not is_sticker and mime_type == 'video/' + ext:
    return await event.reply(f'该消息已经是 {ext} 格式了')
    
  mid = await event.reply('转换中...')
  data = util.Videos()
  document_id = reply_message.media.document.id
  key = f'{document_id}_to_{ext}'
  thumb = None
  attributes = None
  if not (file := data[key]):
    img = util.getCache(str(document_id) + _ext)
    if not os.path.isfile(img):
      await reply_message.download_media(file=img)
    
    if mime_type == 'video/' + ext:
      res = img
    else:
      if mime_type == 'application/x-tgsticker':
        lottiepath = getLottiePath()
        if lottiepath is None:
          return await mid.edit('暂不支持动态贴纸转换')
        img = await tgs2gif(lottiepath, img)
        if not img:
          return await mid.edit('转换失败')
     
      res = await video2ext(img, ext, mid)
      if not res:
        return await mid.edit('转换失败')
  
    file, duration, w, h, thumb = util.videoInfo(res)
    attributes = [
      types.DocumentAttributeVideo(duration=duration, w=int(w), h=int(h), supports_streaming=True), 
      types.DocumentAttributeFilename(file_name=f'{document_id}.{ext}')
    ]
  
  mid = await mid.edit('发送中...')
  res = await event.reply(
    file=file,
    supports_streaming=True,
    thumb=thumb,
    attributes=attributes,
  )
  logger.info('result: %s', res)
  await mid.delete()
  with data:
    data[key] = res


@handler('mp4', info="动图转mp4")
async def _mp4(event):
  await _video_convert(event, 'mp4')
  
  
@handler('webm', info='视频转webm')
async def _webm(event):
  await _video_convert(event, 'webm')
  