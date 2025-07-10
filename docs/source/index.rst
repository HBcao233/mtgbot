
Mtgbot 文档
======

.. code-block:: python
  :linenos:

  @handler(
    'hello',
    info='Hello World!',
  )
  async def _hello(event):
    await event.reply('Hello World!')

- 第一次使用? 跳转 :ref:`installation`
- 需要 Telethon 文档? https://docs.telethon.dev/
- Telethon Bot 对比 HTTP Bot Api 的优势? 见 `HTTP Bot API vs MTProto <https://docs.telethon.dev/en/stable/concepts/botapi-vs-mtproto.html#botapi>`_

这是什么?
------

mtgbot 是一个基于 `Telethon <https://github.com/LonamiWebs/Telethon>`_ 的、轻量化的 Telegram 机器人框架。 致力于用最简单的方式开发复杂机器人

是否厌倦了繁文缛节的 Nonebot 2, 是否看不惯反人类的依赖注入机制, 来试试轻量化的机器人框架 Mtgbot 吧

.. toctree::
  :maxdepth: 4
  :caption: 第一步
  :hidden:
  
  self

.. include:: modules.rst