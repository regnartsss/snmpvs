from pysnmp.hlapi import *
from datetime import datetime, time
from work import sql
from loader import bot
import asyncio
import aiosnmp
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import ChatNotFound
from work.email_send import send_email
from sqlite3 import OperationalError
from aiosnmp.asn1 import Error

async def start_snmp():
    print("start")
    # await asyncio.sleep(120)
    i = 0
    while i < 2:
        rows = await sql.sql_select(f"SELECT loopback, kod, sdwan FROM zabbix")
        for loopback, kod, sdwan in rows:
            if sdwan == 1:
                try:
                    if (await sql.sql_selectone(f"SELECT count(loopback) FROM zb_st WHERE loopback = '{loopback}'"))[0] == 0:
                        await oid(loopback, kod)
                    else:
                        await snmp(loopback, kod)
                except OperationalError:
                    await new_table_zb_st()
            elif sdwan == 0:
                try:
                    if (await sql.sql_selectone(f"SELECT count(loopback) FROM zb_st WHERE loopback = '{loopback}'"))[0] == 0:
                        await oid_mikrotik(loopback, kod)
                    else:
                        await check_snmp(loopback)
                except OperationalError:
                    await new_table_zb_st()
            else:
                print("Ошибка")


async def oid_mikrotik(ip, kod):
    i = 9
    mib = '1.3.6.1.2.1.2.2.1.2.'
    if kod is not None:
        await sql.sql_insert(f"INSERT INTO zb_st (loopback, kod) VALUES ('{ip}', {kod})")
        while i < 30:
            i += 1
            with aiosnmp.Snmp(host=ip, port=161, community="public", timeout=5, retries=1, max_repetitions=2, ) as s:
                try:
                    for res in await s.get(f"{mib}{i}"):
                        name_rou = res.value.decode('UTF-8')
                except AttributeError:
                    continue
                except aiosnmp.exceptions.SnmpTimeoutError:
                    print(f"timeout {ip}")
                    await sql.sql_insert(f"DElETE FROM zb_st WHERE loopback = '{ip}'")
                    break
                try:
                    if name_rou.split("_")[0] == "gre":
                        id = name_rou.split("_")[3]
                        if id == "rou1":
                            await sql.sql_insert(f"UPDATE zb_st SET In_isp1 = '{i}' WHERE loopback = '{ip}'")
                        elif id == "rou2":
                            await sql.sql_insert(f"UPDATE zb_st SET In_isp2= '{i}' WHERE loopback = '{ip}'")
                except UnboundLocalError:
                    continue


async def check_snmp(ip):
    try:
        status1, status2 = await snmp_mikrotik(ip)
    except ValueError:
        status1, status2 = 0, 0
    if status1 == 1:
        status1 = 1
    elif status1 == 2:
        status1 = 0
    if status2 == 1:
        status2 = 1
    elif status2 == 2:
        status2 = 0
    await check_all(ip, status1, status2)


async def snmp_mikrotik(ip):
    mib = '1.3.6.1.2.1.2.2.1.8.'
    mib_all = await sql.sql_selectone(f"SELECT In_isp1, In_isp2 FROM zb_st WHERE loopback = '{ip}'")
    status = []
    for mib_old in mib_all:
        with aiosnmp.Snmp(host=ip, port=161, community="public", timeout=5, retries=2, max_repetitions=2) as s:
            try:
                print(ip)
                print(f"{mib}{mib_old}")
                for res in await s.get(f"{mib}{mib_old}"):
                    status.append(res.value)
            except aiosnmp.exceptions.TimeoutError:
                pass
            except Error:
                status.append(0)
    return status


async def new_table_zb_st():
    request = """CREATE TABLE zb_st (
    loopback TEXT,
    In_isp1  TEXT,
    In_isp2  TEXT,
    Oper_isp1 TEXT,
    Oper_isp2 TEXT,
    Oper1    INT,
    Oper2    INT,
    OperISP2 INT,
    status_operisp2 INT,
    status_1 INT  DEFAULT (0),
    status_2 INT  DEFAULT (0),
    In1_one  INT  DEFAULT (0),
    In1_two  INT  DEFAULT (0),
    Out1_one INT  DEFAULT (0),
    Out1_two INT  DEFAULT (0),
    In2_one  INT  DEFAULT (0),
    In2_two  INT  DEFAULT (0),
    Out2_one INT  DEFAULT (0),
    Out2_two INT  DEFAULT (0),
    kod      INT)"""
    await sql.sql_insert(request)


async def oid(loopback, kod, repeat=0):
    mib = "1.3.6.1.2.1.31.1.1.1.1"
    i = 0
    in_isp1, Oper_isp1, in_isp2, Oper_isp2, Oper_tu1, Oper_tu2 = "0", "0", "0", "0", "0", "0"
    if kod is not None:
        if repeat == 0:
            await sql.sql_insert(f"INSERT INTO zb_st (loopback, kod) VALUES ('{loopback}', {kod})")
        while i < 35:
            i += 1
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                       UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
                       UdpTransportTarget((str(loopback), 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity(f"{mib}.{i}"))
                       ))
            if error_indication:
                return
            elif error_status:
                print('%s at %s' % (error_status.prettyPrint(),
                                    error_index and var_binds[int(error_index) - 1][0] or '?'))
            else:
                for varBind in var_binds:

                    oi = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                    #                print(oi)
                    if oi == "Tu0":
                        num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                        in_isp1 = "1.3.6.1.2.1.31.1.1.1.6.%s" % num_oid
                        Oper_tu1 = "1.3.6.1.2.1.2.2.1.8.%s" % num_oid

                    elif oi == "Tu1":
                        num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                        in_isp2 = "1.3.6.1.2.1.31.1.1.1.6.%s" % num_oid
                        Oper_tu2 = "1.3.6.1.2.1.2.2.1.8.%s" % num_oid
                    else:
                        pass
            Oper_isp2 = "1.3.6.1.2.1.2.2.1.8.2"
            await sql.sql_insert(
                f"UPDATE zb_st SET In_isp1 = '{in_isp1}', Oper_isp1 = '{Oper_tu1}', "
                f"In_isp2 = '{in_isp2}', Oper_isp2 ='{Oper_tu2}', OperISP2 = '{Oper_isp2}' WHERE loopback = '{loopback}'")


async def snmp(loopback, kod):
    print(loopback, kod)
    mib_all = await sql.sql_selectone(
        f"SELECT In_isp1, In_isp2, Oper_isp1, Oper_isp2, OperISP2 FROM zb_st WHERE loopback = '{loopback}'")
    # print(mib_all[0:4])
    if mib_all[0:4] == ('0', '0', '0', '0'):
        print("Проверить ", loopback, kod)
        await oid(loopback, kod, 1)
        return
    d = []
    for mib in mib_all:
        error_indication, error_status, error_index, var_binds = await snmp_v3(loopback, mib)
        if error_indication:
            print(error_indication)
            r = await sql.sql_selectone(f"SELECT In1_two, In2_two FROM zb_st WHERE loopback = '{loopback}'")
            d.append(r[0])
            d.append(r[1])
        elif error_status:
            print('%s at %s' % (error_status.prettyPrint(),
                                error_index and var_binds[int(error_index) - 1][0] or '?'))
        else:
            for varBind in var_binds:
                #                print(' = '.join([x.prettyPrint() for x in varBind]))
                m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                d.append(m)
    # print(d)
    try:
        request = f"UPDATE zb_st SET In1_one = In1_two, In2_one = In2_two, In1_two = {d[0]}, In2_two = {d[1]}, " \
                  f"Oper1 = {d[2]}, Oper2 = {d[3]}, status_operisp2 = {d[4]}  WHERE loopback = '{loopback}'"
        await sql.sql_insert(request)
        await check_cisco(loopback)
    except:
        pass


async def snmp_v3(loopback, mib):
    error_indication, error_status, error_index, var_binds = next(
        getCmd(SnmpEngine(),
               UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
               UdpTransportTarget((str(loopback), 161)),
               ContextData(),
               ObjectType(ObjectIdentity(mib)))
    )
    return error_indication, error_status, error_index, var_binds


async def check_cisco(loopback):
    await asyncio.sleep(1)
    request = f"""SELECT In1_two, In2_two, Out1_two, Out2_two, In1_one,  In2_one, Out1_one, Out2_one
                FROM zb_st WHERE loopback = '{loopback}'"""
    st = await sql.sql_selectone(request)
    in_tunnel_1 = st[0] - st[4]
    in_tunnel_2 = st[1] - st[5]
    out_tunnel_1 = st[2] - st[6]
    out_tunnel_2 = st[3] - st[7]
    status1, status2 = 3, 3
    if in_tunnel_1 > 0 or out_tunnel_1 > 0:
        status1 = 1
    elif in_tunnel_1 == 0 or out_tunnel_1 == 0:
        status1 = 0
    if in_tunnel_2 > 0 or out_tunnel_2 > 0:
        status2 = 1
    elif in_tunnel_2 == 0 or out_tunnel_2 == 0:
        status2 = 0
    await check_all(loopback, status1, status2)


async def check_all(loopback, status1, status2):
    status_t1, status_t2, kod = await sql.sql_selectone(
        f"SELECT status_1, status_2, kod FROM zb_st WHERE loopback = '{loopback}'")

    if status1 == 0 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔴 Филиал не доступен \nLoopback: {data[2]}\n{data[5]}\n" \
                   f"ISP_1: {data[3]}\n {data[6]}\nISP_2: {data[4]}"

            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 0, status_2 = 0 WHERE loopback = '{loopback}'")
            await sql.sql_insert(f"Update registrator SET down = 1 WHERE kod = '{kod}'")
            await send_mess(kod, text)
    elif status1 == 1 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🟢 🔴 Резервный провайдер не работает \n" \
                   f"Loopback: {data[2]}\n{data[6]}\nISP_2: {data[4]}"
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 1, status_2 = 0 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)

    elif status1 == 0 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🟢 Основной провайдер не работает\n\n" \
                   f"Loopback: {data[2]}\n{data[5]}\nISP_1: {data[3]}\n"
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 0, status_2 = 1 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)

    elif status1 == 1 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🟢 🟢 Филиал работает"
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 1, status_2 = 1 WHERE loopback = '{loopback}'")
            await send_mess(kod, text)
    else:
        pass


async def request_name(loopback):
    await asyncio.sleep(1)
    return await sql.sql_selectone(
        f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM zabbix WHERE loopback = '{loopback}'")


async def send_mess(kod, text, name=None, email=0):
    rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
    try:
        for row in rows:
            await asyncio.sleep(1)
            try:

                # await bot.send_message(chat_id=row, text=text, disable_notification=await notif())
                await bot.send_message(chat_id=765333440, text=text, disable_notification=await notif())
                print("sms")
                if email == 1:
                    print("email")
                    # await send_email(kod, text)
            except TypeError:
                print(f"Ошибка отправки {row}")
            except ChatNotFound:
                print(f"Юзер не найден {row}")

    except TypeError:
        print("Никто не подписан")


async def notif():
    H, M, S = datetime.now().strftime("%H:%M:%S").split(":")[0:3]
    time_min = time(20, 00)
    time_max = time(8, 00)
    time_old = time(int(H), int(M))
    if time_min < time_old > time_max:
        # print("Без звука")
        return True
    else:
        # print("Со звуком")
        return None

#
# def data_monitor():
#     return datetime.today().strftime("%H:%M:%S %d/%m/%Y")

#
# async def monitoring():
#     keyboard = InlineKeyboardMarkup()
#     i = 1
#     tab = []
#     column = []
#     request = f"SELECT filial.kod, status_1, status_2, ISP1, ISP2 FROM status " \
#               f"INNER JOIN filial ON status.kod = filial.kod ORDER BY status.kod"
#     rows = await sql.sql_select(request)
#     l = len(rows)
#     num,n = 0,0
#     while num < l:
#         num += 4
#         column.append(num)
#     for row in rows:
#         ch1 = "🔵"
#         ch2 = "🔵"
#         if row[1] == 1:
#             ch1 = "🔵"
#         elif row[1] == 0:
#             ch1 = "🔴"
#         if row[2] == 1:
#             ch2 = "🔵"
#         elif row[2] == 0:
#             ch2 = "🔴"
#         if row[3] == "unassigned":
#             ch1 = "⚪"
#         if row[4] == "unassigned":
#             ch2 = "⚪"
#         tab.append(InlineKeyboardButton(text=f"{ch1}{ch2}{row[0]} ", callback_data=f"sub_{row[0]}"))
#         if i in column:
#             keyboard.row(*tab)
#             tab = []
#             n += 1
#         if i == 100:
#             await edit_mess(keyboard, 1)
#             keyboard = InlineKeyboardMarkup()
#         i += 1
#     keyboard.row(*tab)
#     await edit_mess(keyboard, 2)
#
#
#
# async def edit_mess(keyboard, q):
#     chat = "@test_moni"
#     # chat = "@sdwan_monitoring"
#     text = "<---------------->\n Время проверки %s" % data_monitor()
#     try:
#         message_id = (await sql.sql_selectone(f"SELECT username FROM users WHERE id = 123456789 and first_name = 'mess_{q}'"))[0]
#         print(message_id)
#         await bot.edit_message_text(chat_id=chat, message_id=message_id, text=text, reply_markup=keyboard)
#     except Exception as n:
#         print(n)
#         id = await bot.send_message(chat_id=chat, text=text, reply_markup=keyboard)
#         await sql.sql_insert(f"UPDATE users SET username = {id.message_id} WHERE id = 123456789 and first_name = 'mess_{q}'")

# loop = asyncio.get_event_loop()
# loop.run_until_complete(monitoring())


# async def call_name(call):
#     kod = call.data.split("_")[1]
#     name = (await sql.sql_selectone(f"SELECT name FROM filial WHERE kod = {kod}"))[0]
#     try:
#         await bot.answer_callback_query(callback_query_id=call.id, text=f"{name}")
#     except Exception as n:
#         print(f"cal{n}")
