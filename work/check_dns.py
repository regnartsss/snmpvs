import time
from pysnmp.hlapi import *
import re
from work.sql import sql_insert, sql_select, sql_selectone
from loader import bot
from concurrent.futures import ThreadPoolExecutor
import asyncio

REGION = ['KRAS:РРC ВС Красноярск',
          'ABK:РРС ВС Хакасия и Тыва',
          'BUR:РРС ВС Бурятия, Южная Якутия',
          'ZABAI:РРС ВС Забайкальский Край',
          'IRK:РРС ВС Иркутск и Якутск',
          'IRKobl:РРС ВС Иркутская Область',
          'KRKR:РРС ВС Красноярский Край',
          'SC:Сервис',
          'SKLAD:Склад',
          'ADM:Администрация']

trassir = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11',
    'Не работает камера:': '1.3.6.1.4.1.3333.1.8',
    'ip address ': '1.3.6.1.4.1.3333.1.9',
    'Прошивка ': '1.3.6.1.4.1.3333.1.10'

}
trassirusercam = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11',
    u'\U0001F50D' + ' Не работает камера:': '1.3.6.1.4.1.3333.1.8'
}
trassiruser = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11'

}
# def start_snmp_dns():
#     loop = asyncio.get_event_loop()
#     executor = ThreadPoolExecutor()
#     loop.run_until_complete(snmp_dns_reg_no_async(loop, executor))
#
# #
# # async def start_snmp_dns_reg():
# #     loop = asyncio.get_event_loop()
# #     executor = ThreadPoolExecutor()
# #     await loop.run_in_executor(executor, snmp_dns_reg_no_async)
# #
# #
# # def snmp_dns_no_async():
# #
#
# async def snmp_dns_reg_no_async(loop, executor):
#     await asyncio.wait(fs={loop.run_in_executor(executor, select_device),

#                         loop.run_in_executor(executor, select_registr)})
# async def select_device():
#     loop = asyncio.get_running_loop()
#     executor = ThreadPoolExecutor()
#     await loop.run_in_executor(executor, snmp_no_async)
#



async def select_device():
    print("select_device")
    # await bot.send_message(chat_id=765333440, text="text")
    rows = await sql_select("SELECT ip, oidrou1, oidrou2 FROM snmp")
    for row in rows:
        await asyncio.sleep(1)
        (ip, oidrou1, oidrou2) = tuple(row)
        status1 = await snmp(ip, oidrou1)
        status2 = await snmp(ip, oidrou2)
        if status1 == "2" and status2 == "2":
            rows = await sql_select("SELECT name, rou1, rou2 FROM snmp WHERE ip = '" + ip + "'")
            for row in rows:
                await asyncio.sleep(1)

                (name, rou1, rou2) = tuple(row)
                if rou1 == status1 and rou2 == status2:
                    continue
                else:
                    await sql_insert(
                        "UPDATE snmp SET rou1 = '2', rou2 = '2' WHERE ip = '" + ip + "'")
                    print(u'\U0001F534' + name + " " + ip + " Филиал не доступен")
                    text = (u'\U0001F534' + " " + u'\U0001F534'" " + name + " " + ip + " Филиал не доступен")
                    return text
                    # await send_mess(ip, text)
        elif status1 == "1" and status2 == "2":
            rows = await sql_select("SELECT name, namerou2,  rou1, rou2 FROM snmp WHERE ip = '" + ip + "'")
            for row in rows:
                await asyncio.sleep(1)

                (name, namerou2, rou1, rou2) = tuple(row)
                #                name = ("ᅠ".join(name.split()))
                if rou1 == status1 and rou2 == status2:
                    continue
                else:
                    await sql_insert(
                        "UPDATE snmp SET rou1 = '1', rou2 = '2',status = '2' WHERE ip = '" + ip + "'")
                    print(name + " " + namerou2 + " туннель не работает")
                    text = (u'\U0001F535' + " " + u'\U0001F534'" " + name + " " + namerou2 + " туннель не работает")
                    return text
                    # await send_mess(ip, text)
        elif status1 == "2" and status2 == "1":
            rows = await sql_select("SELECT name, namerou1, rou1, rou2 FROM snmp WHERE ip = '" + ip + "'")
            for row in rows:
                await asyncio.sleep(1)

                (name, namerou1, rou1, rou2) = tuple(row)
                #                name = ("ᅠ".join(name.split()))
                if rou1 == status1 and rou2 == status2:
                    continue
                else:
                    await sql_insert(
                        "UPDATE snmp SET rou1 = '2', rou2 = '1',status = '2' WHERE ip = '" + ip + "'")
                    print(name + " " + namerou1 + " туннель не работает")
                    text = (u'\U0001F534' + " " + u'\U0001F535'" " + name + " " + namerou1 + " туннель не работает")
                    return text
                    # await send_mess(ip, text)


        elif status1 == "1" and status2 == "1":
            rows = await sql_select("SELECT name, rou1, rou2 FROM snmp WHERE ip = '" + ip + "'")
            for row in rows:
                await asyncio.sleep(1)

                (name, rou1, rou2) = tuple(row)
                #                name = ("ᅠ".join(name.split()))
                if rou1 == status1 and rou2 == status2:
                    continue
                else:
                    await sql_insert("UPDATE snmp SET rou1 = '1', rou2 = '1' WHERE ip = '" + ip + "'")
                    print(name + " филиал Работает")
                    text = (u'\U0001F535' + " " + u'\U0001F535'" " + name + " " + ip + " филиал Работает")
                    return text
                    # await send_mess(ip, text)
        else:
            print("тест")


async def snmp(ip, oidrou):
    mib = '1.3.6.1.2.1.2.2.1.8.' + oidrou + ''
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(), CommunityData('public'), UdpTransportTarget((ip, 161)), ContextData(),
                   ObjectType(ObjectIdentity(mib))))
        if errorIndication:
            status = "2"
            return status
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                status = (' ='.join([x.prettyPrint() for x in varBind])).split("=")[1]
        return status
    except Exception as e:
        print(f"Ошибка {e}")


async def snmpregist(ip):
    global st, trassir
    t = 0
    #    print(ip)
    #    print(len(ip.split(";")))
    te, st = '', ''
    try:
        while t < len(ip.split(";")):
            #        print(ip.split(";")[t])
            for r in trassir:
                #        print(r)
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(), CommunityData('dssl'), UdpTransportTarget((ip.split(";")[t], 161)),
                           ContextData(), ObjectType(ObjectIdentity(trassir[r]))))
                if errorIndication:
                    #                print(errorIndication)
                    st = "0"
                    break
                elif errorStatus:
                    print('%s at %s' % (
                        errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    continue
                else:
                    for varBind in varBinds:
                        status = (' ='.join([x.prettyPrint() for x in varBind])).split("=")[1]
                        #                  print(status)
                        te = (str(r) + " " + str(status) + "\n" + te + " ")
                        st = (st + ":" + status)
                        continue
            st += ";"
            t += 1
        #    print(st)

        return (te, st)
    except:
        print("Ошибка проверки айпи регистратора " + ip)


async def select_registr():
    print("select_registr")
    rows = await sql_select("SELECT ip, name, registr, stregistr FROM snmp")
    for row in rows:
            (ip, name, registr, stregistr) = tuple(row)
            st, statusall = "", ""
            s, r = 0, 0
            if stregistr == "1":
                continue
            else:
                while r < len(registr.split(";")):
                    st = (await snmpregist(registr.split(";")[r]))[1]
                    statusall = statusall + st
                    r += 1
                if statusall == stregistr:
                    continue
                else:
                    r = 0
                    stsend = ''
                    while r < len(statusall.split(";")) - 1:
                        if stregistr == "":
                            stsend = statusall
                            await sendreg(statusall, name, reg=registr, st=1)
                            break
                        elif statusall.split(";")[r] == "0":
                            if statusall.split(";")[r] == stregistr.split(";")[r]:
                                stsend = stsend + statusall.split(";")[r] + ";"
                                r += 1
                                continue
                            else:
                                name_server = stregistr.split(";")[r].split(":")[4]
                                stsend = stsend + statusall.split(";")[r]
                                #                        print('Не доступен '+name_server)

                                await sendreg(statusall.split(";")[r], name, reg=registr)
                        elif stregistr.split(";")[r] == "0":
                            stsend = stsend + statusall.split(";")[r]
                            #                    print('Доступен')
                            await sendreg(statusall.split(";")[r], name, text="Доступен", reg=registr, st=1)

                        else:
                            if statusall.split(";")[r] == stregistr.split(";")[r]:
                                stsend = stsend + statusall.split(";")[r] + ";"
                                r += 1
                                continue
                            else:
                                stat = statusall.split(";")[r]
                                stre = stregistr.split(";")[r]
                                #                        print(stat+" = "+ stregistr)
                                if stat.split(":")[2] != stre.split(":")[2]:
                                    if stat.split(":")[2] == "OK":
                                        #                                print("нет ошибка диска")
                                        stsend = stsend + statusall.split(";")[r]
                                        #                                print(registr)
                                        await sendreg(statusall.split(";")[r], name,
                                                      text="Проблема с жестким диском решена",
                                                      reg=registr, st=1)
                                    else:
                                        #                                print("Ошибка диска")
                                        stsend = stsend + statusall.split(";")[r]
                                        #                                print (stsend)
                                        #                                print(registr)
                                        await sendreg(statusall.split(";")[r], name, text="Проблема с жестким диском",
                                                      reg=registr, st=1)
                                elif stat.split(":")[4] != stre.split(":")[4]:
                                    camdown = re.findall('\d+', stat.split(":")[4].split("/")[0])
                                    cam = re.findall('\d+', stat.split(":")[4].split("/")[1])
                                    #                            print (camdown)
                                    #                            print (cam)
                                    if camdown < cam:
                                        #                                print("Ошибка камеры")
                                        stsend = stsend + statusall.split(";")[r]
                                        await sendreg(statusall.split(";")[r], name, text="Проблема с камерой",
                                                      reg=registr,
                                                      st=2)
                                    elif camdown == cam:
                                        #                                print("Камеры ОК")
                                        stsend = stsend + statusall.split(";")[r]
                                        await sendreg(statusall.split(";")[r], name, text="Камеры работают",
                                                      reg=registr,
                                                      st=1)
                                else:
                                    stsend = stsend + statusall.split(";")[r]

                        stsend = stsend + ";"
                        #                print("r1" + str(r))
                        r += 1
                    #                print("r2" + str(r))
                    #
                    await sql_insert("UPDATE snmp SET stregistr = '" + stsend + "' WHERE registr = '" + registr + "'")


async def sendreg(status, name, text="", reg="", st=0):
        rows = await sql_select('SELECT ip, registr, rou1, rou2 from snmp WHERE "registr" = "' + reg + '"')
        for row in rows:
            (ip, registr, rou1, rou2) = tuple(row)
            #        print(ip)
            rows2 = await sql_select('SELECT id, username from user WHERE "' + ip + '" = "' + str(1) + '"')
            for row in rows2:
                (id, username) = tuple(row)
                #            print(id)
                #            bot.send_message(id, text)
                #            print(status.split(";")[0])
                if status.split(";")[0] == '0' and (rou1 == "2" or rou2 == "2"):
                    #                print(id + " " + msg + "\n" + text)
                    bot.send_message(id, name + "\n Регистратор не доступен")
                else:
                    q = 1
                    msg = name + "\n"
                    key = trassir.keys()
                    if st == 1:
                        for s in trassiruser:
                            msg = msg + s + " " + status.split(':')[q] + "\n"
                            q += 1
                    elif st == 2:
                        for s in trassirusercam:
                            msg = msg + s + " " + status.split(':')[q] + "\n"
                            q += 1

                    else:
                        continue
                    # print("qqq")
                    #                print(id+" "+msg+"\n"+text)
                    await bot.send_message(id, msg + "\n" + text)



# def camst(status):
#     cam = status.split(":")[5]
#     camup = str(cam.split("/")[0]) + " "
#     camdown = " " + str(cam.split("/")[1])
#     return (camup, camdown)

#
# def downreg(message):
#     #    print("Появится в будущем")
#     global trassir
#     id = message.from_user.id
#     rows = await sql_select("SELECT ip, name, registr FROM snmp")
#     for row in rows:
#         (ip, name, registr) = tuple(row)
#         #        print(ip +'sss')
#         rows_2 = await sql_select('SELECT "' + ip + '" from user Where id = "' + str(id) + '" and "' + ip + '" = "1"')
#         #        print(len(rows_2))
#         if str(rows_2) == "[('1',)]":
#             r = 0
#             st = ""
#             while r < len(registr.split(";")):
#                 #                print(registr)
#                 st = snmpregist(registr.split(";")[r])[1]
#                 if st == "0;":
#                     await message.answer(message.chat.id,
#                                      text=name + "\n" + "Регистратор trassir не доступен или не установлен на данном филиале \n " +
#                                           registr.split(";")[r])
#                     r += 1
#                     continue
#                 else:
#                     q = 1
#                     msg = name + "\n"
#                     s = ""
#                     for s in trassir:
#                         #                        print(s)
#                         #                       print(st)
#                         #                        print(msg)
#                         msg = msg + s + " " + st.split(':')[q] + "\n"
#                         q += 1
#                 r += 1
#                 time.sleep(1)
#                 bot.send_message(message.chat.id, text=msg)
#         else:
#             continue

#
# def date():
#     time = datetime.datetime.today().strftime("%H:%M:%S %d/%m/%Y")
#     return (time)
#


async def send_mess(ip, text):
    print("send_mess")
    await bot.send_message(chat_id=765333440, text=text)
    # rows = await sql_select('SELECT id, username from user WHERE "' + ip + '" = "' + str(1) + '"')
    # for row in rows:
    #     (id, username) = tuple(row)
    #     print(id)
    #     print(text)
    #     # await bot.send_message(chat_id=id, text=text)

#
# def down(message):
#     id = message.from_user.id
#     mes_down = message.message_id + 1
#     down_name = u'\U0001F534' + "Список не работающих провайдеров" + u'\U0001F534'
#     bot.send_message(message.chat.id, ' - ')
#     rows = await sql_select("SELECT ip, name, namerou1, namerou2, rou1, rou2, datetime FROM snmp WHERE rou1='2' or rou2='2'")
#     for row in rows:
#         (ip, name, namerou1, namerou2, rou1, rou2, datetime) = tuple(row)
#         rows_2 = await sql_select('SELECT "' + ip + '" from user Where id = "' + str(id) + '" and "' + ip + '" = "1"')
#         if str(rows_2) == "[('1',)]":
#
#             try:
#                 try:
#                     if rou1 == "2" and rou2 == "2":
#                         down_rou = " "
#                         #       edit_sen(name, chat, mes_down, down_rou, datetime)
#                         down_name = (
#                                     down_name + "\n" + name + " " + down_rou + "\n " + " " + ip + "\n " + "   не работает с " + datetime + "\n")
#                         bot.edit_message_text(down_name, message.chat.id, mes_down)
#                     elif rou1 == "2" and rou2 == "1":
#                         down_rou = namerou1
#                         #         edit_sen(name, chat, mes_down, down_rou, datetime)
#                         down_name = (
#                                     down_name + "\n" + name + " " + down_rou + "\n " + " " + ip + "\n " + "   не работает с " + datetime + "\n")
#                         bot.edit_message_text(down_name, message.chat.id, mes_down)
#                     elif rou1 == "1" and rou2 == "2":
#                         down_rou = namerou2
#                         #         edit_sen(name, chat, mes_down, down_rou, datetime)
#                         down_name = (
#                                     down_name + "\n" + name + " " + down_rou + "\n " + " " + ip + "\n " + "   не работает с " + datetime + "\n")
#                         bot.edit_message_text(down_name, message.chat.id, mes_down)
#                 except:
#                     pass
#             except:
#                 pass
#     try:
#         bot.edit_message_text(down_name + u'\U0001F534', message.chat.id, mes_down)
#     except:
#         pass
#     bot.send_message(message.chat.id, ' - ', reply_markup=keyboardmenu)
#
#
# def edit_sen(name, chat, mes_down, down_rou, datetime):
#     global down_name
#
#     down_name = (down_name + "\n" + name + " " + down_rou + "\n " + "   не работает с " + datetime + "\n")
#     try:
#         await bot.edit_message_text(down_name, chat, mes_down)
#     except:
#         pass
#     while True:
#         try:
#             bot.edit_message_text(down_name, chat, mes_down)(none_stop=True, timeout=30)
#         except Exception as e:
#             print('Ошибка отправки' + e)
#             time.sleep(30)
#
#
# def searchoid(message):
#     global new_ip, new_name
#     # conn = sqlite3.connect('c:\snmp\mybase.bd')
#     new1 = ""
#     new2 = ""
#     roun1 = ""
#     roun2 = ""
#
#     i = 1
#     while i < 30:
#         mibname = '1.3.6.1.2.1.2.2.1.2.' + str(i) + ''
#
#         errorIndication, errorStatus, errorIndex, varBinds = next(
#             getCmd(SnmpEngine(),
#                    CommunityData('public'),
#                    UdpTransportTarget((new_ip, 161)),
#                    ContextData(),
#                    ObjectType(ObjectIdentity(mibname)))
#         )
#         for varBind in varBinds:
#             namerou = (' ='.join([x.prettyPrint() for x in varBind])).split("=")[1]
#             name = namerou.find("gre")
#             if name == 0:
#                 id = namerou.split("_")[3]
#                 if id == "rou1":
#                     print(new_ip + " qq " + new_name)
#                     await sql_insert(
#                         "INSERT INTO snmp (name, ip, namerou1, oidrou1) VALUES (""'" + new_name + "','" + new_ip + "','" + namerou + "','" + str(
#                             i) + "')")
#                     bot.send_message(message.chat.id,
#                                      "Добавлен филиал " + new_name + ", ip " + new_ip + " туннель " + namerou + " ")
#                 else:
#                     await sql_insert("UPDATE snmp SET oidrou2 = '" + str(
#                         i) + "', namerou2 = '" + namerou + "' WHERE ip = '" + new_ip + "'")
#                     bot.send_message(message.chat.id, "Туннель " + namerou + " ")
#                     await sql_insert("ALTER TABLE user ADD '" + str(new_ip) + "' TEXT ")
#
#         i = i + 1
#
#
# def spam_message(message):
#     rows = await sql_select('SELECT id from user')
#     #    pprint(rows)
#     text = message.text
#     for row in rows:
#         (id) = tuple(row)
#         id = str(id)
#         s = id.split("'")[1]
#         bot.send_message(chat_id=s, text=text)
#         time.spleep(1)
#
