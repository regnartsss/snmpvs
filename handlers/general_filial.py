from loader import dp, bot
from filters.loc import region_cb, send_lease_cb, filials_cb
from aiogram.utils.exceptions import MessageNotModified
from aiogram import types
from work.Keyboard_menu import key_registrator, menu_region, menu_filials, menu_filial
from work.sql import sql_insert
from work.Statistics import info_filial, check_registrator, link, version_po


@dp.message_handler(text="Филиалы")
async def menu(message: types.Message):
    await message.answer("Выберите регион", reply_markup=await menu_region())


@dp.callback_query_handler(region_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    print("ddd")
    print(callback_data)
    try:
        await call.message.edit_text(text="Выберите филиал", reply_markup=await menu_filials(callback_data))
    except MessageNotModified:
        pass


@dp.callback_query_handler(filials_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    # print(callback_data)
    kod = callback_data["kod"]
    # await sql_insert(f"UPDATE users SET ssh_kod = {kod} WHERE id = {call.from_user.id}")
    text = await info_filial(kod)
    keyboard = await menu_filial(callback_data)
    await call.message.edit_text(text=text, reply_markup=keyboard)