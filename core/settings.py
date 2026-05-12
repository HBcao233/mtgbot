import ast
from telethon import Button
import config
import filters
from plugin import Command, Scope


@Command(
  'settings',
  enable=(lambda: len(config.settings) > 0),
  info='设置',
  scope=Scope.private(),
  filter=filters.PRIVATE,
)
async def _settings(event):
  """
  机器人设置命令

  :meta public:
  """
  buttons = []
  index = 0
  for i in config.settings:
    if index == len(buttons):
      buttons.append([])
    buttons[index].append(Button.inline(i.text, i.data))
    if len(buttons[index]) == 2:
      index += 1

  buttons.append([Button.inline('关闭面板', data=b'delete')])
  caption = config.env.get('settings_caption', '')
  if caption:
    caption = ast.parse(r'"""' + caption + '"""').body[0].value.value
  else:
    caption = '设置小派魔的运行参数'
  await event.reply(
    caption,
    buttons=buttons,
  )
