from typing import Callable
import config


class Filter:
  """
  事件过滤器
  
  可与同类进行:
    - 非运算 ``~ Filter``
    - 与运算 ``Filter & Filter``
    - 或运算 ``Filter | Filter``
    - 异或运算 ``Filter ^ Filter``
    
  Arguments
    value (`Callable[[Any], bool]`):
      过滤函数
      
      参数需为 event, 返回值为 bool

  Members
    value (`Callable[[Any], bool]`):
      过滤函数
      
      参数需为 event, 返回值为 bool
  """

  def __init__(self, value: callable, /):
    if hasattr(value, 'filter'):
      self.value = value.filter
    else:
      self.value = value

  def filter(self, event) -> bool:
    """
    运行过滤函数进行过滤
    """
    return self.value(event)

  def __invert__(self):
    return Filter(lambda event: not self.filter(event))

  def __and__(self, other):
    return Filter(lambda event: self.filter(event) and other.filter(event))

  def __or__(self, other):
    return Filter(lambda event: self.filter(event) or other.filter(event))

  def __xor__(self, other):
    return Filter(
      lambda event: (self.filter(event) and not other.filter(event))
      or (not self.filter(event) and other.filter(event))
    )


def Command(cmd='') -> Filter:
  """
  返回一个 过滤指定命令 的过滤器
  
  Arguments:
    cmd (`str`):
      命令名
  """
  return Filter(lambda event: event.message.message.startswith('/' + cmd)) & (~FILE)

#: 过滤私聊
PRIVATE: Filter = Filter(lambda event: event.is_private)
#: 过滤频道
CHANNEL: Filter = Filter(lambda event: event.is_channel)
#: 过滤群组
GROUP: Filter = Filter(lambda event: event.is_group)

#: 是否有文本
TEXT: Filter = Filter(lambda event: event.message.message)
#: 是否有媒体
MEDIA: Filter = Filter(lambda event: event.message.media)

#: 是否有图片
PHOTO: Filter = Filter(lambda event: event.message.photo)
#: 是否有文档
DOCUMENT: Filter = Filter(lambda event: event.message.document)
#: 是否有图片或文档
#: 等价于 PHOTO | DOCUMENT
FILE: Filter = Filter(lambda event: event.message.file)

#: 是否为纯文本 (有文本且无文件)
ONLYTEXT: Filter = TEXT & (~FILE)
#: 是否是命令
COMMAND: Filter = Command()

#: 是否有链接预览
WEB_PREVIEW: Filter = Filter(lambda event: event.message.web_preview)
#: 是否有音频
AUDIO: Filter = Filter(lambda event: event.message.audio)
#: 是否有语音留言
VOICE: Filter = Filter(lambda event: event.message.voice)
#: 是否有视频
VIDEO: Filter = Filter(lambda event: event.message.video)
#: 是否有视频留言
VIDEO_NOTE: Filter = Filter(lambda event: event.message.video_note)
#: 是否有gif
GIF: Filter = Filter(lambda event: event.message.gif)
#: 是否有贴纸
STICKER: Filter = Filter(lambda event: event.message.sticker)
#: 是否有联系人分享
CONTACT: Filter = Filter(lambda event: event.message.contact)
#: 是否有游戏
GAME: Filter = Filter(lambda event: event.message.game)
#: 是否有位置 (GeoPoint media)
GEO: Filter = Filter(lambda event: event.message.geo)
#: 是否有发票
INVOICE: Filter = Filter(lambda event: event.message.invoice)
#: 是否有投票
POLL: Filter = Filter(lambda event: event.message.poll)
#: 是否有 MessageMediaVenue
VENUE: Filter = Filter(lambda event: event.message.venue)
#: 是否有 MessageMediaDice, 骰子
DICE: Filter = Filter(lambda event: event.message.dice)

#: 是否来自机器人
VIA_BOT: Filter = Filter(lambda event: event.message.via_bot)
#: 是否有按钮
BUTTON: Filter = Filter(lambda event: event.message.buttons)

#: 是否回复某消息
REPLY: Filter = Filter(lambda event: event.message.is_reply)
#: 是否是转发消息
FORWARD: Filter = Filter(lambda event: event.message.forward)

SUPERADMIN: Filter = Filter(lambda event: event.chat_id in config.superadmin)