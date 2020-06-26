from work import sql
from pysnmp.hlapi import *
import asyncio
import aiosnmp
from loader import bot
import time
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
trassirmonitoring = ['1.3.6.1.4.1.3333.1.3', '1.3.6.1.4.1.3333.1.5']


async def snmpregist(ip):
    d = []
    for r in trassirmonitoring:
        with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=10, retries=3,
                          max_repetitions=5, ) as snmp:
            try:
                for res in await snmp.get(r):
                    status = res.value.decode('UTF-8')
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
                            status = res.value.decode('UTF-8')
                            d.append(status)
        return d


async def start_check_registrator():
    while 0 < 1:
        await asyncio.sleep(5)
        rows = await sql.sql_select("SELECT ip FROM registrator")
        for row in rows:
            data_r = await snmpregist(row[0])
            if data_r is False:
                print("ti")
                request = f"""SELECT filial.name, registrator.hostname, filial.kod, down FROM filial LEFT JOIN registrator 
                ON filial.kod = registrator.kod WHERE registrator.ip = '{row[0]}'
                    """
                r = await sql.sql_selectone(request)
                if r[3] == 0:
                    await sql.sql_insert(f"Update registrator SET down = 1 WHERE ip = '{row[0]}'")
                    text = f"{r[0]} \nРегистратор {r[1]}\nНе доступен"
                    await send_mess(r[2], text)
            else:
                disk = data_r[0]
                cam_down = data_r[1].split()[0]
                select = await sql.sql_selectone(f"SELECT disk, cam_down, kod, cam, down FROM registrator WHERE ip = '{row[0]}'")
                disk_old, cam_down_old, kod, cam, down = select
                if down == "":
                    await info_registrator(row[0])
                    continue
                elif down == 1:
                    text = "Регистратор работает\n"
                    text += await info_filial(row[0], 'up')
                    await send_mess(kod, text)

                    await sql.sql_insert(f"Update registrator SET down = 0 WHERE ip = '{row[0]}'")
                if disk_old == disk:
                    pass
                else:
                    print(f"Ошибка диска {row[0]}")
                    await sql.sql_insert(
                        f"Update registrator SET disk = '{data_r[0]}' WHERE ip = '{row[0]}'")
                if cam_down == cam_down_old:
                    pass
                else:
                    if cam_down == cam:
                        print(f"Камера работает {row[0]}")
                        text = await info_filial(row[0], 'cam_up')
                        text += "Камеры работают"
                        await send_mess(kod, text)
                    else:
                        print(f"Камера не работает {row[0]}")
                        text = await info_filial(row[0], 'cam_down')
                        text += "Камеры не работают"
                        await send_mess(kod, text)
                    await sql.sql_insert(f"Update registrator SET cam_down ='{cam_down}' WHERE ip = '{row[0]}'")
                # except:
                #     r = (await sql.sql_selectone(f"""
                #     SELECT filial.name, registrator.hostname, filial.kod FROM filial LEFT JOIN registrator ON filial.kod = registrator.kod
                #     WHERE registrator.ip = '{row[0]}'
                #     """))
                #     text = f"{r[0]} \nРегистратор {r[1]}\nНе доступен"
                #     await send_mess(r[2], text)
                #     print("GLOBAL ERROR")


async def info_filial(ip, data):
    if data == 'cam_up':
        mib = [
           '1.3.6.1.4.1.3333.1.2',  # archive
           '1.3.6.1.4.1.3333.1.3',  # disk
           '1.3.6.1.4.1.3333.1.5',  # cameras
           '1.3.6.1.4.1.3333.1.11',  # up_time
           ]
        print("dddd")
        info = await info_snmp_registrator(ip, mib)
        print(info)
        request = f"""SELECT filial.name, registrator.hostname FROM filial LEFT JOIN registrator ON filial.kod = registrator.kod 
                    WHERE registrator.ip = '{ip}'"""
        print(request)
        row = await sql.sql_selectone(request)
        text = f"""
        {row[0]}
        💻 Сервер {row[1]}
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
        💻 Сервер {row[1]}
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
        print(info)
        request = f"""SELECT filial.name, registrator.hostname FROM filial LEFT JOIN registrator 
ON filial.kod = registrator.kod WHERE registrator.ip = '{ip}'"""
        row = await sql.sql_selectone(request)
        print(row)
        text = f"{row[0]}\n" \
               f"💻 Сервер {row[1]}\n" \
               f"💽 Диски {info[1]}\n" \
               f"📃 Глубина архива дней {info[0]}\n" \
               f"🎥 Камеры {info[2]}\n" \
               f"🔍 Не работает камера: {info[4]}\n" \
               f"⌛  Время работы сервера  {info[6]}\n"
        return text

async def info_registrator(ip):
    row = await info_snmp_registrator(ip, trassir)
    print(row)
    print(row[2])
    cam = row[2].split()[2]
    cam_down = row[2].split()[0]
    request = f"""UPDATE registrator 
SET archive = '{row[0]}', disk = '{row[1]}', cam = '{cam}', 
cam_down = '{cam_down}', script = '{row[3]}', firmware = '{row[4]}', uptime = '{row[5]}', down = 0 WHERE ip = '{ip}'"""
    # print(request)
    await sql.sql_insert(request)
    #     f"UPDATE disk = '{disk}', cam_down = '{cam_down}', cam = '{cam}' FROM registrator WHERE ip = '{row[0]}'")
    #
    #

        #     st, statusall = "", ""
        #     s, r = 0, 0
        #     #        if len(registr.split(";")) > 1:
        #     #            print("Больше двух")
        #     #       print("registra " + registr)
        #     #        print(len(registr.split(";")))
        #     if stregistr == "1":
        #         #            print(registr + " не проверяется")
        #         continue
        #     else:
        #         while r < len(registr.split(";")):
        #             st = snmpregist(registr.split(";")[r])[1]
        #             statusall = statusall + st
        #             r += 1
        #
        #         #        print(statusall)
        #         if statusall == stregistr:
        #             continue
        #         else:
        #             r = 0
        #             stsend = ''
        #             while r < len(statusall.split(";")) - 1:
        #                 if stregistr == "":
        #
        #                     stsend = statusall
        #
        #                     # sendreg(statusall, name, reg=registr, st=1)
        #                     break
        #                 elif statusall.split(";")[r] == "0":
        #                     if statusall.split(";")[r] == stregistr.split(";")[r]:
        #                         stsend = stsend + statusall.split(";")[r] + ";"
        #                         r += 1
        #                         continue
        #                     else:
        #                         name_server = stregistr.split(";")[r].split(":")[4]
        #                         stsend = stsend + statusall.split(";")[r]
        #                         #                        print('Не доступен '+name_server)
        #
        #                         # sendreg(statusall.split(";")[r], name, reg=registr)
        #                 elif stregistr.split(";")[r] == "0":
        #                     stsend = stsend + statusall.split(";")[r]
        #                     #                    print('Доступен')
        #                     # sendreg(statusall.split(";")[r], name, text="Доступен", reg=registr, st=1)
        #
        #                 else:
        #                     if statusall.split(";")[r] == stregistr.split(";")[r]:
        #                         stsend = stsend + statusall.split(";")[r] + ";"
        #                         r += 1
        #                         continue
        #                     else:
        #                         stat = statusall.split(";")[r]
        #                         stre = stregistr.split(";")[r]
        #                         #                        print(stat+" = "+ stregistr)
        #                         if stat.split(":")[2] != stre.split(":")[2]:
        #                             if stat.split(":")[2] == "OK":
        #                                 #                                print("нет ошибка диска")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 #                                print(registr)
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с жестким диском решена",
        #                                 #         reg=registr, st=1)
        #                             else:
        #                                 #                                print("Ошибка диска")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 #                                print (stsend)
        #                                 #                                print(registr)
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с жестким диском",
        #                                 #         reg=registr, st=1)
        #                         elif stat.split(":")[4] != stre.split(":")[4]:
        #                             camdown = re.findall('\d+', stat.split(":")[4].split("/")[0])
        #                             cam = re.findall('\d+', stat.split(":")[4].split("/")[1])
        #                             #                            print (camdown)
        #                             #                            print (cam)
        #                             if camdown < cam:
        #                                 #                                print("Ошибка камеры")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с камерой", reg=registr,
        #                                 #         st=2)
        #                             elif camdown == cam:
        #                                 #                                print("Камеры ОК")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 # sendreg(statusall.split(";")[r], name, text="Камеры работают", reg=registr,
        #                                 #         st=1)
        #                         else:
        #                             stsend = stsend + statusall.split(";")[r]
        #
        #                 stsend = stsend + ";"
        #                 #                print("r1" + str(r))
        #                 r += 1
        #             #                print("r2" + str(r))
        #             #
        #             # sql_insert("UPDATE snmp SET stregistr = '" + stsend + "' WHERE registr = '" + registr + "'")
        # except Exception as e:
        #     print(e)
            # if str(e) == "list index out of range":
            #     bot.send_message(ADMIN, "Ошибка проверки регистратора, добавлен новый регистратор " + registr)
            #     sql_insert("UPDATE snmp SET stregistr = '' WHERE registr = '" + str(registr) + "'")
            # #         print("Ошибка проверки регистратора "+ str(e))
            # else:
            #     bot.send_message(ADMIN, "Ошибка проверки регистратора " + str(registr) + " " + str(e))
            #     sql_insert("UPDATE snmp SET stregistr = '' WHERE registr = '" + str(registr) + "'")
            #     continue
    # sr += 1
    # savestatus(sr, timesr, p=2)
    # select_registr()


async def send_mess(kod, text):
    try:
        rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
        for row in rows:
            await asyncio.sleep(1)
            await bot.send_message(chat_id=row, text=text)
    except TypeError:
        print("Ошибка отправки")

# start_check_registrator()

