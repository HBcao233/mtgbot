import os
import sys
from typing import TYPE_CHECKING
from dotenv import load_dotenv

if TYPE_CHECKING:
  from plugin import Command, InlineCommand, Setting


default_api_id = '4'
default_api_hash = '014b35b6184100b085b0d0572f9b5103'

botRoot = botHome = os.path.dirname(os.path.realpath(__file__))
commands: list['Command'] = []
inlines: list['InlineCommand'] = []
settings: list['Setting'] = []


env = os.environ

bot_home = env.get('BOT_HOME', '')
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

echo_chat_id = int(x) if (x := env.get('echo_chat_id', '')) else 0
superadmin = [int(x) for x in env.get('superadmin', '').split(',') if x]

telegraph_author_name = env.get('telegraph_author_name', '')
telegraph_author_url = env.get('telegraph_author_url', '')
telegraph_access_token = env.get('telegraph_access_token', '')

proxy_url = proxy = None
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
