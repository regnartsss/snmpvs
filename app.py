from aiogram import executor
from loader import dp, bot
from work.check_vs import start_snmp
from work.check_registrator import start_check_registrator
# from asgiref.sync import sync_to_async
import asyncio
import handlers
import concurrent.futures
import time




#
async def on_startup(dp):
    import middlewares
    middlewares.setup(dp)
    await bot.send_message(765333440, "Бот запущен")
#     loop = asyncio.get_event_loop()
#     asyncio.ensure_future(start())
#     asyncio.ensure_future(thread_check())
#     loop.run_forever()
async def check():
    asyncio.ensure_future(start_snmp("ASC"))
    # asyncio.ensure_future(start_snmp("DESC"))
    # asyncio.ensure_future(start_snmp())
    asyncio.ensure_future(start_check_registrator())

def startbot():
    if __name__ == '__main__':
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


# loop = asyncio.get_event_loop()
asyncio.ensure_future(check())
asyncio.ensure_future(startbot())
# loop.run_forever()


