from telethon import types, utils
import ujson as json
import os.path
import sqlite3
from typing import Union
from collections import namedtuple

from .file import getDataFile
from .log import logger


def getData(file: str) -> dict:
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
  with open(getDataFile(f'{file}.json'), 'w') as f:
    f.write(json.dumps(data, indent=4))
    
    
class Data(object):
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, '__instance'):
      cls.__instance = super().__new__(cls)
    return cls.__instance
  
  def __init__(self, file: str):
    self.file = file
    self.data = getData(file)
    
  def __str__(self):
    return f'Data(file={self.file}, data={self.data})'
    
  def __repr__(self):
    return self.__repr__()
  
  def __contains__(self, key):
    return key in self.data
  
  def __len__(self):
    return len(self.data)
    
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
    print(f'del data {key}')
    self.data.pop(key)
    
  def get(self, key, default=None):
    return self.__getitem__(key, default)
  
  def keys(self):
    return self.data.keys()
    
  def items(self):
    return self.data.items()
    
  def values(self):
    return self.data.values()
    
  def save(self):
    setData(self.file, self.data)
    
  def __enter__(self):
    return self
    
  def __exit__(self, type, value, trace):
    self.save()
    
  def __iter__(self):
    return iter(self.data)
    

class Photos(Data):
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
  def __init__(self):
    super().__init__('videos')
    
class Animations(Documents):
  def __init__(self):
    super().__init__('animations')



def namedtuple_factory(cursor, row):
  fields = [column[0] for column in cursor.description]
  cls = namedtuple("Row", fields, rename=True)
  cls.__repr__ = lambda self: 'Row(' + (', '.join([
    f'{repr(_k) if k.startswith("_") else k}={getattr(self, k)}'
    for k, _k in zip(self._fields, fields)
  ])) + ')'
  return cls._make(row)


class MessageData():
  _conn = sqlite3.connect(getDataFile('messages.db'))
  _conn.row_factory = namedtuple_factory
  inited = False
  
  def __new__(cls):
    if not hasattr(cls, '__instance'):
      cls.__instance = super().__new__(cls)
    return cls.__instance

  def __init__(self):
    self.init()

  @classmethod
  def init(cls):
    if cls.inited: return
    cls._conn.execute(f"CREATE TABLE if not exists messages(id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL)")
    cls._conn.execute(f"CREATE UNIQUE INDEX if not exists id_index ON messages (id)")
    r = cls._conn.execute(f"select count(name) from sqlite_master where type='table' and name='messages' and sql like '%grouped_id%'")
    if not (res := r.fetchone()) or res[0] == 0:
      cls._conn.execute(f"ALTER TABLE messages ADD COLUMN grouped_id INTEGER DEFAULT value NULL")
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
    logger.debug(f'add_message chat_id: {chat_id}, message_id: {message_id}, grouped_id: {grouped_id}')
    
    cursor = cls._conn.cursor()
    cursor.execute(f"insert into messages(chat_id, message_id, grouped_id) values(?,?,?)", (chat_id, message_id, grouped_id))
    cls._conn.commit()
    return cursor.lastrowid

  @classmethod
  def has_chat(cls, chat_id):
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
    r = cls._conn.execute(f"SELECT id FROM messages WHERE chat_id='{chat_id}'")
    if r.fetchone():
      return True
    return False

  @classmethod
  def get_message(cls, chat_id: Union[int, types.Message], message_id: int = None):
    """
    MessageData.get_message(message: types.Message)
    MessageData.get_message(chat_id: int, message_id: int)
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
    
    r = cls._conn.execute(f"SELECT * FROM messages WHERE chat_id='{chat_id}' and message_id='{message_id}'")
    if (res := r.fetchone()):
      return res
    return None

  @classmethod
  def get_message_by_rid(cls, rid):
    """
    通过记录id获取message
    """
    cls.init()
    r = cls._conn.execute(f"SELECT * FROM messages WHERE id='{rid}'")
    if (res := r.fetchone()):
      return res
    return None, None

  @classmethod
  def get_message_by_mid(cls, mid):
    logger.warning('DeprecationWarning: Use MessageData.get_message_by_rid instead')
    return cls.get_message_by_rid(mid)

  @classmethod
  def has_message(cls, chat_id, message_id=None):
    """
    MessageData.has_message(message: types.Message)
    MessageData.has_message(chat_id: int, message_id: int)
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

    r = cls._conn.execute(f"SELECT id FROM messages WHERE chat_id='{chat_id}' and message_id='{message_id}'")
    if (res := r.fetchone()):
      return True
    return False

  @classmethod
  def iter_chats(cls):
    cls.init()
    offset = 0
    while True:
      r = cls._conn.execute(f"SELECT DISTINCT chat_id FROM messages LIMIT 100 OFFSET {offset}")
      if not (res := r.fetchall()):
        break
      offset += len(res)
      for i in res:
        yield i.chat_id


  @classmethod
  def iter_messages(cls, 
    chat_id: int, 
    *, 
    reverse: bool = False, 
    min_id: int = None, 
    max_id: int = None
  ):
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
      
      r = cls._conn.execute(f"SELECT message_id FROM messages WHERE {wheres} ORDER BY id {sort} LIMIT 100 OFFSET {_offset}")
      if not (res := r.fetchall()):
        break
      offset += len(res)
      for i in res:
        yield i.message_id

  @classmethod
  def get_group(cls, grouped_id: int) -> list[int]:
    cls.init()
    r = cls._conn.execute(f"SELECT message_id FROM messages WHERE grouped_id='{grouped_id}'")
    if (res := r.fetchall()):
      return [i[0] for i in res]
    return []
