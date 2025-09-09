from dowhen import when
from telethon import utils
from telethon.extensions.html import HTMLToTelegramParser
import inspect


def html_callback(attrs, args):
  if 'expandable' in attrs.keys():
    args['collapsed'] = True
    return {'args': args}


when(HTMLToTelegramParser.handle_starttag, 'EntityType = MessageEntityBlockquote').do(
  html_callback
)


def pack_callback():
  return {
    'size': type(
      'PhotoSize',
      (),
      {
        'volume_id': 0,
        'local_id': 0,
      },
    )
  }


code = inspect.getsource(utils.pack_bot_file_id).split('\n')
any(
  (line := i) and code[i].strip().startswith('size = size.location')
  for i in range(len(code))
)
when(utils.pack_bot_file_id, 'size = size.location').goto(f'+{line + 1}').do(
  pack_callback
)
