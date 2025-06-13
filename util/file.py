import os.path
import config


def _getFile(path='', name=''):
  name = name.replace('\\', '/')
  f = os.path.join(path, name)
  return f


def getFile(dir_name='', name=''):
  name = str(name)
  path = os.path.join(config.botHome, dir_name)
  if '/' in name:
    p, name = os.path.split(name)
    path = os.path.join(path, p)
  if name == '':
    return path
  return _getFile(path, name)


def getResource(name=''):
  return getFile('resources/', name)


def getDataFile(name=''):
  path = getFile('data/')
  if not os.path.isdir(path):
    os.mkdir(path)
  return getFile('data/', name)


def getCache(name=''):
  path = getDataFile('cache/')
  if not os.path.isdir(path):
    os.mkdir(path)
  return getDataFile(os.path.join('cache/', str(name)))
