import json
import os
import config
import re


ad_pattern = re.compile(r'优质交流群|群发器|免费|盗U|速进|粉商|号商|接码|盘口|拍卖群|收活跃群|收.*群管理|(有意向.*|有需求|详情|直接|定制.*)联系|供应商品|广招代理|一件发货|送卖号机器人|自助取号|(国际|放心)娱乐|美女直播|看片|(代f|红包).*(https|t.me|@)|会员广告|.*u包月|超低价|立即体验|降低成本|更省钱|老板专用|快.*进|就差你了|注册链接|新币|彩票软件|资金实力|(微信|支付宝)流水|(查看|永久)频道|公群上押|来领钱|送彩金|全网担保|回馈客户|(质量保证|担保.*|仿真.*|出售.*)假钞|假钞供货商|快来抢|我抢了.*多|咸鱼代发|无需押金|日赚几百|直登|永远不改价格|大降价|免手续费|送会员|诚招代理').search
global_config_path = os.path.join(config.botRoot, 'global.json')
default_blacklist = [
  5474729952, 
  6281740603,
  6740189676, 
  6745892379,
  7141954098,
  7199611144,
  7388945927,
  8154067875,
  8167288046,
  8246313729,
  8216294019,
  8329070515,
  6181496478,
  6190464815,
  6502418850,
  7089636897,
  7097461400,
  7840916442,
  8079028202,
  8096345848,
  7898202547,
  8409139212,
  2017299100,
  7867091719,
  8498930707,
  6691551279,
  7577886338,
  6054478306,
  6219383783,
  8018765011,
  2088168588,
  7864532507,
  6842316901,
  7648388149,
  6236830793,
  7334415627,
  1908800086,
  1421926746,
  5389428028, 
  7940034636,
  5765239934,
  7423318740,
  6439418807,
  5130826597, 
  8138391619,
  7231811771, 
  6433199111, 
  6133218327,
  7364453910,
  7539224448, 
  8148643087, 
  7513479583, 
  8140062776,
  7969307589,
  7864132652, 
  6688000767, 
  7390859469,
  5254268404, 
  7616401322, 
  5723404941, 
  5630082926,
  8115425450,
  6407629541,
  8448702383,
  7812881170,
  8425293289,
  1982334809,
  1982334809,
  8476401845,
  8510056537,
  8191147046,
  8228741629,
  8318348849,
  8444881868,
  8389850441,
  8365095566,
  6108014357,
]

def get_global_config():
  if not os.path.isfile(global_config_path):
    return {'blacklist': default_blacklist}

  with open(global_config_path) as f:
    content = f.read()
  try:
    res = json.loads(content)
  except json.JSONDecodeError:
    logger.exception('global配置解析失败')
    return {'blacklist': default_blacklist}

  if not isinstance(res.get('blacklist', None), list):
    res['blacklist'] = []
  res['blacklist'] = list(set(res['blacklist'] + default_blacklist))
  return res


def set_global_config(c):
  with open(global_config_path, 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)


def get_blacklist():
  """
  获取黑名单
  """
  c = get_global_config()
  if c.get('blacklist', None):
    return c['blacklist']
  return default_blacklist
