from telethon import types, utils
import sys
import os.path


default_api_id = '4'
default_api_hash = '014b35b6184100b085b0d0572f9b5103'


class Config:
  botRoot = workPath = os.path.dirname(os.path.realpath(__file__))
  commands = []
  def __init__(self):
    self.env = os.environ
    self.bot_home = x if (x := self.env.get('BOT_HOME', '')) != '.' else ''
    if self.bot_home:
      self.botRoot = os.path.join(self.workPath, self.bot_home)
    
    self.token = self.env.get('token')
    self.api_id = self.env.get('api_id', '') or self.env.get('app_id', '') or default_api_id
    self.api_hash = self.env.get('api_hash', '') or self.env.get('app_hash', '') or default_api_hash
    self.debug = False
    if self.env.get('debug', '') in ['true', 'T', '1', 'True', 'debug']:
      self.debug = True
    
    self.echo_chat_id = int(x) if (x := self.env.get('echo_chat_id', '')) else 0
    self.superadmin = [int(x) for x in self.env.get('superadmin', '').split(',') if x]
    
    self.telegraph_author_name = self.env.get('telegraph_author_name', '')
    self.telegraph_author_url = self.env.get('telegraph_author_url', '')
    self.telegraph_access_token = self.env.get('telegraph_access_token', '')
    
    self.proxy_url = None
    self.proxies = {}
    if (port := self.env.get('proxy_port', '')) != '':
      host = 'localhost'
      if self.env.get('proxy_host', '') != '':
        host = self.env.get('proxy_host', '')
      self.proxy_url = f'http://{host}:{port}/'
    
      proxy_user = self.env.get('proxy_user', '')
      proxy_pass = self.env.get('proxy_pass', '')
      if proxy_user and proxy_pass:
        self.proxy_url = f'http://{proxy_user}:{proxy_pass}@{host}:{port}'
          
    if self.proxy_url is not None:
      self.proxies.update({
        "http://": self.proxy_url,
        "https://": self.proxy_url
      })
    
sys.modules[__name__] = Config()
