import random
import hashlib
import re
from typing import Union


markdown_escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
html_escape_chars = {
  '<': '&lt;', 
  '>': '&gt;', 
  '&': '&amp;'
}
widths = [
    (126,    1), (159,    0), (687,     1), (710,   0), (711,   1), 
    (727,    0), (733,    1), (879,     0), (1154,  1), (1161,  0), 
    (4347,   1), (4447,   2), (7467,    1), (7521,  0), (8369,  1), 
    (8426,   0), (9000,   1), (9002,    2), (11021, 1), (12350, 2), 
    (12351,  1), (12438,  2), (12442,   0), (19893, 2), (19967, 1),
    (55203,  2), (63743,  1), (64106,   2), (65039, 1), (65059, 0),
    (65131,  2), (65279,  1), (65376,   2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]


def multiple_replace(text, d):
  regex = re.compile('|'.join(map(re.escape, d)))
  return regex.sub(lambda i: d[i.group(0)], text)
  
def markdown_escape(text):
  return multiple_replace(text, {k: '\\' + k for k in markdown_escape_chars})
  
def markdown_unescape(text):
  return multiple_replace(text, {'\\' + k: k for k in markdown_escape_chars})


def html_escape(text):
  return multiple_replace(text, html_escape_chars)
  
def html_unescape(text):
  return multiple_replace(text, {v: k for k, v in dict(**html_escape_chars, **{'"': '&quot;'}).items()})

def get_escape_func(parse_mode: str):
  if parse_mode.__class__.__name__ == 'module':
    if parse_mode.__name__ == 'telethon.extensions.markdown':
      parse_mode = 'markdown'
    elif parse_mode.__name__ == 'telethon.extensions.html':
      parse_mode = 'html'
  if not isinstance(parse_mode, str):
    raise ValueError('Unknown parse_mode')
  return {
    'md': markdown_escape,
    'markdown': markdown_escape,
    'htm': html_escape,
    'html': html_escape
  }[parse_mode.lower()]
  
def get_unescape_func(parse_mode):
  return {
    'md': markdown_unescape,
    'markdown': markdown_unescape,
    'htm': html_unescape,
    'html': html_unescape
  }[parse_mode.lower()]
  
escape_makedown = markdown_escape 
unescape_makedown = markdown_unescape
escape_html = html_escape
unescape_html = html_unescape

  
def randStr(length: int = 8) -> str:
    """
    随机字符串

    Args:
        length: 字符串长度, 默认为 8

    Returns:
        str: 字符串
    """
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    res = ""
    for i in range(length):
        res += random.choice(chars)
    return res


def md5sum(
    string: Union[str, bytes] = None, byte: bytes = None, file_path: str = None
) -> str:
    """
    计算字符串或文件的 md5 值

    Args:
        string: 字符串（三选一）
        byte: bytes（三选一）
        file_path: 文件路径（三选一）

    Returns:
        str: md5
    """
    if string:
        if isinstance(string, bytes):
            return hashlib.md5(string).hexdigest()
        return hashlib.md5(string.encode()).hexdigest()
    if byte:
        return hashlib.md5(byte).hexdigest()
    if file_path:
        with open(file_path, "rb") as fp:
            data = fp.read()
        return hashlib.md5(data).hexdigest()
    return ""
    
    
def get_width(o: int) -> int:
    """Return the screen column width for unicode ordinal o."""
    global widths
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1
    
    
def width(s: str) -> int:
  res = 0
  for i in s:
    res += get_width(ord(i))
  return res
  