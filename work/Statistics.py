from work.sql import sql_selectone, sql_select
import aiosnmp
from aiogram import types
from loader import bot


async def info_filial(kod):
    request = f"SELECT * FROM zabbix INNER JOIN zb_region ON zabbix.region = zb_region.id WHERE kod = {kod}"
    row = await sql_selectone(request)
    text = f"""
{await sdwan_mikrotik(row[17])}
{row[2]}
Код филиала: {kod}
Регион: {row[19]}
hostname: {row[4]}
loopback: {row[1]}
IP_LAN: {row[7]}
IP_Kiosk: {row[8]}
IP_CAM: {row[10]}
IP_SC: {row[11]}
ISP1_name: {row[12]}
ISP1: {row[5]}
gateway_isp1: {row[14]}
ISP2_name: {row[13]}
ISP2: {row[6]}
gateway_isp2: {row[15]}
serial: {row[16]}
cisco: {await cisco(kod)}
регистратор: {await registrator(kod)}
"""
    return text


async def cisco(kod):
    request = f"SELECT * FROM cisco WHERE kod = {kod}"
    rows = await sql_select(request)
    text = ""
    for row in rows:
        print(row)
        text += f"\n{row[1]} {row[2]}"
    return text

async def registrator(kod):
    request = f"SELECT * FROM registrator WHERE kod = {kod}"
    rows = await sql_select(request)
    text = ""
    for row in rows:
        text += f"\n{row[1]} {row[2]}"
    return text


async def sdwan_mikrotik(data):
    if data == 1:
        return "SDWAN"
    elif data == 0:
        return "Mikrotik"


async def info_registrator(call):
    region = call.data.split("_")[1]
    request=f"SELECT registrator.ip, registrator.hostname, filial.name, region.id, region.name FROM filial " \
            f"LEFT JOIN registrator, region " \
            f"ON region.id = filial.region and registrator.kod = filial.kod WHERE region.id = {region} ORDER BY registrator.hostname"
    rows = await sql_select(request)
    text = f"{(await sql_selectone(f'SELECT name FROM region WHERE id = {region}'))[0]}\n"
    for row in rows:
        text += f"{row[2]} {row[0]}\n"
    return text


async def version_po(message):
    text=""
    rows_old = await sql_select(f"SELECT ip, hostname, firmware FROM registrator")
    for row_old in rows_old:
        print(row_old)
        text += f"{row_old[2]} {row_old[1]} {row_old[0]}\n"
    while len(text) > 4000:
        await message.answer(text=text[:4000])
        text = text[4000:]
    return text


async def check_registrator(message):
    rows = await sql_select(f"SELECT kod FROM sub WHERE user_id = {message.from_user.id}")
    if len(rows) > 20:
        return "Слишком много филиалов для проверки"
    else:
        for row in rows:
            rows_old = await sql_select(f"SELECT ip FROM registrator WHERE kod = {row[0]}")
            for row_old in rows_old:
                print(row_old[0])
                mib = [
                    # '1.3.6.1.4.1.3333.1.1',  # db
                    '1.3.6.1.4.1.3333.1.2',  # archive
                    '1.3.6.1.4.1.3333.1.3',  # disk
                    # '1.3.6.1.4.1.3333.1.4',  # network
                    '1.3.6.1.4.1.3333.1.5',  # cameras
                    '1.3.6.1.4.1.3333.1.6',  # script
                    # '1.3.6.1.4.1.3333.1.7',  # name
                    '1.3.6.1.4.1.3333.1.8',  # cam_down
                    # '1.3.6.1.4.1.3333.1.9',  # ip address
                    '1.3.6.1.4.1.3333.1.10',  # firmware
                    '1.3.6.1.4.1.3333.1.11',  # up_time
                ]

                info = await info_snmp_registrator(row_old[0], mib)
                request = f"""SELECT filial.name, registrator.hostname, registrator.ip FROM filial LEFT JOIN registrator 
                ON filial.kod = registrator.kod WHERE registrator.ip = '{row_old[0]}'"""
                row = await sql_selectone(request)
                text = f"{row[0]}\n" \
                       f"💻 Сервер {row[1]}\n" \
                       f"💻 IP адрес {row[2]}\n" \
                       f"💽 Диски {info[1]}\n" \
                       f"📃 Глубина архива дней {info[0]}\n" \
                       f"🎥 Камеры {info[2]}\n" \
                       f"🔍 Не работает камера: {info[4]}\n" \
                       f"   Прошивка: {info[5]}\n" \
                       f"⌛  Время работы сервера  {info[6]}\n"
                await message.answer(text)
        return "Проверка закончена"



async def info_snmp_registrator(ip, mib_all):
        d = []
        for r in mib_all:
            with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=10, retries=3,
                              max_repetitions=5, ) as snmp:
                for res in await snmp.get(r):
                    status = res.value.decode('UTF-8')
                    d.append(status)
        return d

    # for row in rows:


# def stat(kod)


# print(text)
# text += "Cisco:\n"
# for k_l, v_l in lease[kod]["cisco"].items():
#     text += "%s %s\n" % (k_l, v_l)
#
# text += "Registrator:\n"
# for k_l, v_l in lease[kod]["registrator"].items():
#     text += "%s %s\n" % (k_l, v_l)
#


#
#
# def info_filial(kod, st="all"):
#     text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nloopback %s\n" \
#            "IP_LAN: %s\nIP_Kiosk: %s\nIP_CAM: %s\nIP_SC: %s\nISP1_NAME: %s\nISP1: %s\ngateway_isp1: %s\n
#            ISP2_NAME: %s\nISP2: %s\ngateway_isp2: %s\nserial: %s\n" % \
#            (dat[kod]["name"],
#             dat[kod]["kod"],
#             data.region[int(dat[kod]["region"])],
#             dat[kod]["sysName"],
#             dat[kod]["loopback"],
#             dat[kod]["Vlan100"],
#             dat[kod]["Vlan200"],
#             dat[kod]["Vlan400"],
#             dat[kod]["Vlan500"],
#             dat[kod]["ISP1_NAME"],
#             dat[kod]["ISP1"],
#             dat[kod]["gateway_isp1"],
#             dat[kod]["ISP2_NAME"],
#             dat[kod]["ISP2"],
#             dat[kod]["gateway_isp2"],
#             dat[kod]["serial"])
#     print("error_m_2")
#     try:

# except:
#     pass
#
# return text

# print("error_m_2")
# try:
#     text += "Cisco:\n"
#     for k_l, v_l in lease[self.kod]["cisco"].items():
#         text += "%s %s\n" % (k_l, v_l)
#
#     text += "Registrator:\n"
#     for k_l, v_l in lease[self.kod]["registrator"].items():
#         text += "%s %s\n" % (k_l, v_l)
# except:
#     pass

# return text
# elif st == "fil":
#     text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nIP_LAN: %s\nIP_CAM: %s\nIP_SC: %s\n" % \
#            (dat[self.kod]["name"], dat[self.kod]["kod"], data.region[int(dat[self.kod]["region"])],
#             dat[self.kod]["sysName"],
#             dat[self.kod]["IP_100"],
#             dat[self.kod]["IP_400"],
#             dat[self.kod]["IP_500"]
#             )
#     return text

async def link():
    keyboard = types.InlineKeyboardMarkup()
    url = "https://docs.google.com/spreadsheets/d/1068DuSdyrtRYG3kDDL3oXx2GnqqC5CDMRlF4ZSfDvpU/edit?usp=sharing"
    url_button = types.InlineKeyboardButton(text="График дежурств", url=url)
    vpn_button = types.InlineKeyboardButton(text="Настройка VPN", url="https://telegra.ph/Nastrojka-VPN-06-29")
    reg_button = types.InlineKeyboardButton(text="Настройка видеорегистратора", url="https://telegra.ph/11-01-23-10")
    domen_button = types.InlineKeyboardButton(text="Ввод компьютера в домен", url="https://telegra.ph/Vvod-kompyutera-v-domen-06-30")
    keyboard.add(url_button)
    keyboard.add(vpn_button)
    keyboard.add(reg_button)
    keyboard.add(domen_button)
    return keyboard
