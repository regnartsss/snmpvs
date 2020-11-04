from loader import dp
from aiogram import executor


if __name__ == '__main__':
    import handlers
    executor.start_polling(dp, skip_updates=False)



