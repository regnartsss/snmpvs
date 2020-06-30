from aiogram.dispatcher.filters.state import State, StatesGroup
from work.keyboard import main_menu
from loader import bot
from work.sql import sql_select

class AllMessage(StatesGroup):
    message = State()


async def message_all():
    await AllMessage.message.set()
    return "Введите сообщение"

async def send_mess(message):
    text = "Бот обновлен, внесены следующие изменения:\n"
    text += message.text
    text += "❓ По вопросам и предложениям обращаться сюда \n➡️ @regnartsss"
    rows = await sql_select("SELECT id FROM Users")
    for row in rows:
        try:
            await bot.send_message(chat_id=row[0], text=text, disable_notification=True)
        except:
            pass


async def mess(message, state):
    if message.text == "🚫 Отмена":
        await message.answer("🚫 Отмена", reply_markup=main_menu())
        await state.finish()
    else:
        await send_mess(message)
        await state.finish()
