from aiogram import types
from loader import dp
from work.new_user import new_user
from work.admin import message_all
from work.keyboard import cancel, main_menu_user, main_menu
# rom work.Ssh import arp
from data.data import admin_id


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await new_user(message)


@dp.message_handler(commands=['id'])
async def start_message(message: types.Message):
    await message.answer(text=f"id: {message.from_user.id}")


@dp.message_handler(lambda c: c.from_user.id in admin_id, commands=['button'])
async def start_message(message: types.Message):
    await message.answer(text="Кнопки", reply_markup=main_menu())


@dp.message_handler(commands=['button'])
async def start_message(message: types.Message):
    await message.answer(text="Кнопки", reply_markup=main_menu_user())


@dp.message_handler(commands=['message'])
async def message(message: types.Message):
    await message.answer(text=await message_all(), reply_markup=cancel())


# @dp.message_handler(commands=['arp'])
# async def message(message: types.Message):
#     await arp()