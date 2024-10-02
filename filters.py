class Filter:
  def __init__(self, value, /):
    if hasattr(value, 'filter'):
      self.value = value.filter
    else:
      self.value = value

  def filter(self, event) -> bool:
    return self.value(event)

  def __and__(self, other):
    return Filter(lambda event: self.filter(event) and other.filter(event))

  def __or__(self, other):
    return Filter(lambda event: self.filter(event) or other.filter(event))

  def __xor__(self, other):
    return Filter(
      lambda event: (self.filter(event) and not other.filter(event))
      or (not self.filter(event) and other.filter(event))
    )

  def __invert__(self):
    return Filter(lambda event: not self.filter(event))


def Command(cmd='') -> Filter:
  return Filter(lambda event: event.message.message.startswith('/' + cmd)) & (~MEDIA)


PRIVATE = Filter(lambda event: event.is_private)
CHANNEL = Filter(lambda event: event.is_channel)
GROUP = Filter(lambda event: event.is_group)

TEXT = Filter(lambda event: event.message.message)
MEDIA = Filter(lambda event: event.message.media)
ONLYTEXT = TEXT & (~MEDIA)
COMMAND = Command()

PHOTO = Filter(lambda event: event.message.photo)
DOCUMENT = Filter(lambda event: event.message.document)
WEB_PREVIEW = Filter(lambda event: event.message.web_preview)
AUDIO = Filter(lambda event: event.message.audio)
VOICE = Filter(lambda event: event.message.voice)
VIDEO = Filter(lambda event: event.message.video)
VIDEO_NOTE = Filter(lambda event: event.message.video_note)
GIF = Filter(lambda event: event.message.gif)
STICKER = Filter(lambda event: event.message.sticker)
CONTACT = Filter(lambda event: event.message.contact)
GAME = Filter(lambda event: event.message.game)
GEO = Filter(lambda event: event.message.geo)
INVOICE = Filter(lambda event: event.message.invoice)
POLL = Filter(lambda event: event.message.poll)
VENUE = Filter(lambda event: event.message.venue)
DICE = Filter(lambda event: event.message.dice)

VIA_BOT = Filter(lambda event: event.message.via_bot)
BUTTON = Filter(lambda event: event.message.buttons)

REPLY = Filter(lambda event: event.message.is_reply)
FORWARD = Filter(lambda event: event.message.forward)
