import os
import sys
from typing import TYPE_CHECKING
from dotenv import load_dotenv

if TYPE_CHECKING:
  from plugin import Command, InlineCommand, Setting
  from bot import Bot


default_api_id = '4'
default_api_hash = '014b35b6184100b085b0d0572f9b5103'

#: Bot 实例
#:
#: :meta hide-value:
bot: 'Bot'

#: mtgbot 根目录
#:
#: :meta hide-value:
botRoot: str = os.path.dirname(os.path.realpath(__file__))

#: bot 私有目录 (.env所在目录)
#:
#: :meta hide-value:
botHome: str = botRoot

#: 加载的 Commands
commands: list['Command'] = []
#: 加载的 InlineCommands
inlines: list['InlineCommand'] = []
#: 加载的 Settings
settings: list['Setting'] = []

#: 当前环境变量 (.env导入的变量)
#:
#: :meta hide-value:
env: dict = os.environ

#: bot文件夹名
#:
#: :meta hide-value:
bot_home: str = env.get('BOT_HOME', '')
bot_home = sys.argv[1] if len(sys.argv) > 1 else bot_home
if bot_home:
  botHome = os.path.join(botRoot, bot_home)

env_path = os.path.join(botHome, '.env')
load_dotenv(dotenv_path=env_path, verbose=True)
env = os.environ

token = env.get('token') or ''
api_id = env.get('api_id', '') or env.get('app_id', '') or default_api_id
api_hash = env.get('api_hash', '') or env.get('app_hash', '') or default_api_hash
debug = False
if env.get('debug', '') in ['true', 'T', '1', 'True', 'debug']:
  debug = True

#: 超级管理员列表
superadmin = [int(x) for x in env.get('superadmin', '').split(',') if x]

telegraph_author_name = env.get('telegraph_author_name', '')
telegraph_author_url = env.get('telegraph_author_url', '')
telegraph_access_token = env.get('telegraph_access_token', '')

#: 代理链接
proxy_url: str = None
#: Telethon格式代理
proxy: dict = None
proxy_type = env.get('proxy_type', '') or 'http'
if (proxy_port := env.get('proxy_port', '')) != '':
  proxy_port = int(proxy_port)
  proxy_host = 'localhost'
  if env.get('proxy_host', '') != '':
    proxy_host = env.get('proxy_host')
  proxy_url = f'{proxy_type}://{proxy_host}:{proxy_port}/'
  proxy = {
    'proxy_type': proxy_type,  # (mandatory) protocol to use (see above)
    'addr': proxy_host,  # (mandatory) proxy IP address
    'port': proxy_port,  # (mandatory) proxy port number
    'rdns': False,  # (optional) whether to use remote or local resolve
  }

  proxy_username = env.get('proxy_username', '')
  proxy_password = env.get('proxy_password', '')
  if proxy_username and proxy_password:
    proxy_url = (
      f'{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}'
    )
    proxy.update(
      {
        'username': proxy_username,
        'password': proxy_password,
      }
    )
