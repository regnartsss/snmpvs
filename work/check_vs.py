from pysnmp.hlapi import *
from pprint import pprint
from datetime import datetime
from work import sql
from loader import bot
import asyncio
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from concurrent.futures import ThreadPoolExecutor


async def start_snmp():
    print("start")
    i = 0
    loop = asyncio.get_running_loop()
    while i < 2:
        rows = await sql.sql_select("SELECT loopback, kod FROM filial ORDER BY loopback")
        for row in rows:
            await asyncio.sleep(1)
            if (await sql.sql_selectone(f"SELECT count(loopback) FROM status WHERE loopback = '{row[0]}'"))[0] == 0:
                await oid(row[0], row[1])
            else:
                await snmp(row[0])
                # executor = ThreadPoolExecutor()
                # await loop.run_in_executor(executor, snmp_no_async, row[0])
        await monitoring()


async def oid(loopback, kod):
    await asyncio.sleep(1)
    mib = "1.3.6.1.2.1.31.1.1.1.1"
    i = 0
    In_isp1, Out_isp1, In_isp2, Out_isp2 = "0", "0", "0", "0"
    await sql.sql_insert(f"INSERT INTO status (loopback, kod) VALUES ('{loopback}', {kod})")
    while i < 35:
        await asyncio.sleep(1)
        i += 1
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
                   UdpTransportTarget((str(loopback), 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(f"{mib}.{i}"))
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
                    In_isp1 = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    Out_isp1 = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                elif oi == "Tu1":
                    numoid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    In_isp2 = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    Out_isp2 = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                else:
                    pass
        await sql.sql_insert(
            f"UPDATE status SET In_isp1 = '{In_isp1}',Out_isp1 = '{Out_isp1}', "
            f"In_isp2 = '{In_isp2}', Out_isp2 ='{Out_isp2}' WHERE loopback = '{loopback}'")

# def snmp_no_async(loopback):
#     print("test")
#     asyncio.run(snmp(loopback))

async def snmp(loopback):
    # print("snmp")
    # oid_all = await sql.sql_selectone(f"SELECT In_isp1, Out_isp1, In_isp2, Out_isp2 FROM status "
    #                                   f"WHERE loopback = '{loopback}'")
    mib_all = await sql.sql_selectone(f"SELECT In_isp1, In_isp2 FROM status "
                                      f"WHERE loopback = '{loopback}'")
    d = []
    for mib in mib_all:
        await asyncio.sleep(1)
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
                   UdpTransportTarget((str(loopback), 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(mib)))
        )

        if errorIndication:
            print(errorIndication)
            print("Loopback не доступен")
            r = await sql.sql_selectone(f"SELECT In1_two, In2_two FROM status WHERE loopback = '{loopback}'")
            d.append(r[0])
            d.append(r[1])

            break
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                #                print(' = '.join([x.prettyPrint() for x in varBind]))
                m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                d.append(m)
    # request = f"UPDATE status SET In1_one = In1_two, Out1_one = Out1_two, In2_one = In2_two, Out2_one = Out2_two, " \
    #           f"In1_two = {d[0]}, Out1_two = {d[1]},In2_two = {d[2]}, Out2_two = {d[3]} WHERE loopback = '{loopback}'"
    request = f"UPDATE status SET In1_one = In1_two, In2_one = In2_two, In1_two = {d[0]}, In2_two = {d[1]} " \
              f"WHERE loopback = '{loopback}'"
    await sql.sql_insert(request)
    await check(loopback)


async def check(loopback):
    await asyncio.sleep(1)
    request = f"""SELECT In1_two, In2_two, Out1_two, Out2_two, In1_one,  In2_one, Out1_one, Out2_one
                FROM status WHERE loopback = '{loopback}'"""
    st = await sql.sql_selectone(request)
    In_tunnel_1 = st[0] - st[4]
    In_tunnel_2 = st[1] - st[5]
    Out_tunnel_1 = st[2] - st[6]
    Out_tunnel_2 = st[3] - st[7]
    # print(Intunnel1)
    # print(Outtunnel1)
    # print(Intunnel2)
    # print(Outtunnel2)
    status1, status2 = 3, 3
    if In_tunnel_1 > 0 or Out_tunnel_1 > 0:
        status1 = 1
    elif In_tunnel_1 == 0 or Out_tunnel_1 == 0:
        status1 = 0
    if In_tunnel_2 > 0 or Out_tunnel_2 > 0:
        status2 = 1
    elif In_tunnel_2 == 0 or Out_tunnel_2 == 0:
        status2 = 0
    status_t1, status_t2, kod = await sql.sql_selectone(
        f"SELECT status_1, status_2, kod FROM status WHERE loopback = '{loopback}'")

    if status1 == 0 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔴 Филиал не доступен \nLoopback: {data[2]}\n{data[5]}\n" \
                   f"ISP_1: {data[3]}\n {data[6]}\nISP_2: {data[4]}"

            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 0 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)
    elif status1 == 1 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔴 Резервный провайдер не работает \n" \
                   f"Loopback: {data[2]}\n{data[6]}\nISP_2: {data[4]}"
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 0 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)

    elif status1 == 0 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔵 Основной провайдер не работает\n\n" \
                   f"Loopback: {data[2]}\n{data[5]}\nISP_1: {data[3]}\n"
            print("Основной не работает")
            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 1 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)

    elif status1 == 1 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            print("Филиал работает")
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔵 Филиал работает"
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 1 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)
    else:
        pprint("тест")


async def request_name(loopback):
    await asyncio.sleep(1)
    return await sql.sql_selectone(
        f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial WHERE loopback = '{loopback}'")


async def send_mess(kod, text):
    try:
        rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
        for row in rows:
            await asyncio.sleep(1)
            await bot.send_message(chat_id=row, text=text)
    except TypeError:
        print("Ошибка отправки")


def data_monitor():
    return datetime.today().strftime("%H:%M:%S %d/%m/%Y")


async def monitoring():
    keyboard = InlineKeyboardMarkup()
    i = 1

    tab = []
    column = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60]
    # column_old = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51]
    request = f"SELECT filial.kod, status_1, status_2, ISP1, ISP2 FROM status " \
              f"INNER JOIN filial ON status.kod = filial.kod ORDER BY status.kod"
    # print(request)
    rows = await sql.sql_select(request)
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
        tab.append(InlineKeyboardButton(text=f"{ch1}{ch2}{row[0]} ", callback_data=f"sub_{row[0]}"))
        if i in column:
            keyboard.row(*tab)
            tab = []
        i += 1
    keyboard.row(*tab)
    await bot.edit_message_text(chat_id="@sdwan_monitoring", message_id=21,
                                text="<---------------->\n Время проверки %s" % data_monitor(), reply_markup=keyboard)


async def call_name(call):
    kod = call.data.split("_")[1]
    name = (await sql.sql_selectone(f"SELECT name FROM filial WHERE kod = {kod}"))[0]
    try:
        await bot.answer_callback_query(callback_query_id=call.id, text=f"{name}")
    except Exception as n:
        print(n)
