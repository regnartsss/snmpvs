from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from work import sql
from work.Statistics import info_filial
from filters.loc import send_lease_cb, region_cb, filials_cb, ssh_cb, lease_cb, console_ssh_cb, update_cb, region_registr_cb, console_input_cb
from work.sql import sql_selectone

async def menu_region():
    keyboard = InlineKeyboardMarkup()
    rows = await sql.sql_select("SELECT id, name FROM zb_region ORDER BY name")
    for id, name in rows:
        keyboard.row(InlineKeyboardButton(text=f"{name}", callback_data=region_cb.new(num=id)))
    return keyboard


async def menu_filials(callback_data):
    region = callback_data["num"]
    # print("ddd")
    keyboard = InlineKeyboardMarkup(row_width=2)
    rows = await sql.sql_select(f"SELECT name, kod FROM zabbix WHERE region = {region} ORDER BY name")
    for name, kod in rows:
        if kod is not None:
            # keyboard.insert(
            #     InlineKeyboardButton(text=f"{kod} {name}", callback_data=filials_cb.new(region=region, kod=kod)))
            keyboard.insert(
                InlineKeyboardButton(text=f"{name}", callback_data=filials_cb.new(region=region, kod=kod)))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="menu"))
    return keyboard


async def menu_filial(callback_data):
        keyboard = InlineKeyboardMarkup()
        kod = callback_data["kod"]
        region= callback_data["region"]
        LAN = InlineKeyboardButton(text="LAN", callback_data=lease_cb.new(data="vlan100", kod=kod, region=region))
        CAM = InlineKeyboardButton(text="CAM", callback_data=lease_cb.new(data="vlan400", kod=kod, region=region))
        SC = InlineKeyboardButton(text="SC", callback_data=lease_cb.new(data="vlan500", kod=kod, region=region))
        keyboard.row(LAN, CAM, SC)
        keyboard.row(InlineKeyboardButton(text="ssh", callback_data=ssh_cb.new(kod=kod, region=region)))
        keyboard.row(InlineKeyboardButton(text="Обновить информацию", callback_data=update_cb.new(data="update", kod=kod, region=region)))
        keyboard.row(InlineKeyboardButton(text="Отключить проверку", callback_data=update_cb.new(data="close", kod=kod, region=region)))
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data=region_cb.new(num=region)))
        return keyboard


async def check_filial(callback_data):
    keyboard = InlineKeyboardMarkup()
    kod = callback_data["kod"]
    region = callback_data["region"]
    keyboard.row(InlineKeyboardButton(text="Обновить провайдеров", callback_data=update_cb.new(data="gateway", kod=kod, region=region)))
    keyboard.row(InlineKeyboardButton(text="Найти рег и циско", callback_data=update_cb.new(data="reg_cis", kod=kod, region=region)))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=filials_cb.new(region=region, kod=kod)))
    return keyboard


async def ssh(callback_data):
    kod = callback_data["kod"]
    try:
        region = callback_data["region"]
    except KeyError:
        region = (await sql_selectone(f"SELECT region FROM zabbix WHERE kod = {kod}"))[0]
    keyboard = InlineKeyboardMarkup()
    # keyboard.row(InlineKeyboardButton(text="ssh_console", callback_data=console_ssh_cb.new(kod=kod)))
    keyboard.row(InlineKeyboardButton(text="sh ip int br", callback_data=console_input_cb.new(kod=kod, command="sh ip int br")))
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
    rows = await sql.sql_select("SELECT id, name FROM zb_region ORDER BY zb_region.name")
    for row in rows:
        keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=region_registr_cb.new(num=row[0])))
    return keyboard



