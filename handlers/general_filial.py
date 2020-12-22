from loader import dp, bot
from filters.loc import region_cb, send_lease_cb, filials_cb, region_registr_cb
from aiogram.utils.exceptions import MessageNotModified
from aiogram import types
from work.Keyboard_menu import key_registrator, menu_region, menu_filials, menu_filial
from work.sql import sql_insert
from work.Statistics import info_filial, check_registrator, link, version_po
from work.Statistics import info_registrator, info_filial
from work.keyboard import main_menu


@dp.message_handler(text="Филиалы")
async def menu(message: types.Message):
    await message.answer("null", reply_markup=main_menu())
    await message.answer("Выберите регион", reply_markup=await menu_region())


@dp.callback_query_handler(region_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    try:
        await call.message.edit_text(text="Выберите филиал", reply_markup=await menu_filials(callback_data))
    except MessageNotModified:
        pass


@dp.callback_query_handler(filials_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    kod = callback_data["kod"]
    text = await info_filial(kod)
    keyboard = await menu_filial(callback_data)
    await sql_insert(f"UPDATE users SET ssh_kod = {kod} WHERE user_id = {call.from_user.id}")

    await call.message.edit_text(text=text, reply_markup=keyboard)


@dp.callback_query_handler(region_registr_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    region = callback_data['num']
    await call.message.edit_text(await info_registrator(region))
