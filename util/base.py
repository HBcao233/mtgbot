import json
import os
import config


global_config_path = os.path.join(config.botRoot, 'global.json')
default_global_config = {
  'blacklist': [
    5474729952, 
    6281740603,
    6740189676, 
    6745892379,
    7141954098,
    7199611144,
    7388945927,
    8154067875,
    8246313729,
    8216294019,
    8329070515,
  ],
}

def get_global_config():
  if not os.path.isfile(global_config_path):
    with open(os.path.join(config.botRoot, 'global.json'), 'w') as f:
      json.dump(default_global_config, f, indent=2, ensure_ascii=False)
    return default_global_config

  with open(global_config_path) as f:
    content = f.read()
  try:
    return json.loads(content)
  except json.JSONDecodeError:
    logger.exception('global配置解析失败')
    return default_global_config
  

def get_blacklist():
  """
  获取黑名单
  """
  global_config = get_global_config()
  if global_config.get('blacklist', []):
    return global_config['blacklist']
  return default_global_config['blacklist']
