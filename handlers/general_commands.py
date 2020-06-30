from aiogram import types
from loader import dp
from work.new_user import new_user
from work.admin import message_all
from work.keyboard import cancel, main_menu_user


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await new_user(message)


@dp.message_handler(commands=['button'])
async def start_message(message: types.Message):
    await message.answer(text="Кнопки", reply_markup=main_menu_user())


@dp.message_handler(commands=['message'])
async def message(message: types.Message):
    await message.answer(text=await message_all(), reply_markup=cancel())
