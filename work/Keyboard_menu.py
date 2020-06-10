from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from work import sql
from work.Statistics import info_filial

async def work(message, call=""):
    keyboard = InlineKeyboardMarkup()
    if message.text == "Филиалы" or call.data.split("_")[0] == "menu":
        rows = await sql.sql_select("SELECT id, name FROM region")
        for row in rows:
            keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=f"region_{row[0]}"))
        return keyboard
    elif call.data.split("_")[0] == "region":
        rows = await sql.sql_select(f"SELECT name, kod FROM filial WHERE region = {call.data.split('_')[1]} ORDER BY name")
        for row in rows:
            keyboard.row(InlineKeyboardButton(text=f"{row[1]} {row[0]}", callback_data=f"filial_{row[1]}_{call.data.split('_')[1]}"))
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data="menu"))
        return keyboard
    elif call.data.split("_")[0] == "filial":
        text = await info_filial(call.data.split("_")[1])
        keyboard.row(
            InlineKeyboardButton(text="Назад", callback_data=f"region_{call.data.split('_')[2]}"))
        return text, keyboard



