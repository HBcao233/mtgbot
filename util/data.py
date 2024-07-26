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
    return 'Data' + str(self.data)
    
  def __repr__(self):
    return 'Data' + repr(self.data)
  
  def __contains__(self, key):
    return key in self.data
  
  def __len__(self):
    return len(self.data)
    
  def __getitem__(self, key, default=None):
    return self.data.get(str(key), default)
    
  def __setitem__(self, key, value):
    self.data[str(key)] = value
  
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

class Videos(Data):
  def __init__(self):
    super().__init__('videos')

class Documents(Data):
  def __init__(self):
    super().__init__('documents')
