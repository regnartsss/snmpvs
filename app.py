from work.check_vs import start_snmp
from work.check_registrator import start_check_registrator
from loader import dp


async def on_startup(dp):
    import asyncio
    import middlewares
    middlewares.setup(dp)
    # await bot.send_message(765333440, "Бот запущен")
    asyncio.ensure_future(start_snmp())
    asyncio.ensure_future(start_check_registrator("ASC"))
    # asyncio.ensure_future(start_check_registrator("DESC"))


if __name__ == '__main__':
    from aiogram import executor
    import handlers
    # from handlers import dp
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


