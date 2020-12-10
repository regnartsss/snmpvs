from filters.loc import ssh_cb, console_ssh_cb,  console_ssh_cb, console_input_cb
from loader import dp
from aiogram import types
from work.Keyboard_menu import ssh
from work.Ssh import ssh_console
from aiogram.dispatcher.filters.state import State, StatesGroup
from work.keyboard import cancel
from aiogram.dispatcher import FSMContext
from work.Ssh import ssh_console, Ssh_console, console_command, search_mac
from aiogram.utils.exceptions import MessageTextIsEmpty


@dp.callback_query_handler(ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_reply_markup(reply_markup=await ssh(callback_data))


@dp.callback_query_handler(console_ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    kod = callback_data['kod']
    await Ssh_console.command.set()
    await call.message.answer(text=await ssh_console(kod, call.from_user.id), reply_markup=cancel())
    # async with state.proxy() as data:
    #     data['kod'] = callback_data['kod']


@dp.callback_query_handler(console_input_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    kod = callback_data['kod']
    command = callback_data['command']
    print(kod, command)
    await call.message.edit_text(text=await console_command(kod, command, call.from_user.id), reply_markup=await ssh(callback_data))


@dp.message_handler(state=Ssh_console.command, text = "🚫 Отмена")
async def process_name(message: types.Message, state: FSMContext):
    await message.answer(text="🚫 Отмена")
    await state.finish()


# @dp.message_handler(state=Ssh_console.command)
# async def process_name(message: types.Message, state: FSMContext, callback_data: dict):
#     kod = callback_data['kod']
#     await message.answer(await console_command(message, kod))
