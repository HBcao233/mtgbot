from telethon import types, utils
import ujson as json
import os.path
import sqlite3

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
    # return dict(id=v.id, access_hash=v.access_hash, dc_id=v.dc_id)
    
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
  

class MessageData():
  _conn = sqlite3.connect(getDataFile('messages.db'))
  inited = False
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
  def add_message(cls, chat_id, message_id, grouped_id=None):
    chat_id = utils.get_peer_id(chat_id)
    if isinstance(message_id, types.Message):
      grouped_id = getattr(message_id, 'grouped_id', None)
      message_id = message_id.id
    cls.init()
    if cls.has_message(chat_id, message_id):
      return
    logger.debug(f'add_message chat_id: {chat_id}, message_id: {message_id}, grouped_id: {grouped_id}')
    
    r = cls._conn.execute(f"insert into messages(chat_id, message_id, grouped_id) values(?,?,?)", (chat_id, message_id, grouped_id))
    cls._conn.commit()
    return r.fetchone()
  
  @classmethod
  def get_chat(cls, chat_id):
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
   
    r = cls._conn.execute(f"SELECT id FROM messages WHERE chat_id='{chat_id}'")
    if (res := r.fetchone()):
      return res[0]
    return None
  
  @classmethod
  def has_chat(cls, chat_id):
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
    return cls.get_chat(chat_id) is not None
  
  @classmethod
  def get_message(cls, chat_id, message_id=None):
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
      return res[0]
    return None
  
  @classmethod
  def get_message_by_mid(cls, mid):
    cls.init()
    r = cls._conn.execute(f"SELECT chat_id, message_id FROM messages WHERE id='{mid}'")
    if (res := r.fetchone()):
      return res[0], res[1]
    return None, None
    
  @classmethod
  def has_message(cls, chat_id, message_id):
    cls.init()
    chat_id = utils.get_peer_id(chat_id)
    if isinstance(message_id, types.Message):
      message_id = message_id.id
    return cls.get_message(chat_id, message_id) is not None
  
  @classmethod
  def iter_chats(cls):
    cls.init()
    _set = set()
    _id = 0
    while True:
      r = cls._conn.execute(f"SELECT chat_id, id FROM messages WHERE id > '{_id}' ORDER BY id ASC LIMIT 1")
      if not (res := r.fetchone()):
        break
      chat_id, _id = res
      if chat_id is None:
        break
      if chat_id not in _set:
        yield chat_id
      _set.add(chat_id)
      
  @classmethod
  def iter_messages(cls, chat_id, *, offset_id=None, reverse=False):
    chat_id = utils.get_peer_id(chat_id)
    cls.init()
    _id = 0
    while True:
      offset = ''
      sort = 'ASC'
      t = f"and id > '{_id}'"
      if offset_id: offset = f"and message_id > '{offset_id}'"
        
      if reverse:
        sort = 'DESC'
        t = ''
        if t != 0:
          t = f"and id < '{_id}'"
        if offset_id: offset = f"and message_id < '{offset_id}'"
      
      r = cls._conn.execute(f"SELECT message_id, id FROM messages WHERE chat_id = '{chat_id}' {t} {offset} ORDER BY id {sort} LIMIT 1")
      if not (res := r.fetchone()):
        break
      message_id, _id = res
      if message_id is None:
        break
      yield message_id
  
  @classmethod
  def get_group(cls, grouped_id: int) -> list[int]:
    cls.init()
    r = cls._conn.execute(f"SELECT message_id FROM messages WHERE grouped_id='{grouped_id}'")
    if (res := r.fetchall()):
      return [i[0] for i in res]
    return []
    