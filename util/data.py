from telethon import types, utils
from typing import Union, Generator
from collections import namedtuple
import ujson as json
import os.path
import sqlite3

from .file import getDataFile
from .log import logger


def getData(file: str) -> dict:
  """
  读取 ``data/{file}.json`` 文件, 并将其转为字典数据

  Arguments
    file (`str`):
      文件名

  Returns
    dict: 字典数据
  """
  path = getDataFile(f'{file}.json')
  if not os.path.isfile(path):
    setData(file, dict())
  with open(path, 'r') as f:
    data = f.read()
    if data == '':
      return {}
    data = json.loads(data)
    return data


def setData(file: str, data: dict):
  """
  将字典数据转为json存入 ``data/{file}.json`` 文件

  Arguments
    file (`str`):
      文件名

    data (`dict`):
      字典数据
  """
  with open(getDataFile(f'{file}.json'), 'w') as f:
    json.dumps(data, f, indent=2)


class Data(object):
  """
  读取 ``data/{file}.json`` 文件, 并将其转为 方便py存取的格式

  .. code-block:: python

    with Data('urls') as data:
      print(data['xxx'])
      print(data.get('xxx'))
      data['xxx'] = 'yyy'
  """

  def __init__(self, file: str):
    self.file = file
    self.data = getData(file)

  def __repr__(self):
    return f'Data(file={self.file}, data={self.data})'

  def __contains__(self, key):
    return key in self.data

  def __len__(self):
    return len(self.data)

  def save(self):
    """
    保存数据
    """
    setData(self.file, self.data)

  @staticmethod
  def value_to_json(v):
    return v

  @staticmethod
  def value_de_json(v):
    return v

  def __getitem__(self, key, default=None):
    return self.value_de_json(self.data.get(str(key), default))

  def __setitem__(self, key, value):
    self.data[str(key)] = self.value_to_json(value)

  def __delitem__(self, key):
    self.data.pop(key)

  def get(self, key, default=None):
    return self.__getitem__(key, default)

  def keys(self):
    return self.data.keys()

  def items(self):
    return self.data.items()

  def values(self):
    return self.data.values()

  def __enter__(self):
    return self

  def __exit__(self, type, value, trace):
    self.save()

  def __iter__(self):
    return iter(self.data)


class Photos(Data):
  """
  保存已发送至 Telegram 的图片 file_id
  """

  def __init__(self):
    super().__init__('photos')

  @staticmethod
  def value_to_json(v):
    if v is None:
      return None
    if isinstance(v, types.Message):
      v = v.photo
    if not isinstance(v, types.Photo):
      raise ValueError('value not a photo')
    return utils.pack_bot_file_id(v)

  @staticmethod
  def value_de_json(v):
    if v is None:
      return None
    if isinstance(v, str):
      return v
    return types.Photo(
      **v,
      date=None,
      sizes=[],
      file_reference=b'',
      thumbs=None,
      has_stickers=False,
      video_sizes=[],
    )


class Documents(Data):
  """
  保存已发送至 Telegram 的文档 file_id
  """

  def __init__(self, file='documents'):
    super().__init__(file)

  @staticmethod
  def value_to_json(v):
    if v is None:
      return None
    if isinstance(v, types.Message):
      v = v.media.document
    if not isinstance(v, types.Document):
      raise ValueError('value not a document')
    return utils.pack_bot_file_id(v)

  @staticmethod
  def value_de_json(v):
    if v is None:
      return None
    if isinstance(v, str):
      return v
    return types.Document(
      **v,
      date=None,
      mime_type='',
      size=0,
      attributes=[],
      file_reference=b'',
      thumbs=None,
    )


class Videos(Documents):
  """保存已发送至 Telegram 的视频 file_id"""

  def __init__(self):
    super().__init__('videos')


class Animations(Documents):
  """保存已发送至 Telegram 的动画 file_id"""

  def __init__(self):
    super().__init__('animations')


class Audios(Documents):
  """保存已发送至 Telegram 的音频 file_id"""

  def __init__(self):
    super().__init__('audios')


class Settings(Data):
  """
  保存机器人设置
  """

  class Unset:
    pass

  unset = Unset()

  def __init__(self):
    super().__init__('settings')

  def __getitem__(self, key, default=unset):
    if isinstance(default, Settings.Unset):
      return self.value_de_json(self.data.get(str(key)))
    return self.value_de_json(self.data.get(str(key), default))

  def get(self, key, default=unset):
    if isinstance(default, Settings.Unset):
      return self.__getitem__(key)
    return self.__getitem__(key, default)


def namedtuple_factory(cursor, row):
  """
  SQLite 命名数组工厂

  :meta private:
  """
  fields = [column[0] for column in cursor.description]
  cls = namedtuple('Row', fields, rename=True)
  cls.__repr__ = (
    lambda self: 'Row('
    + (
      ', '.join(
        [
          f'{repr(_k) if k.startswith("_") else k}={getattr(self, k)}'
          for k, _k in zip(self._fields, fields)
        ]
      )
    )
    + ')'
  )
  return cls._make(row)


class MessageData:
  """
  消息id数据库
  """

  inited = False

  def __new__(cls):
    if not hasattr(cls, '__instance'):
      cls.__instance = super().__new__(cls)
    return cls.__instance

  def __init__(self):
    self.init()

  @classmethod
  def init(cls):
    if cls.inited:
      return
    cls._conn = sqlite3.connect(getDataFile('messages.db'))
    cls._conn.row_factory = namedtuple_factory
    cls._conn.execute(
      'CREATE TABLE if not exists messages(id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL)'
    )
    cls._conn.execute('CREATE UNIQUE INDEX if not exists id_index ON messages (id)')

    r = cls._conn.execute(
      "select count(name) from sqlite_master where type='table' and name='messages' and sql like '%grouped_id%'"
    )
    if not (res := r.fetchone()) or res[0] == 0:
      cls._conn.execute(
        'ALTER TABLE messages ADD COLUMN grouped_id INTEGER DEFAULT value NULL'
      )

    cls._conn.commit()
    cls.inited = True

  @classmethod
  def add_message(cls, chat_id, message_id, grouped_id=None) -> int:
    """
    记录 chat_id, message_id 并返回记录id
    """
    chat_id = utils.get_peer_id(chat_id)
    if isinstance(message_id, types.Message):
      grouped_id = getattr(message_id, 'grouped_id', None)
      message_id = message_id.id
    cls.init()
    if cls.has_message(chat_id, message_id):
      return
    logger.debug(
      f'add_message chat_id: {chat_id}, message_id: {message_id}, grouped_id: {grouped_id}'
    )

    cursor = cls._conn.cursor()
    cursor.execute(
      'insert into messages(chat_id, message_id, grouped_id) values(?,?,?)',
      (chat_id, message_id, grouped_id),
    )
    cls._conn.commit()
    return cursor.lastrowid

  @classmethod
  def has_chat(cls, chat_id):
    """是否存在chat_id"""
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
    r = cls._conn.execute(f"SELECT id FROM messages WHERE chat_id='{chat_id}'")
    if r.fetchone():
      return True
    return False

  @classmethod
  def get_message(cls, chat_id: Union[int, types.Message], message_id: int = None):
    """
    获取 message_id 列

    - `MessageData.get_message(message: types.Message)`
    - `MessageData.get_message(chat_id: int, message_id: int)`
    """
    cls.init()
    if isinstance(chat_id, types.Message):
      if message_id is None:
        message_id = chat_id.id
      chat_id = chat_id.peer_id
    chat_id = utils.get_peer_id(chat_id)
    if isinstance(message_id, types.Message):
      message_id = message_id.id
    if message_id is None:
      raise ValueError('message_id is not offered')

    r = cls._conn.execute(
      f"SELECT * FROM messages WHERE chat_id='{chat_id}' and message_id='{message_id}'"
    )
    if res := r.fetchone():
      return res
    return None

  @classmethod
  def get_message_by_rid(cls, rid):
    """
    通过记录id获取message
    """
    cls.init()
    r = cls._conn.execute(f"SELECT * FROM messages WHERE id='{rid}'")
    if res := r.fetchone():
      return res
    return None, None

  @classmethod
  def get_message_by_mid(cls, mid):
    logger.warning('DeprecationWarning: Use MessageData.get_message_by_rid instead')
    return cls.get_message_by_rid(mid)

  @classmethod
  def has_message(cls, chat_id, message_id=None):
    """
    是否存在 message_id

    - `MessageData.has_message(message: types.Message)`
    - `MessageData.has_message(chat_id: int, message_id: int)`
    """
    cls.init()
    if isinstance(chat_id, types.Message):
      if message_id is None:
        message_id = chat_id.id
      chat_id = chat_id.peer_id
    chat_id = utils.get_peer_id(chat_id)
    if isinstance(message_id, types.Message):
      message_id = message_id.id
    if message_id is None:
      raise ValueError('message_id is not offered')

    r = cls._conn.execute(
      f"SELECT id FROM messages WHERE chat_id='{chat_id}' and message_id='{message_id}'"
    )
    if r.fetchone():
      return True
    return False

  @classmethod
  def iter_chats(cls) -> Generator[int, None, None]:
    """
    枚举 chat_id

    Returns
      `Generator[int, None, None]`
    """
    cls.init()
    offset = 0
    while True:
      r = cls._conn.execute(
        f'SELECT DISTINCT chat_id FROM messages LIMIT 100 OFFSET {offset}'
      )
      if not (res := r.fetchall()):
        break
      offset += len(res)
      for i in res:
        yield i.chat_id

  @classmethod
  def iter_messages(
    cls, chat_id: int, *, reverse: bool = False, min_id: int = None, max_id: int = None
  ) -> Generator[int, None, None]:
    """
    枚举某 chat 中的 message_id

    Arguments
      chat_id (`int`):
        chat_id

      reverse (`bool`):
        是否反向

        - ``False``: 由小到大
        - ``True``: 由大到小

      min_id (`int`):
        最小id

      max_id (`int`):
        最大id
    """
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
    _offset = 0
    while True:
      sort = 'ASC'
      if reverse:
        sort = 'DESC'
      wheres = [f"chat_id = '{chat_id}'"]
      if min_id:
        wheres.append(f"message_id >= '{min_id}'")
      if max_id:
        wheres.append(f"message_id <= '{max_id}'")
      wheres = ' and '.join(wheres)

      r = cls._conn.execute(
        f'SELECT message_id FROM messages WHERE {wheres} ORDER BY id {sort} LIMIT 100 OFFSET {_offset}'
      )
      if not (res := r.fetchall()):
        break
      _offset += len(res)
      for i in res:
        yield i.message_id

  @classmethod
  def get_group(cls, grouped_id: int) -> list[int]:
    """
    根据 grouped_id 获取一组 message_id
    """
    cls.init()
    r = cls._conn.execute(
      f"SELECT message_id FROM messages WHERE grouped_id='{grouped_id}'"
    )
    if res := r.fetchall():
      return [i[0] for i in res]
    return []
