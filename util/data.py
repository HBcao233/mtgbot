from telethon import types, utils
import ujson as json
import os.path

from .file import getDataFile


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
    