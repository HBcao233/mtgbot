import os.path
import config


def _getFile(path='', name=''):
  """
  获取指定目录的指定文件
  """
  name = name.replace('\\', '/')
  f = os.path.join(path, name)
  return f


def getFile(dir_name='', name=''):
  """
  获取指定bot私有目录下目录名的指定文件
  """
  name = str(name)
  path = os.path.join(config.botHome, dir_name)
  if '/' in name:
    p, name = os.path.split(name)
    path = os.path.join(path, p)
  if name == '':
    return path
  return _getFile(path, name)


def getResourceFile(name=''):
  """
  获取resources文件夹下文件
  """
  return getFile('resources/', name)


getResource = getResourceFile


def getDataFile(name=''):
  """
  获取data文件夹下文件
  """
  path = getFile('data/')
  if not os.path.isdir(path):
    os.mkdir(path)
  return getFile('data/', name)


def getCacheFile(name=''):
  """
  获取data/cache文件夹下文件
  """
  path = getDataFile('cache/')
  if not os.path.isdir(path):
    os.mkdir(path)
  return getDataFile(os.path.join('cache/', str(name)))


getCache = getCacheFile
