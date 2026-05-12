import sqlite3
import re
import threading

from telethon import events, functions, types, Button
import filters
import config
from plugin import Command, Scope
from util.file import getDataFile


class GroupConfig:
  _conn = None
  _lock = threading.Lock()

  @classmethod
  def _init(cls):
    with cls._lock:
      if cls._conn is not None:
        return

      path = getDataFile('group_config.db')
      cls._conn = sqlite3.connect(path, check_same_thread=False)
      cls._conn.row_factory = sqlite3.Row

      res = cls._conn.execute('PRAGMA user_version').fetchone()
      user_version = int(res[0]) if res else 0
      if user_version == 0:
        cls._migrate_v0_to_v1()

  @classmethod
  def _migrate_v0_to_v1(cls):
    cls._conn.execute("""CREATE TABLE group_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    UNIQUE(chat_id, config_key)
    )""")
    cls._conn.execute(
      'CREATE INDEX if not exists group_config_chat_id_index ON group_config (chat_id)'
    )

    cls._conn.execute('PRAGMA user_version=1')
    cls._conn.commit()

  @classmethod
  def get_config(cls, chat_id: int, config_key: str) -> str | None:
    cls._init()

    r = cls._conn.execute(
      'SELECT config_value FROM group_config WHERE chat_id=? AND config_key=?',
      (chat_id, config_key),
    )
    if res := r.fetchone():
      return res['config_value']
    return None

  @classmethod
  def set_config(cls, chat_id: int, config_key: str, config_value: str) -> bool:
    cls._init()

    with cls._lock:
      cls._conn.execute(
        """INSERT INTO group_config (chat_id, config_key, config_value) 
      VALUES (?, ?, ?)
      ON CONFLICT(chat_id, config_key)
      DO UPDATE SET config_value=excluded.config_value
      """,
        (chat_id, config_key, config_value),
      )
      cls._conn.commit()
      return True
  
  @classmethod
  def remove_config(cls, chat_id: int, config_key: str) -> bool:
    cls._init()
    
    with cls._lock:
      cur = cls._conn.execute(
          'DELETE FROM group_config WHERE chat_id=? AND config_key=?',
          (chat_id, config_key),
      )
      cls._conn.commit()
      return cur.rowcount > 0

  @classmethod
  def iter_config_by_prefix(cls, prefix: str):
    cls._init()
    
    prefix = prefix.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    query_param = f'{prefix}%'
    r = cls._conn.execute(
      """SELECT *
      FROM group_config
      WHERE config_key LIKE ? ESCAPE '\\'""",
      (query_param,)
    )
    for row in r.fetchall():
      yield row


group_config_buttons = []


def render_buttons(chat_id: int):
  buttons = []
  index = 0
  for btn in group_config_buttons:
    if index == len(buttons):
      buttons.append([])

    config_key = btn.config_key
    config_value = GroupConfig.get_config(chat_id, config_key)
    text = btn.on_text if config_value == '1' else btn.off_text
    buttons[index].append(Button.inline(text, btn.data))
    if len(buttons[index]) == 1:
      index += 1

  buttons.append([Button.inline('关闭面板', data=b'delete#')])
  return buttons


class GroupConfigSwitch:
  def __init__(
    self,
    config_key: str,
    off_text: str,
    on_text: str = None,
  ):
    self.config_key = config_key
    self.off_text = off_text
    if not on_text:
      on_text = '✅ ' + off_text
    self.on_text = on_text

    self.data = b'gc_' + config_key.encode()
    self.pattern = re.compile(b'^' + self.data + b'$').match

  def get_config(self, chat_id: int):
    return GroupConfig.get_config(chat_id, self.config_key)

  def set_config(self, chat_id: int, config_value: str):
    return GroupConfig.set_config(chat_id, self.config_key, config_value)

  def switch(self, chat_id: int):
    old_value = self.get_config(chat_id)
    new_value = '0' if old_value == '1' else '1'
    self.set_config(chat_id, new_value)

  @staticmethod
  def add(
    config_key: str,
    off_text: str,
    on_text: str = None,
  ):
    gc_btn = GroupConfigSwitch(
      config_key,
      off_text,
      on_text,
    )
    group_config_buttons.append(gc_btn)

    async def _func(event, *args, **kwargs):
      chat_id = event.chat_id
      sender_id = event.sender_id
      sender_permissions = await bot.get_permissions(chat_id, sender_id)
      if not sender_permissions.is_admin:
        await event.answer('仅管理员可以修改。', alert=True)
        return
      
      gc_btn.switch(chat_id)

      buttons = render_buttons(chat_id)
      await event.edit(buttons=buttons)
      await event.answer()

    config.bot.add_event_handler(_func, events.CallbackQuery(pattern=gc_btn.pattern))
    return _func


async def get_linked_channel_id(chat_id):
  full_info = await bot(functions.channels.GetFullChannelRequest(channel=chat_id))
  linked_id = full_info.full_chat.linked_chat_id

  if linked_id:
    return -linked_id - 100_00000_00000
  else:
    return None


@Command(
  'config',
  enable=(lambda: len(group_config_buttons) > 0),
  info='群聊配置',
  scope=Scope.chats(),
  filter=filters.GROUP,
)
async def _settings(event):
  """
  群聊配置命令

  :meta public:
  """
  if not event.is_group:
    return
  
  await event.message.delete()

  chat_id = event.chat_id
  sender_id = event.sender_id
  # 不是当前群身份
  if sender_id != chat_id:
    # 是普通用户
    if sender_id > 0:
      sender_permissions = await bot.get_permissions(chat_id, sender_id)
      if not sender_permissions.is_admin:
        return
    # 是频道
    else:
      linked_channel_id = await get_linked_channel_id(chat_id)
      if linked_channel_id is None:
        return
      # 是当前群聊关联的频道
      if sender_id != linked_channel_id:
        return
  
  buttons = render_buttons(chat_id)

  caption = '小派魔的群聊配置'
  await event.reply(
    caption,
    buttons=buttons,
  )
