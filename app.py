from aiogram import executor
from loader import dp, bot
from work.check_vs import thread_check
from asgiref.sync import sync_to_async
import asyncio
import handlers
import concurrent.futures
import time




#
async def on_startup(dp):
    # print("tt")
    # await thread_check()
    # loop = asyncio.get_event_loop()
    # # asyncio.ensure_future(start())
    # loop.run_until_complete(thread_check())
    # loop.run_forever()
    await bot.send_message(765333440, "Бот запущен")
#     loop = asyncio.get_event_loop()
#     asyncio.ensure_future(start())
#     asyncio.ensure_future(thread_check())
#     loop.run_forever()

def startbot():
    if __name__ == '__main__':
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)



loop = asyncio.get_event_loop()
asyncio.ensure_future(thread_check())
asyncio.ensure_future(startbot())
loop.run_forever()


