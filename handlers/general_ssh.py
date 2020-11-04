from filters.loc import ssh_cb, console_ssh_cb,  console_ssh_cb
from loader import dp
from aiogram import types
from work.Keyboard_menu import ssh
from work.Ssh import ssh_console
from aiogram.dispatcher.filters.state import State, StatesGroup
from work.keyboard import cancel
from aiogram.dispatcher import FSMContext
from work.Ssh import ssh_console, Ssh_console, ssh_console_command, search_mac



@dp.callback_query_handler(ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_reply_markup(reply_markup=await ssh(callback_data))


@dp.callback_query_handler(console_ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.answer(text=await ssh_console(callback_data, call.from_user.id), reply_markup=cancel())
    async with state.proxy() as data:
        data['kod'] = callback_data['kod']



@dp.message_handler(state=Ssh_console.command)
async def process_name(message: types.Message, state: FSMContext):
    text = await ssh_console_command(message, state)
    await message.answer(text=text)