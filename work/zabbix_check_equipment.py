import aiosnmp
from work.sql import sql_select, sql_insert, sql_selectone
from sqlite3 import OperationalError
from aiosnmp.exceptions import SnmpTimeoutError
from pysnmp.hlapi import getCmd, SnmpEngine, UsmUserData, usmHMACSHAAuthProtocol, UdpTransportTarget, ContextData, \
    ObjectType, ObjectIdentity, CommunityData, bulkCmd


async def check_equipment():
    try:
        rows = await sql_select("select loopback, zabbix.kod, zabbix.name, sdwan from zabbix except "
                                "select loopback, registrator.kod, zabbix.name, sdwan from registrator "
                                "left join zabbix on registrator.kod = zabbix.kod")
    except OperationalError:
        await table_registrator()
        await check_equipment()
        await table_cisco()
        return
    for loopback, kod, name, sdwan in rows:
        if sdwan == 1:
            await sql_insert(f"DELETE FROM registrator WHERE kod = {kod}")
            await sql_insert(f"DELETE FROM cisco WHERE kod = {kod}")
            await cisco_registrator(loopback)
        elif sdwan == 0:
            try:
                await sql_insert(f"DELETE FROM registrator WHERE kod = {kod}")
                await sql_insert(f"DELETE FROM cisco WHERE kod = {kod}")
            except OperationalError:
                await mikrotik_cisco(loopback, kod)
                await mikrotik_registrator(loopback, kod)


async def cisco_registrator(loopback):
    row = await sql_selectone(f"SELECT vlan100, vlan400, vlan500, kod FROM zabbix WHERE loopback = '{loopback}'")
    vlan100, vlan400, vlan500, kod = row
    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in bulkCmd(SnmpEngine(),
                              UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
                                          authProtocol=usmHMACSHAAuthProtocol
                                          ),
                              UdpTransportTarget((loopback, 161)),
                              ContextData(),
                              10, 20,
                              ObjectType(ObjectIdentity('IP-MIB', 'ipNetToMediaNetAddress')),
                              lexicographicMode=False):
        if errorIndication:
            print(errorIndication)
            break
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            break
        else:
            for varBind in varBinds:
                #                    print(' = '.join([x.prettyPrint() for x in varBind]))
                ip = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
                #                    print(ip.split(".")[3])
                if ip == "No more variables left in this MIB View":
                    print("err1")
                elif 1 < int(ip.split(".")[3]) < 20:
                    if vlan100.split(".")[0:3] == ip.split(".")[0:3]:
                        if 1 < int(ip.split(".")[3]) < 10:
                            # await asyncio.sleep(1)
                            # print("cisco")
                            await snmp_cisco_v2(ip, kod)
                    elif vlan400.split(".")[0:3] == ip.split(".")[0:3]:
                        if 1 < int(ip.split(".")[3]) < 15:
                            # await asyncio.sleep(1)
                            await snmp_trassir(ip, kod)
                    elif vlan500.split(".")[0:3] == ip.split(".")[0:3]:
                        if 1 < int(ip.split(".")[3]) < 15:
                            # await asyncio.sleep(1)
                            await snmp_cisco_v2(ip, kod)
                else:
                    pass


async def snmp_cisco_v2(ip, kod):
    with aiosnmp.Snmp(host=ip, port=161, community="read", timeout=10, retries=2, max_repetitions=2, ) as snmp:
        try:
            for res in await snmp.get(".1.3.6.1.4.1.9.2.1.3.0"):
                name = res.value.decode('UTF-8')
                request = f"INSERT INTO cisco (kod, ip, hostname) VALUES ({kod}, '{ip}','{name}')"
                await sql_insert(request)
        except Exception as n:
            print(f"Ошибка_cisco {n}")


async def snmp_trassir(ip, kod):
    with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=10, retries=2, max_repetitions=2, ) as snmp:
        try:
            for res in await snmp.get("1.3.6.1.4.1.3333.1.7"):
                name = res.value.decode('UTF-8')
                request = f"INSERT INTO registrator (kod, ip, hostname) VALUES ({kod}, '{ip}','{name}')"
                await sql_insert(request)
        except SnmpTimeoutError:
            print("snmp_trassir_timeout ", ip)


async def mikrotik_cisco(ip, kod):
    with aiosnmp.Snmp(host=ip, port=161, community="public") as snmp:
        try:
            results = await snmp.bulk_walk(".1.3.6.1.2.1.4.22.1.3")
        except SnmpTimeoutError:
            return
        except TimeoutError:
            return
        for res in results:
            ip_old = str(res.value)
            if 1 < int(ip_old.split(".")[3]) < 20:
                ip_n = ip.split(".")[1:3]
                ip_cisco = f"10.{ip_n[0]}.{ip_n[1]}.0"
                if ip_cisco.split(".")[0:3] == ip_old.split(".")[0:3]:
                    try:
                        with aiosnmp.Snmp(host=ip_old, port=161, community="read") as snmp:
                            for res in await snmp.get(".1.3.6.1.4.1.9.2.1.3.0"):
                                name = res.value.decode('UTF-8')
                                if kod is not None:
                                    request = f"INSERT INTO cisco (kod, ip, hostname) VALUES ({kod}, '{ip_old}','{name}')"
                                    await sql_insert(request)
                    except SnmpTimeoutError:
                        pass


async def mikrotik_registrator(ip, kod):
    with aiosnmp.Snmp(host=ip, port=161, community="public") as snmp:
        try:
            results = await snmp.bulk_walk(".1.3.6.1.2.1.4.22.1.3")
        except SnmpTimeoutError:
            return
        for res in results:
            ip_old = str(res.value)
            if 1 < int(ip_old.split(".")[3]) < 20:
                ip_n = ip.split(".")[1:3]
                ip_reg = f"19.{ip_n[0]}.{ip_n[1]}.0"
                if ip_reg.split(".")[0:3] == ip_old.split(".")[0:3]:
                    try:
                        with aiosnmp.Snmp(host=ip_old, port=161, community="dssl") as snmp:
                            for res in await snmp.get("1.3.6.1.4.1.3333.1.7"):
                                try:
                                    name = res.value.decode('UTF-8')
                                except AttributeError:
                                    print('Скрипт не работает ', ip_old)
                                    return
                                if kod is not None:
                                    request = f"INSERT INTO registrator (kod, ip, hostname) VALUES ({kod}, '{ip_old}','{name}')"
                                    await sql_insert(request)
                    except SnmpTimeoutError:
                        pass


async def update_reg_cis(kod):
    loopback, sdwan = await sql_selectone(f"SELECT loopback, sdwan FROM zabbix WHERE kod = {kod}")
    if sdwan == 1:
        await sql_insert(f"DELETE FROM registrator WHERE kod = {kod}")
        await sql_insert(f"DELETE FROM cisco WHERE kod = {kod}")
        await cisco_registrator(loopback)
    elif sdwan == 0:
        await sql_insert(f"DELETE FROM registrator WHERE kod = {kod}")
        await sql_insert(f"DELETE FROM cisco WHERE kod = {kod}")
        await mikrotik_cisco(loopback, kod)
        await mikrotik_registrator(loopback, kod)


async def table_registrator():
    request = """CREATE TABLE registrator (
    kod      INT,
    ip       TEXT,
    hostname TEXT,
    disk     TEXT,
    archive  TEXT,
    cam      TEXT,
    cam_down TEXT,
    uptime   TEXT,
    firmware TEXT,
    script   TEXT,
    down     INT,
    ver_snmp TEXT
);"""
    await sql_insert(request)


async def table_cisco():
    request = """CREATE TABLE cisco (
    kod      INT,
    ip       TEXT,
    hostname TEXT
);"""
    await sql_insert(request)
