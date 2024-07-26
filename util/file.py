import os.path
import config


def _getFile(path='', name=''):
  f = os.path.join(path, name)
  if os.path.isfile(f) or '.' in name:
    return f
    
  f = os.path.join(path, f'{name}.cache')
  if os.path.isfile(f):
    return f
  
  for i in os.listdir(path):
    if os.path.splitext(i)[0] == name:
      return i
  
  return os.path.join(path, f'{name}.cache')
  
def getFile(dir_name='', name=''):
  name = str(name)
  path = os.path.join(config.botRoot, dir_name)
  if '/' in name:
    p, name = os.path.split(name)
    path = os.path.join(path, p)
  if name == '':
    return path
  return _getFile(path, name)

def getResource(name=''):
  return getFile('resources/', name)
  
def getDataFile(name=''):
  path = getFile("data/")
  if not os.path.isdir(path):
    os.mkdir(path)
  return getFile("data/", name)
  
def getCache(name=''):
  path = getDataFile("cache/")
  if not os.path.isdir(path):
    os.mkdir(path)
  return getDataFile(os.path.join("cache/", str(name)))
  
def getWorkFile(name=''):
  return _getFile(config.workPath, name)
