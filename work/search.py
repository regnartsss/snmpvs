from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql


class SearchFilial(StatesGroup):
    Filial = State()
    Kod = State()
    Serial = State()


async def search_name(message):
    await message.answer("Введите название филиала или наберите Нет для отмены")
    await SearchFilial.Filial.set()


async def search_name_win(message):
    rows = await sql.sql_select(f"SELECT * FROM data_full WHERE data_full.name_reg LIKE '%{message.text}%'")
    text = ""
    for row in rows:
        text += f"{row[1]} {row[0]}\n"
    return text


async def search_kod(message):
    await message.answer("Введите код филиала или наберите Нет для отмены")
    await SearchFilial.Kod.set()


async def search_kod_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT * FROM data_full WHERE kod = {message.text}")
        text = f"{row[1]} {row[0]}\n"
        return text
    except Exception as n:
        print(n)
        return "Ничего не найдено"


async def search_serial(message):
    await message.answer("Введите серийный номер или наберите Нет для отмены")
    await SearchFilial.Serial.set()


async def search_serial_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT kod, name FROM filial WHERE serial = '{message.text}'")
        text = f"{row[1]} {row[0]}\n"
        return text
    except TypeError:
        return "Ничего не найдено"
