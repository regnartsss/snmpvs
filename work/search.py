from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql


class SearchFilial(StatesGroup):
    Filial = State()
    Kod = State()
    Serial = State()


async def search_name_win(message):
    rows = await sql.sql_select(f"SELECT * FROM data_full WHERE data_full.name_reg LIKE '%{message.text}%'")
    text = ""
    for row in rows:
        text += f"{row[1]} {row[0]}\n"
    return text


async def search_kod_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT * FROM data_full WHERE kod = {message.text}")
        text = f"{row[1]} {row[0]}\n"
        return text
    except Exception as n:
        print(n)
        return "Ничего не найдено"


async def search_serial_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT kod, name FROM zabbix WHERE serial = '{message.text}'")
        text = f"{row[1]} {row[0]}\n"
        return text
    except TypeError:
        return "Ничего не найдено"
