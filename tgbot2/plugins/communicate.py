from telethon import events, types, utils
from telethon.custom import Button

import config 
from util import logger
from plugin import handler


bot = config.bot


@bot.on(events.NewMessage)
async def _(event):
  message = event.message 
  if config.echo_chat_id == 0:
    return
  
  peer_id = utils.get_peer_id(event.message.peer_id)
  chat = await config.bot.get_entity(event.message.peer_id)
  name = getattr(chat, 'first_name', '') 
  
  reply_message = await event.message.get_reply_message()
  if t := getattr(chat, 'last_name', ''):
    name += ' ' + t
    
  reply_to = None
  if peer_id != config.echo_chat_id:
    buttons = [
      [Button.url(name, url=f"tg://user?id={chat.id}")],
      [Button.inline('data', message.id.to_bytes(5, 'big'))],
    ]
    if reply_message and reply_message.buttons:
      reply_to = int.from_bytes(reply_message.buttons[0][0].data, 'big')
    
    return await bot.send_message(
      config.echo_chat_id,
      message, 
      buttons=buttons,
      reply_to=reply_to,
    )
  
  if reply_message and reply_message.buttons:
    if len(reply_message.buttons) > 1:
      reply_to = int.from_bytes(reply_message.buttons[1][0].data, 'big')
    await bot.send_message(
      int(reply_message.buttons[0][0].url.replace('tg://user?id=', '')),
      message,
      buttons=Button.inline('data', message.id.to_bytes(5, 'big')),
      reply_to=reply_to,
    )