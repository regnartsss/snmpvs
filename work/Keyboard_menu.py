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
        print(call.data)
        rows = await sql.sql_select(f"SELECT name, kod FROM filial WHERE region = {call.data.split('_')[1]} ORDER BY name")
        for row in rows:
            keyboard.row(InlineKeyboardButton(text=f"{row[1]} {row[0]}", callback_data=f"filial_{row[1]}_{call.data.split('_')[1]}"))
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data="menu"))
        return keyboard
    elif call.data.split("_")[0] == "filial":
        print("Филиал")
        print(call.data)
        text = await info_filial(call.data.split("_")[1])
        keyboard.row(InlineKeyboardButton(text="ssh", callback_data=f"ssh_{call.data}"))
        keyboard.row(InlineKeyboardButton(text="Обновить информацию", callback_data=f"check_{call.data.split('_')[1]}"))
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data=f"region_{call.data.split('_')[2]}"))
        return text, keyboard

async def ssh(call):
    keyboard = InlineKeyboardMarkup()
    text = await info_filial(call.data.split("_")[2])
    # keyboard.row(InlineKeyboardButton(text="lease", callback_data=f"lease_{call.data.split('_')[2]}"))
    keyboard.row(InlineKeyboardButton(text="ssh_console", callback_data=f"console_{call.data.split('_')[2]}"))
    keyboard.row(InlineKeyboardButton(text="traceroute vrf 100 10.10.33.5", callback_data=f"ssh_trac_{call.data.split('_')[2]}"))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=f"filial_{call.data.split('_')[2]}_{call.data.split('_')[3]}"))
    return text, keyboard


# async def lease(call):
#     kod = call.data.split("_")[1]
#     keyboard = InlineKeyboardMarkup()
#     LAN = InlineKeyboardButton(text="LAN", callback_data=f"lease_{kod}_LAN")
#     CAM = InlineKeyboardButton(text="CAM", callback_data=f"lease_{kod}_CAM")
#     SC = InlineKeyboardButton(text="SC", callback_data=f"lease_{kod}_SC")
#     KIOSK = InlineKeyboardButton(text="Kiosk", callback_data=f"lease_{kod}_KIOSK")
#     keyboard.row(LAN, CAM, SC, KIOSK)
#     keyboard.row(InlineKeyboardButton(text="ssh", callback_data="ssh_%s" % kod))
#     keyboard.row(InlineKeyboardButton(text="Назад", callback_data="region_%s" % dat[kod]["region"]))
#     return keyboard

async def key_registrator(message):
    keyboard = InlineKeyboardMarkup()
    rows = await sql.sql_select("SELECT id, name FROM region")
    for row in rows:
        keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=f"registrator_{row[0]}"))
    return keyboard



