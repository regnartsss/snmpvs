from pysnmp.hlapi import *
from datetime import datetime, time
from work import sql
from loader import bot
import asyncio
import aiosnmp
from aiogram.utils.exceptions import ChatNotFound
from sqlite3 import OperationalError
from aiosnmp.asn1 import Error
import aioping
import logging
from aiogram.utils.exceptions import NetworkError, BotBlocked
from data.config import channel_mess
p = 0


async def start_snmp(data):
    await asyncio.sleep(10)
    i, y, z = 0, 0, 0
    while True:
        logging.info(f"start_cisco {i}")
        rows = await sql.sql_select(f"SELECT loopback, kod, sdwan FROM zabbix WHERE work is Null or work = 0 ORDER BY kod {data}")
        for loopback, kod, sdwan in rows:
            # logging.info(f"snmp {loopback}")
            request = f"SELECT count(loopback) FROM zb_st WHERE loopback = '{loopback}'"
            count = (await sql.sql_selectone(request))[0]
            if sdwan == 1:
                try:
                    if count == 0:
                        # logging.info(f"oid {y} {loopback}")
                        y += 1
                        await oid(loopback, kod)
                    else:
                        # logging.info(f"snmp {z} {loopback}")
                        z += 1
                        await snmp(loopback, kod, 0)

                except OperationalError:
                    await new_table_zb_st()
            elif sdwan == 0:
                try:
                    if count == 0:
                        await oid_mikrotik(loopback, kod)
                    else:
                        # logging.info(f"snmp mikrotik {z} {loopback}")
                        await check_snmp(loopback)
                except OperationalError:
                    await new_table_zb_st()
            else:
                print("Ошибка")
        i += 1

async def start_snmp_operstatus():
    i = 0
    while i < 2:
        rows = await sql.sql_select(f"SELECT loopback, kod, sdwan FROM zabbix WHERE sdwan = 1")
        for loopback, kod, sdwan in rows:
            if sdwan == 1:
                # logging.info(f"operstatus {loopback}")

                await snmp_operstatus(loopback)
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
    except TypeError:
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
        try:
            with aiosnmp.Snmp(host=ip, port=161, community="public") as s:
                for res in await s.get(f"{mib}{mib_old}"):
                    status.append(res.value)
        except Error as n:
            logging.info(f"snmp_mikrotik_1 {ip} {n}")
            # return await ping_mikrotik(ip)
            # return [2, 2]
            continue
        except aiosnmp.exceptions.SnmpTimeoutError as n:
            logging.info(f"snmp_mikrotik_2 {ip} {n}")
            # return await ping_mikrotik(ip)
            # return [2, 2]
            status.append(2)
        except TimeoutError as n:
            logging.info(f"snmp_mikrotik_3 {ip} {n}")
            continue
        except Exception as n:
            logging.info(f"snmp_mikrotik_4 {ip} {n}")
            continue
    return status


# async def ping_mikrotik(host):
#     try:
#         delay = await aioping.ping(host) * 1000
#         print("Ping response in %s ms" % delay)
#         await snmp_mikrotik(host)
#     except TimeoutError:
#         print("Timed out ", host)
#         return [2, 2]


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
    in_isp1, Oper_isp1, in_isp2, Oper_isp2, Oper_tu1, Oper_tu2, OperISP2 = "0", "0", "0", "0", "0", "0", "0"
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
                # print(error_indication)
                break
            elif error_status:
                print('%s at %s' % (error_status.prettyPrint(),
                                    error_index and var_binds[int(error_index) - 1][0] or '?'))
            else:
                for varBind in var_binds:
                    oi = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                    if oi == "Tu0":
                        num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                        in_isp1 = f"1.3.6.1.2.1.31.1.1.1.6.{num_oid.strip()}"
                        Oper_tu1 = f"1.3.6.1.2.1.2.2.1.8.{num_oid.strip()}"
                    elif oi == "Tu1":
                        num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                        in_isp2 = f"1.3.6.1.2.1.31.1.1.1.6.{num_oid.strip()}"
                        Oper_tu2 = f"1.3.6.1.2.1.2.2.1.8.{num_oid.strip()}"
                        Oper_isp2 = "1.3.6.1.2.1.2.2.1.8.2"
                    else:
                        pass
        await sql.sql_insert(
        f"UPDATE zb_st SET In_isp1 = '{in_isp1}', Oper_isp1 = '{Oper_tu1}', "
        f"In_isp2 = '{in_isp2}', Oper_isp2 ='{Oper_tu2}', OperISP2 = '{Oper_isp2}' WHERE loopback = '{loopback}'")


# async def ping_cisco(loopback, kod):
#     global p
#     logging.info(f"ping {p} {loopback}")
#     p += 1
#     try:
#         await aioping.ping(loopback)
#         await oid(loopback, kod, 1)
#     except TimeoutError:
#         pass
#
#
# async def ping_cisco_old(loopback, kod):
#     global p
#     logging.info(f"ping {p} {loopback}")
#     p += 1
#     try:
#         await aioping.ping(loopback, 100)
#         await snmp(loopback, kod)
#     except TimeoutError:
#         return False


async def snmp(loopback, kod, repeat):
    # logging.info(f"snmp {loopback} {repeat}")
    mib_all = await sql.sql_selectone(
        f"SELECT In_isp1, In_isp2, Oper_isp1, Oper_isp2, OperISP2 FROM zb_st WHERE loopback = '{loopback}'")
    if mib_all[0:2] == ('0', '0') or mib_all[0:2] == (None, None):
        logging.info(f"{loopback} oid не найден")
        await oid(loopback, kod, 1)

    else:
        d, op1, op2, st_op2 = [], '0', '0', '0'
        for errorIndication, errorStatus, \
            errorIndex, varBinds in bulkCmd(
            SnmpEngine(),
            UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
            UdpTransportTarget((str(loopback), 161)),
            ContextData(),
            0, 100,  # GETBULK specific: request up to 50 OIDs in a single response
            ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6')),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8')),
            lexicographicMode=False
        ):
            if errorIndication:
                # print(repeat)
                if repeat == 0:
                    # print('repeat')
                    repeat = 1
                    await asyncio.sleep(5)
                    await snmp(loopback, kod, 1)
                # # if await ping_cisco_old(loopback, kod) is False:
                # #     logging.info(f"{loopback} не доступен")
                # elif repeat == 1:
                #     print("столп")
                else:
                    r = await sql.sql_selectone(f"SELECT In1_two, In2_two FROM zb_st WHERE loopback = '{loopback}'")
                    d.append(r[0])
                    d.append(r[1])
                    break

            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                break
            else:
                for varBind in varBinds:
                    data = [x.prettyPrint() for x in varBind]
                    oid_d = '.'.join(data[0].split(".")[5:7])
                    try:
                        In_isp1 = '.'.join(mib_all[0].split(".")[10:12]).strip()
                        In_isp2 = '.'.join(mib_all[1].split(".")[10:12]).strip()
                        Oper1 = '.'.join(mib_all[2].split(".")[10:12]).strip()
                        Oper2 = '.'.join(mib_all[3].split(".")[10:12]).strip()
                        status_oper1 = '.'.join(mib_all[4].split(".")[10:12]).strip()
                        if In_isp1 == oid_d:
                            d.append(data[1])
                        if In_isp2 == oid_d:
                            d.append(data[1])
                        if Oper1 == oid_d:
                            op1 = data[1]
                        if Oper2 == oid_d:
                            op2 = data[1]
                        if status_oper1 == oid_d:
                            st_op2 = data[1]
                    except AttributeError as n:
                        print(n)

        try:
            request = f"UPDATE zb_st SET In1_one = In1_two, In2_one = In2_two, In1_two = {d[0]}, In2_two = {d[1]}, " \
                      f"Oper1 = {op1}, Oper2 = {op2}, status_operisp2 = {st_op2} WHERE loopback = '{loopback}'"
            await sql.sql_insert(request)
            await check_cisco(loopback)
        except Exception as n:
            print("Cis_errr", n)
            pass
    # if mib_all[0:4] == ('0', '0', '0', '0') or mib_all[0:4] == (None, None, None, None):
    #     # print("Нет oid, проверить", loopback, kod)
    #     if await ping_cisco(loopback, kod) is False:
    #         return
    # d = []
    # logging.info(f"snmp_{mib_all}")
    # for mib in mib_all:
    #     error_indication, error_status, error_index, var_binds = await snmp_v3(loopback, mib)
    #     logging.info("snmp_v3_start")
    #     if error_indication:
    #         if await ping_cisco_old(loopback, kod) is False:
    #             print(loopback, "Не доступен")
    #             print(error_indication)
    #             r = await sql.sql_selectone(f"SELECT In1_two, In2_two FROM zb_st WHERE loopback = '{loopback}'")
    #             d.append(r[0])
    #             d.append(r[1])
    #             return
    #     elif error_status:
    #         print("error")
    #         print(loopback)
    #         print('%s at %s' % (error_status.prettyPrint(),
    #                             error_index and var_binds[int(error_index) - 1][0] or '?'))
    #     else:
    #         for varBind in var_binds:
    #             #                print(' = '.join([x.prettyPrint() for x in varBind]))
    #             m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
    #             d.append(m)


async def snmp_operstatus(loopback):
    # mib_all = await sql.sql_selectone(f"SELECT Oper_isp1, Oper_isp2, OperISP2 FROM zb_st WHERE loopback = '{loopback}'")
    # d = []

    for errorIndication, errorStatus, errorIndex, varBinds in bulkCmd(
            SnmpEngine(),
            UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
            UdpTransportTarget((loopback, 161)),
            ContextData(),
            0, 20,  # GETBULK specific: request up to 50 OIDs in a single response
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8.2')),
            lexicographicMode=False
    ):
        if errorIndication:
            print(errorIndication)
            return
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                data = [x.prettyPrint() for x in varBind]
                print(data)
    #         oid = '.'.join(data[0].split(".")[5:7])
    #         In_isp1 = '.'.join(mib_all[0].split(".")[10:12]).strip()
    #         In_isp2 = '.'.join(mib_all[1].split(".")[10:12]).strip()
    #         if In_isp1 == oid:
    #             d.append(data[1])
    #         if In_isp2 == oid:
    #             d.append(data[1])
    # try:
    #     request = f"UPDATE zb_st SET In1_one = In1_two, In2_one = In2_two, In1_two = {d[0]}, In2_two = {d[1]} " \
    #               f" WHERE loopback = '{loopback}'"
    #     await sql.sql_insert(request)
    #     await check_cisco(loopback)
    # except Exception as n:
    #     print("Cis_errr", n)
    #     pass


async def snmp_v3(loopback, mib):
    '1.3.6.1.2.1.1.3.0'
    logging.info("snmp_v3_start")
    error_indication, error_status, error_index, var_binds = next(
        getCmd(SnmpEngine(),
               UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
               UdpTransportTarget((str(loopback), 161)),
               ContextData(),
               ObjectType(ObjectIdentity(mib)))
    )
    if error_indication:
        print(error_indication)
    elif error_status:
        print("error")
        print('%s at %s' % (error_status.prettyPrint(),
                            error_index and var_binds[int(error_index) - 1][0] or '?'))
    else:
        for varBind in var_binds:
            m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
            seconds = int(m[:-2])
            return await format_seconds_to_hhmmss(seconds)


async def format_seconds_to_hhmmss(seconds):
    day = seconds // (60 * 60 * 24)
    seconds %= (60 * 60 * 24)
    hours = seconds // (60 * 60)
    seconds %= (60 * 60)
    minutes = seconds // 60
    seconds %= 60
    return "%02id %02ih %02im %02is" % (day, hours, minutes, seconds)


async def check_cisco(loopback):
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
            await send_mess(kod, text, 0)
    elif status1 == 1 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🟢 🔴 Резервный провайдер не работает \n" \
                   f"Loopback: {data[2]}\n{data[6]}\nISP_2: {data[4]}\nUptime: "
            uptime = await snmp_v3(loopback, '1.3.6.1.2.1.1.3.0')
            text +=  str(uptime)
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 1, status_2 = 0, uptime = '{uptime}' WHERE loopback = '{loopback}'")
            await send_mess(kod, text, 0)
    elif status1 == 0 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🟢 Основной провайдер не работает\n\n" \
                   f"Loopback: {data[2]}\n{data[5]}\nISP_1: {data[3]}\nUptime: "
            uptime = await snmp_v3(loopback, '1.3.6.1.2.1.1.3.0')
            text += str(uptime)
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 0, status_2 = 1, uptime = '{uptime}' WHERE loopback = '{loopback}'")
            await send_mess(kod, text, 0)
    elif status1 == 1 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await request_name(loopback)
            text = f"{data[0]}\nКод: {data[1]}\n🟢 🟢 Филиал работает\nUptime: "
            uptime = await snmp_v3(loopback, '1.3.6.1.2.1.1.3.0')
            text +=  str(uptime)
            await sql.sql_insert(f"UPDATE zb_st SET status_1 = 1, status_2 = 1, uptime = '{uptime}' WHERE loopback = '{loopback}'")
            await send_mess(kod, text, 0)
    else:
        pass


async def request_name(loopback):
    await asyncio.sleep(1)
    return await sql.sql_selectone(
        f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM zabbix WHERE loopback = '{loopback}'")


async def send_mess(kod, text, data=1, email=0):
    if channel_mess == 0:
        if data == 0:
            await bot.send_message(chat_id='@sdwan_log', text=text, disable_notification=True)
        rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
        try:
            for row in rows:
                await asyncio.sleep(1)
                try:
                    try:
                        await bot.send_message(chat_id=row, text=text, disable_notification=await notif())
                    except NetworkError:
                        logging.info(f"Ошибка подключения к серверу телеграм")
                except TypeError:
                    print(f"Ошибка отправки {row}")
                except ChatNotFound:
                    print(f"Юзер не найден {row}")
                except BotBlocked:
                    print(f"Юзер заблокировал {row}")
        except TypeError:
            print("Никто не подписан ", kod)


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
