from pysnmp.hlapi import *
from pprint import pprint
import os
from datetime import datetime
from work import sql
# from loader_telebot import bot
from loader import bot
import asyncio
import time
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

mib = {  # "ifInOctets_isp1": "1.3.6.1.2.1.31.1.1.1.6.1",
    #   "ifOutOctets_isp1": "1.3.6.1.2.1.31.1.1.1.10.1",
    #   "ifInOctets_isp2": "1.3.6.1.2.1.31.1.1.1.6.2",
    #   "ifOutOctets_isp2": "1.3.6.1.2.1.31.1.1.1.10.2",

    "ifInOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.6.%s",
    "ifOutOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.10.%s",
    "ifInOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.6",
    "ifOutOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.10"
}
import threading



async def thread_check():
    print("start")
    await start_snmp()
    # asyncio.run(start_snmp())
    # asyncio.ensure_future(start_snmp())
    # loop = asyncio.get_running_loop()
    # # with concurrent.futures.ThreadPoolExecutor() as pool:
    # #     await loop.run_in_executor(pool, start_snmp)
    # #     # print('custom thread pool', result)
    # # loop.run_in_executor(start_snmp)
    # loop.run_in_executor(None, start_snmp())
    # await start_snmp()
async def start_snmp():
    print("stop")
    await bot.send_message(chat_id=765333440, text="dddddd")
    i = 0
    while i < 2:
        rows = await sql.sql_select("SELECT loopback, kod FROM filial")
        for row in rows:
            if (await sql.sql_selectone(f"SELECT count(loopback) FROM status WHERE loopback = '{row[0]}'"))[0] == 0:
                await oid(row[0], row[1])
            else:
                await snmp(row[0])

async def oid(loopback, kod):
    oid = "1.3.6.1.2.1.31.1.1.1.1"
    i = 0
    print(loopback)
    In_isp1, Out_isp1, In_isp2, Out_isp2 = "0", "0", "0", "0"
    await sql.sql_insert(f"INSERT INTO status (loopback, kod) VALUES ('{loopback}', {kod})")
    while i < 35:
        await asyncio.sleep(1)
        i += 1
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',

                               authProtocol=usmHMACSHAAuthProtocol
                               ),
                   UdpTransportTarget((str(loopback), 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity("%s.%s" % (oid, i)))
                   ))

        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:

                oi = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                #                print(oi)
                if oi == "Tu0":
                    numoid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    print(numoid)
                    In_isp1 = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    Out_isp1 = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                    # stat[kod]["oid"]["ifInOctets_isp1_tunnel"] = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    # stat[kod]["oid"]["ifOutOctets_isp1_tunnel"] = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                elif oi == "Tu1":
                    numoid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    print(numoid)
                    In_isp2 = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    Out_isp2 = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                    # stat[kod]["oid"]["ifInOctets_isp2_tunnel"] = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    # stat[kod]["oid"]["ifOutOctets_isp2_tunnel"] = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                else:
                    pass

        await sql.sql_insert(
            f"UPDATE status SET In_isp1 = '{In_isp1}',Out_isp1 = '{Out_isp1}', In_isp2 = '{In_isp2}', Out_isp2 ='{Out_isp2}' WHERE loopback = '{loopback}'")


async def snmp(loopback):
    # print(loopback)
    await asyncio.sleep(1)
    oid_all = sql.sql_selectone_no_await(
        f"SELECT In_isp1, Out_isp1, In_isp2, Out_isp2 FROM status WHERE loopback = '{loopback}'")
    d = []
    for oid in oid_all:
        await asyncio.sleep(1)
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
                   UdpTransportTarget((str(loopback), 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )

        if errorIndication:
            print(errorIndication)
            # "No SNMP response received before timeout"
            print("тут ошибка")
            await sql.sql_select(
                f"UPDATE status SET In1_two = In1_one, Out1_two = Out1_one, In2_two = In2_one, Out2_two = Out2_one "
                f"WHERE loopback = '{loopback}'")
            break
        #            for k in subscrib[kod]:
        #                bot.send_message(chat_id=k, text="%s\n  %s" % (dat[kod]["name"], text))
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                #                print(' = '.join([x.prettyPrint() for x in varBind]))
                m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                d.append(m)
    request = f"UPDATE status SET In1_one = In1_two, Out1_one = Out1_two, In2_one = In2_two, Out2_one = Out2_two, " \
              f"In1_two = {d[0]}, Out1_two = {d[1]},In2_two = {d[2]}, Out2_two = {d[3]} WHERE loopback = '{loopback}'"

    await sql.sql_insert(request)
    await check(loopback)


async def check(loopback):
    await asyncio.sleep(1)
    st = await sql.sql_selectone(
        f"SELECT In1_two, In2_two, Out1_two, Out2_two, In1_one,  In2_one, Out1_one, Out2_one "
        f"FROM status WHERE loopback = '{loopback}'")
    Intunnel1 = st[0] - st[4]
    Intunnel2 = st[1] - st[5]
    Outtunnel1 = st[2] - st[6]
    Outtunnel2 = st[3] - st[7]
    status1, status2 = 3, 3
    if Intunnel1 > 0 or Outtunnel1 > 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status1 = 1 WHERE loopback = '{loopback}'")
        status1 = 1
    elif Intunnel1 == 0 or Outtunnel1 == 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status1 = 0 WHERE loopback = '{loopback}'")
        status1 = 0
    else:
        print("Ошибка 1")
    if Intunnel2 > 0 or Outtunnel2 > 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status2 = 1 WHERE loopback = '{loopback}'")
        status2 = 1
    elif Intunnel2 == 0 or Outtunnel2 == 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status2 = 0 WHERE loopback = '{loopback}'")
        status2 = 0
    else:
        print("Ошибка 2")
    # print("%s" % status1)
    # print("%s" % status2)
    status_t1, status_t2, kod = await sql.sql_selectone(
        f"SELECT status_1, status_2, kod FROM status WHERE loopback = '{loopback}'")
    # print(status_t1)
    # print(status_t2)
    # t = "%s\n%s\n" % (dat[kod]["name"], dat[kod]["sysName"])
    # text = "Филиал %s\n" % kod
    # try:
    #     stat[kod]["status_t1"]
    #     stat[kod]["status_t2"]
    # except:
    #     stat[kod]["status_t1"] = 3
    #     stat[kod]["status_t2"] = 3
    if status1 == 0 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            # print("ok")
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔴 Филиал не доступен \nLoopback: {data[2]}\n{data[5]}\n" \
                   f"ISP_1: {data[3]}\n" \
                   f"{data[6]}\nISP_2: {data[4]}"
            print("Филиал не доступен")
            # stat[kod]["status_t1"] = 0
            # stat[kod]["status_t2"] = 0
            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 0 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)
    elif status1 == 1 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔴 Резервный провайдер не работает \n" \
                   f"Loopback: {data[2]}\n{data[6]}\nISP_2: {data[4]}"
            # text += "🔵 🔴 Резервный провайдер не работает\n%s\nISP_2: %s"%(dat[kod]["ISP2_NAME"],dat[kod]["ISP2"])
            print("Резервный не работает")
            # stat[kod]["status_t1"] = 1
            # stat[kod]["status_t2"] = 0
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 0 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)

    elif status1 == 0 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name "
                f"FROM filial WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔵 Основной провайдер не работает\n\n" \
                   f"Loopback: {data[2]}\n{data[5]}\nISP_1: {data[3]}\n"
            # text += "🔴 🔵 Основной провайдер не работает\n%s\nISP_1: %s"%(dat[kod]["ISP1_NAME"],dat[kod]["ISP1"])
            print("Основной не работает")
            # stat[kod]["status_t1"] = 0
            # stat[kod]["status_t2"] = 1
            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 1 WHERE loopback = '{loopback}'")

            await send_mess(kod, text)

    elif status1 == 1 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            # text += "🔵 🔵 Филиал работает"
            print("Филиал работает")
            data =await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔵 Филиал работает"
            # stat[kod]["status_t1"] = 1
            # stat[kod]["status_t2"] = 1
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 1 WHERE loopback = '{loopback}'")

            await send_mess(kod, text)
    else:
        pprint("тест")


async def send_mess(kod, text):
    try:
        rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
        # print(rows)
        for row in rows:
            # print(row)
                 await bot.send_message(chat_id=row, text=text)
    except TypeError:
        print("Ошибка отправки")


def data_monitor():
    return datetime.today().strftime("%H:%M:%S %d/%m/%Y")


def monitoring():
    keyboard = InlineKeyboardMarkup()
    i = 1
    # tab = []
    # null = InlineKeyboardButton(text="   ", callback_data="sub")
    # #    tab.append(telebot.types.InlineKeyboardButton(text="мониторинг", callback_data="sub"))
    # #    keyboard.row(null,null,null,null,null,null,null)
    tab = []
    text = ""
    colum = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60]
    colum_old = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51]
    rows = sql.sql_select_no_await(f"SELECT kod, status_1, status_2, ISP1, ISP2 FROM filial")
    for row in rows:
        ch1 = "🔵"
        ch2 = "🔵"
        if row[1] == 1:
            ch1 = "🔵"
        elif row[1] == 0:
            ch1 = "🔴"
        if row[2] == 1:
            ch2 = "🔵"
        elif row[2] == 0:
            ch2 = "🔴"
        if row[3] == "unassigned":
            ch1 = "⚪"
        if row[4] == "unassigned":
            ch2 = "⚪"
        tab.append(InlineKeyboardButton(text=f"{row[0]} {ch1}{ch2}", callback_data=f"sub_{row[0]}"))
        if i in colum_old:
            keyboard.row(*tab)
            tab = []
        i += 1
    keyboard.row(*tab)
    bot.edit_message_text(chat_id="@sdwan_monitoring", message_id=21,
                          text="<---------------->\n Время проверки %s" % data_monitor(), reply_markup=keyboard)
