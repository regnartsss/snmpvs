from aiogram import types
from loader import dp
from work.new_user import new_user
# from Users import search_user, db
# import sql


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await new_user(message)

