from work import sql
from pysnmp.hlapi import *
import asyncio
import aiosnmp
from loader import bot
from work.check_vs import send_mess
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlite3 import OperationalError
from aiosnmp.exceptions import SnmpTimeoutError
trassir = [
           # '1.3.6.1.4.1.3333.1.1',  # db
           '1.3.6.1.4.1.3333.1.2',  # archive
           '1.3.6.1.4.1.3333.1.3',  # disk
           # '1.3.6.1.4.1.3333.1.4',  # network
           '1.3.6.1.4.1.3333.1.5',  # cameras
           '1.3.6.1.4.1.3333.1.6',  # script
           # '1.3.6.1.4.1.3333.1.7',  # name
           # '1.3.6.1.4.1.3333.1.8',  # cam_down
           # '1.3.6.1.4.1.3333.1.9',  # ip address
           '1.3.6.1.4.1.3333.1.10',  # firmware
           '1.3.6.1.4.1.3333.1.11',  # up_time
            '1.3.6.1.4.1.3333.1.12',  # version
           ]


# trassirusercam = {
#     u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
#     u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
#     u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
#     u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
#     u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11',
#     u'\U0001F50D' + ' Не работает камера:': '1.3.6.1.4.1.3333.1.8'
# }
# trassiruser = {
#     u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
#     u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
#     u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
#     u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
#     u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11'
# }
trassirmonitoring = ['1.3.6.1.4.1.3333.1.3', '1.3.6.1.4.1.3333.1.5', '1.3.6.1.4.1.3333.1.6', '1.3.6.1.4.1.3333.1.12']


async def snmpregist(ip):
    d = []
    for r in trassirmonitoring:
        with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=15, retries=3, max_repetitions=7, ) as snmp:
            try:
                for res in await snmp.get(r):
                    if r == '1.3.6.1.4.1.3333.1.12':
                        try:
                            status = res.value.decode('UTF-8')
                            d.append(status)
                        except AttributeError:
                            d.append('0')
                    else:
                        try:
                            status = res.value.decode('UTF-8')
                        except AttributeError:
                            return "Null"
                        d.append(status)
            except aiosnmp.exceptions.SnmpTimeoutError:
                return False
    return d


async def info_snmp_registrator(ip, mib_all):
        d = []
        for r in mib_all:
            with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=10, retries=3,
                              max_repetitions=5, ) as snmp:
                        for res in await snmp.get(r):
                            try:
                                status = res.value.decode('UTF-8')
                            except AttributeError:
                                d.append("ERROR")
                            d.append(status)
        return d


async def cam_snmp(ip):
    d = []
    with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=5, retries=3, max_repetitions=2, ) as snmp:
        try:
            for res in await snmp.get('1.3.6.1.4.1.3333.1.5'):
                status = res.value.decode('UTF-8')
                d.append(status)
        except SnmpTimeoutError:
            return False

    # try:
        #     for res in await snmp.get('1.3.6.1.4.1.3333.1.5'):
        #         try:
        #             status = res.value.decode('UTF-8')
        #             d.append(status)
        #         except AttributeError:
        #             d.append("ERROR")
        # except SnmpTimeoutError:
        #     d.append("ERROR")
    return d


async def shed():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(start_check_registrator_cam, 'interval', hours=3)
    scheduler.start()


async def start_check_registrator_cam():
    print("reg_cam_start")
    rows = await sql.sql_select(f"SELECT ip FROM registrator")
    for row in rows:
        data_r = await cam_snmp(row[0])
        if data_r is False:
            print(f"Регистратор не доступен, камеры не проверить {row[0]}")
            pass
        # if data_r is False:
        #     request = f"""SELECT filial.name, registrator.hostname, filial.kod, down FROM filial LEFT JOIN registrator
        #     ON filial.kod = registrator.kod WHERE registrator.ip = '{row[0]}'"""
        #     r = await sql.sql_selectone(request)
        #     if r[3] == 0:
        #         await sql.sql_insert(f"Update registrator SET down = 1 WHERE ip = '{row[0]}'")
        #         text = f"{r[0]} \nРегистратор {r[1]}\nНе доступен"
        #         await send_mess(r[2], text)
        # elif data_r == "Null":
        #     print(f"Ошибка скрипта snmp {row}")
        else:
            cam_down = data_r[0].split()[0]
            select = await sql.sql_selectone(f"SELECT disk, cam_down, kod, cam, down, script FROM registrator WHERE ip = '{row[0]}'")
            disk_old, cam_down_old, kod, cam, down, script_old = select
            if cam_down != cam_down_old:
                if cam_down == cam:
                    text = await info_filial(row[0], 'cam_up')
                    text += "Камеры работают"
                    await send_mess(kod, text)
                else:
                    text = await info_filial(row[0], 'cam_down')
                    text += "Камера не работает"
                    await send_mess(kod, text)
                await sql.sql_insert(f"Update registrator SET cam_down ='{cam_down}' WHERE ip = '{row[0]}'")
    print("reg_cam_stop")


async def start_check_registrator(order):
    print("reg")
    while 0 < 1:
        rows = await sql.sql_select(f"SELECT ip FROM registrator ORDER BY ip {order}")
        for row in rows:
            print(row[0])
            data_r = await snmpregist(row[0])
            print(data_r)
            try:
                await sql.sql_insert(f"UPDATE registrator SET ver_snmp = '{data_r[3]}'")
            except OperationalError:
                await sql.sql_insert("ALTER TABLE registrator ADD ver_snmp TEXT")
            except TypeError:
                pass
            if data_r is False:
                request = f"""SELECT filial.name, registrator.hostname, filial.kod, down FROM filial LEFT JOIN registrator 
                ON filial.kod = registrator.kod WHERE registrator.ip = '{row[0]}'
                    """
                r = await sql.sql_selectone(request)
                if r[3] == 0:
                    await sql.sql_insert(f"Update registrator SET down = 1 WHERE ip = '{row[0]}'")
                    text = f"{r[0]} \nРегистратор {r[1]}\nНе доступен"
                    await send_mess(r[2], text)
            elif data_r == "Null":
                print(f"Ошибка скрипта snmp {row}")
            else:
                disk = data_r[0]
                cam_down = data_r[1].split()[0]
                script = data_r[2]
                select = await sql.sql_selectone(f"SELECT disk, cam_down, kod, cam, down, script FROM registrator WHERE ip = '{row[0]}'")
                disk_old, cam_down_old, kod, cam, down, script_old = select
                if down is None:
                    await info_registrator(row[0])
                    continue
                elif down == 1:
                    text = "Регистратор работает\n"
                    try:
                        text += await info_filial(row[0], 'up')
                    except Exception as n:
                        print(f"ERROR = Регистратор работает {n}")
                    await send_mess(kod, text)
                    await sql.sql_insert(f"Update registrator SET down = 0 WHERE ip = '{row[0]}'")

                if disk_old != disk:
                    await sql.sql_insert(f"Update registrator SET disk = '{data_r[0]}' WHERE ip = '{row[0]}'")
                # if cam_down != cam_down_old:
                #     if cam_down == cam:
                #         text = await info_filial(row[0], 'cam_up')
                #         text += "Камеры работают"
                #         await send_mess(kod, text)
                #     else:
                #         text = await info_filial(row[0], 'cam_down')
                #         text += "Камера не работает"
                #         await send_mess(kod, text)
                #     await sql.sql_insert(f"Update registrator SET cam_down ='{cam_down}' WHERE ip = '{row[0]}'")
                if script != script_old:
                    await sql.sql_insert(f"Update registrator SET script = '{data_r[2]}' WHERE ip = '{row[0]}'")


async def info_filial(ip, data):
    if data == 'cam_up':
        mib = [
           '1.3.6.1.4.1.3333.1.2',  # archive
           '1.3.6.1.4.1.3333.1.3',  # disk
           '1.3.6.1.4.1.3333.1.5',  # cameras
           '1.3.6.1.4.1.3333.1.11',  # up_time
           ]
        info = await info_snmp_registrator(ip, mib)
        request = f"""SELECT filial.name, registrator.hostname FROM filial LEFT JOIN registrator ON filial.kod = registrator.kod 
                    WHERE registrator.ip = '{ip}'"""
        row = await sql.sql_selectone(request)
        text = f"""
        {row[0]}
💻 Сервер {row[1]} / {ip}
💽 Диски {info[1]}
📃 Глубина архива дней {info[0]}
🎥 Камеры {info[2]}
⌛  Время работы сервера  {info[3]}\n """
        return text

    elif data == 'cam_down':
        mib = [
           '1.3.6.1.4.1.3333.1.2',  # archive
           '1.3.6.1.4.1.3333.1.3',  # disk
           '1.3.6.1.4.1.3333.1.5',  # cameras
           '1.3.6.1.4.1.3333.1.11',  # up_time
           '1.3.6.1.4.1.3333.1.8',  # cam_down
           ]
        info = await info_snmp_registrator(ip, mib)
        request = f"""SELECT filial.name, registrator.hostname FROM filial LEFT JOIN registrator ON filial.kod = registrator.kod 
                    WHERE registrator.ip = '{ip}'"""
        row = await sql.sql_selectone(request)
        text = f"""
        {row[0]}
💻 Сервер {row[1]} / {ip}
💽 Диски {info[1]}
📃 Глубина архива дней {info[0]}
🎥 Камеры {info[2]}
⌛  Время работы сервера  {info[3]}\n
🔍 Не работает камера: {info[4]} 
                """
        return text

    elif data == 'up':
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
        info = await info_snmp_registrator(ip, mib)
        request = f"""SELECT filial.name, registrator.hostname FROM filial LEFT JOIN registrator 
ON filial.kod = registrator.kod WHERE registrator.ip = '{ip}'"""
        row = await sql.sql_selectone(request)
        text = f"{row[0]}\n" \
               f"💻 Сервер {row[1]} / {ip}\n" \
               f"💽 Диски {info[1]}\n" \
               f"📃 Глубина архива дней {info[0]}\n" \
               f"🎥 Камеры {info[2]}\n" \
               f"🔍 Не работает камера: {info[4]}\n" \
               f"⌛  Время работы сервера  {info[6]}\n"
        return text

async def info_registrator(ip):
    row = await info_snmp_registrator(ip, trassir)
    cam = row[2].split()[2]
    cam_down = row[2].split()[0]
    request = f"""UPDATE registrator 
SET archive = '{row[0]}', disk = '{row[1]}', cam = '{cam}', 
cam_down = '{cam_down}', script = '{row[3]}', firmware = '{row[4]}', uptime = '{row[5]}', down = 0 WHERE ip = '{ip}'"""
    print(request)
    await sql.sql_insert(request)

