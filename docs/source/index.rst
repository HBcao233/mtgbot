.. mtgbot documentation master file, created by
   sphinx-quickstart on Fri Oct  4 16:56:58 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mtgbot documentation
====================

.. code-block:: python
   :linenos:

   @handler(
      'ping',
      pattern=_pattern,
      info='/ping ping! pong!',
      filter=filters.PRIVATE | filters.Command('ping'),
   )
   async def ping(event, text):
      await event.reply('pong!')


.. include:: catalogue.rst