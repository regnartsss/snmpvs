from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from work import sql
from work.Statistics import info_filial
from filters.loc import send_lease_cb, region_cb, filials_cb, ssh_cb, lease_cb, console_ssh_cb


async def menu_region():
    keyboard = InlineKeyboardMarkup()
    rows = await sql.sql_select("SELECT id, name FROM region")
    for row in rows:
        keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=region_cb.new(num=row[0])))
    return keyboard


async def menu_filials(callback_data):
    region = callback_data["num"]
    print("ddd")
    keyboard = InlineKeyboardMarkup(row_width=2)
    rows = await sql.sql_select(f"SELECT name, kod FROM filial WHERE region = {region} ORDER BY name")
    for row in rows:

        keyboard.insert(
            InlineKeyboardButton(text=f"{row[1]} {row[0]}", callback_data=filials_cb.new(region=region, kod=row[1])))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="menu"))
    return keyboard


async def menu_filial(callback_data):
        keyboard = InlineKeyboardMarkup()
        print("Филиал")
        kod = callback_data["kod"]
        region= callback_data["region"]
        LAN = InlineKeyboardButton(text="LAN", callback_data=lease_cb.new(data="vlan100", kod=kod, region=region))
        CAM = InlineKeyboardButton(text="CAM", callback_data=lease_cb.new(data="vlan400", kod=kod, region=region))
        SC = InlineKeyboardButton(text="SC", callback_data=lease_cb.new(data="vlan500", kod=kod, region=region))
        keyboard.row(LAN, CAM, SC)
        keyboard.row(InlineKeyboardButton(text="ssh", callback_data=ssh_cb.new(kod=kod, region=region)))
        keyboard.row(InlineKeyboardButton(text="Обновить информацию", callback_data=f"check_{kod}"))
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data=region_cb.new(num=region)))
        return keyboard


async def ssh(callback_data):
    print(callback_data)
    region = callback_data["region"]
    kod = callback_data["kod"]
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text="ssh_console", callback_data=console_ssh_cb.new(kod=kod)))
    # keyboard.row(InlineKeyboardButton(text="traceroute vrf 100 10.10.33.5", callback_data=f"ssh_trac_{call.data.split('_')[2]}"))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=filials_cb.new(region=region, kod=kod)))
    return keyboard



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


async def key_registrator():
    keyboard = InlineKeyboardMarkup()
    rows = await sql.sql_select("SELECT id, name FROM region")
    for row in rows:
        keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=f"registrator_{row[0]}"))
    return keyboard



