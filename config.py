import os


default_api_id = '4'
default_api_hash = '014b35b6184100b085b0d0572f9b5103'

botRoot = workPath = os.path.dirname(os.path.realpath(__file__))
commands = []
inlines = []
settings = []


env = os.environ
bot_home = x if (x := env.get('BOT_HOME', '')) != '.' else ''
if bot_home:
  botRoot = os.path.join(workPath, bot_home)

token = env.get('token')
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
proxies = {}
proxy_type = env.get('proxy_type', '') or 'http'
if (proxy_port := env.get('proxy_port', '')) != '':
  proxy_host = 'localhost'
  if env.get('proxy_host', '') != '':
    proxy_host = env.get('proxy_host')
  proxy_url = f'{proxy_type}://{proxy_host}:{proxy_port}/'

  proxy_username = env.get('proxy_username', '')
  proxy_password = env.get('proxy_password', '')
  if proxy_username and proxy_password:
    proxy_url = (
      f'{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}'
    )

if proxy_url is not None:
  proxies.update({'http://': proxy_url, 'https://': proxy_url})
  proxy = (proxy_type, proxy_host, proxy_port, True, proxy_username, proxy_password)
