from bs4 import BeautifulSoup
import asyncio
import re 
import ujson as json
import traceback

import util
import config
from util import logger
from util.telegraph import createPage, getPageList


env = config.env
ipb_member_id = env.get('ex_ipb_member_id', '')
ipb_pass_hash = env.get('ex_ipb_pass_hash', '')
igneous = env.get('ex_igneous', '')
headers = {
  'cookie': f'ipb_member_id={ipb_member_id};ipb_pass_hash={ipb_pass_hash};igneous={igneous}',
}

def parseEidSMsg(eid, _html):
    '''
    格式化e站s单页 msg
    '''
    soup = BeautifulSoup(_html, "html.parser")
    name = soup.select("#i1 h1")[0].string
    url = soup.select("#i3 img")[0].attrs["src"]
    sn = soup.select("#i2 .sn div")[0].text

    prev = soup.select("#i2 #prev")[0].attrs["href"]
    next = soup.select("#i2 #next")[0].attrs["href"]
    source = soup.select("#i6 a")[2].attrs["href"]
    parent = soup.select("#i5 a")[0].attrs["href"]
    return (
        f"\n<code>{name}</code>\n"
        f"{sn}\n"
        f"前：{prev}\n"
        f"后：{next}\n"
        f"原图：{source}\n"
        f"画廊：{parent}"
        f"\n\n{eid}",
        url
    )


async def parseEidGMsg(eid, soup):
    '''
    格式化e站g画廊 msg
    '''
    title = soup.select("#gd2 #gj")[0].string
    num = soup.select("#gdd tr")[5].select(".gdt2")[
        0].text.replace(" pages", "")
    if not title:
      title = soup.select("#gd2 #gn")[0].string

    url = soup.select("#gd5 p")[2].a.attrs["onclick"].split("'")[1]
    r = await util.get(url, headers=headers)
    html = r.text
    soup2 = BeautifulSoup(html, "html.parser")

    magnets = []
    for i in soup2.select("table a"):
        torrent = i.attrs["href"]
        if torrent:
            match = re.search(r"(?<=/)([0-9a-f]{40})(?=.torrent)", torrent)
            if match:
                magnet = "magnet:?xt=urn:btih:" + str(match.group())
                magnets.append(magnet)
        
    return title, num, magnets 
    
    
async def parsePage(text, soup, title, num, nocache=False, bar=None):
  num = int(num)
  if not nocache:
    for i in await getPageList():
      if i['title'] == title:
        return i['url']
  
  urls = []
  for i in soup.select("#gdt a"):
    urls.append(i.attrs["href"])
    
  p = 1
  while len(urls) < min(num, 100):
    try:
      r = await util.get(text, params={'p': p}, headers=headers)
      html1 = r.text
      soup1 = BeautifulSoup(html1, "html.parser")
      arr = soup1.select("#gdt a")
      for i in arr:
        urls.append(i.attrs["href"])
    except Exception:
      logger.warning('未能成功获取所有p')
      break
    p += 1
  
  async def parse(u):
    nonlocal bar, urls, data
    if not (url := data.get(u)) or nocache:
      r = await util.get(u, headers=headers)
      html1 = r.text
      soup1 = BeautifulSoup(html1, "html.parser")
      try:
        url = soup1.select("#i3 img")[0].attrs["src"]
      except:
        logger.warning(f'[{urls.find(u)}] {u} 获取失败')
        logger.warning(traceback.format_exc())
        return None
      try:
        try:
          r0 = await util.get(url, 
            headers=headers.update({'referer': text}))
        except:
          r0 = await util.get(url, 
            headers=headers.update({'referer': text}))
        r = await util.post(
          'https://telegra.ph/upload',
          files={
            'file': r0.content
          }
        )
        url0 = r.json()[0]['src']
      except:
        logger.warning(f'[{urls.index(u)}] {u} 获取失败')
        logger.warning(traceback.format_exc())
      else:
        url = url0
        data[u] = url
    
    if bar is not None:
      await bar.add(100//len(urls))
    return {
      'tag': 'img',
      'attrs': {
        'src': url,
      },
    }
    
  content = []
  data = util.Data('urls')
  tasks = [parse(i) for i in urls]
  for i in await asyncio.gather(*tasks):
    if i is not None:
      content.append(i)
  data.save()
  
  return await createPage(title, content)
  