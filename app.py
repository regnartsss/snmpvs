from loader import dp
from aiogram import executor
import handlers
import middlewares


if __name__ == '__main__':
    middlewares.setup(dp)
    executor.start_polling(dp, skip_updates=True)



