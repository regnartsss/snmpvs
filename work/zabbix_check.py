from work.sql import sql_select, sql_insert, sql_selectone
from pysnmp.hlapi import getCmd, SnmpEngine, UsmUserData, usmHMACSHAAuthProtocol, UdpTransportTarget, ContextData, \
    ObjectType, ObjectIdentity, CommunityData, bulkCmd
import aiosnmp
import paramiko
import os
import asyncio
from pyzabbix import ZabbixAPI
from sqlite3 import OperationalError
from loader import bot
import re
from work.zabbix_check_equipment import check_equipment
import logging


def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()


async def check():
    print("check")
    await check_zabbix()
    rows = await sql_select(f"SELECT loopback, sdwan FROM zabbix WHERE hostname is Null")
    for loopback, sdwan in rows:
        logging.info(f"zabb {loopback}")
        if sdwan == 1:
            hostname = await hostname_cisco(loopback)
            if hostname is not None:
                print("vlan_cisco")
                await vlan_cisco(loopback)
                print("isp_name_cisco")
                await isp_name_cisco(loopback)
                print("cisco_ssh_serial")
                await cisco_ssh_serial(loopback)
                print("end")
        elif sdwan == 0:
            await hostname_mikrotik(loopback)
    await check_equipment()
    print("end")
    return


async def hostname_cisco(loopback):
    errorIndication, errorStatus, errorIndex, varBinds = next(getCmd(SnmpEngine(),
                                                                     UsmUserData(userName='dvsnmp',
                                                                                 authKey='55GjnJwtPfk',
                                                                                 authProtocol=usmHMACSHAAuthProtocol),
                                                                     UdpTransportTarget((loopback, 161)),
                                                                     ContextData(),
                                                                     ObjectType(
                                                                         ObjectIdentity("1.3.6.1.2.1.1.5.0"))))
    for varBind in varBinds:
        sysName = ' = '.join([x.prettyPrint() for x in varBind])
        kod = sysName.split("= ")[1].split("-")[2]
        kod = re.findall(r'\d+', kod)
        hostname = [x.prettyPrint() for x in varBind][1]
        hostname = hostname.split(".")[0]
        request = f"UPDATE zabbix SET kod = '{kod[0]}', hostname = '{hostname}' WHERE loopback = '{loopback}'"
        await sql_insert(request)
        return hostname


async def hostname_mikrotik(ip):
    with aiosnmp.Snmp(host=ip, port=161, community="public", timeout=10, retries=2, max_repetitions=2, ) as snmp:
        try:
            for res in await snmp.get("1.3.6.1.2.1.1.5.0"):
                hostname = res.value.decode('UTF-8')
                request = f"UPDATE zabbix SET hostname = '{hostname}' WHERE loopback = '{ip}'"
                await sql_insert(request)
                return hostname
        except aiosnmp.exceptions.SnmpTimeoutError:
            return None


async def vlan_cisco(loopback):
    command = "sh ip int br"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    data = {}
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    open(PATH + 'leas.txt', 'wb').write(f)
    await asyncio.sleep(1)
    with open(PATH + 'leas.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() != []:
                line.split()
                try:
                    if line.split()[0] == 'Tunnel0':
                        data["ISP1"] = line.split()[1]
                    elif line.split()[0] == 'Tunnel1':
                        data["ISP2"] = line.split()[1]
                    elif line.split()[0] == 'Loopback0':
                        data["loopback"] = line.split()[1]
                    elif line.split()[0] == 'Vlan100':
                        if line.split()[1].split(".")[0] == "169":
                            data["Vlan100"] = "null"
                        else:
                            data["Vlan100"] = line.split()[1]
                    elif line.split()[0] == 'Vlan200':
                        if line.split()[1].split(".")[0] == "169":
                            data["Vlan200"] = "null"
                        else:
                            data["Vlan200"] = line.split()[1]
                    elif line.split()[0] == 'Vlan300':
                        if line.split()[1].split(".")[0] == "169":
                            data["Vlan300"] = "null"
                        else:
                            data["Vlan300"] = line.split()[1]
                    elif line.split()[0] == 'Vlan400':
                        if line.split()[1].split(".")[0] == "169":
                            data["Vlan400"] = "null"
                        else:
                            data["Vlan400"] = line.split()[1]
                    elif line.split()[0] == 'Vlan500':
                        if line.split()[1].split(".")[0] == "169":
                            data["Vlan500"] = "null"
                        else:
                            data["Vlan500"] = line.split()[1]
                except Exception as n:
                    print(n)
    command = "show ip route"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    print("test_3")
    open(PATH + 'g.txt', 'wb').write(f)
    await asyncio.sleep(1)
    isp_1, isp_2 = "0.0.0.0", "0.0.0.0"
    with open(PATH + 'g.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() == []:
                pass
            else:
                if line.split()[0] == 'S*':
                    isp_1 = line.split()[4]
                elif line.split()[0] == '[1/0]':
                    isp_2 = line.split()[2]

    data["gateway_isp1"] = "0.0.0.0"
    data["gateway_isp2"] = "0.0.0.0"

    try:
        if data["ISP1"].split(".")[0:2] == isp_1.split(".")[0:2]:
            data["gateway_isp1"] = isp_1
        elif data["ISP1"].split(".")[0:2] == isp_2.split(".")[0:2]:
            data["gateway_isp1"] = isp_2

        if data["ISP2"].split(".")[0:2] == isp_2.split(".")[0:2]:
            data["gateway_isp2"] = isp_2
        elif data["ISP2"].split(".")[0:2] == isp_1.split(".")[0:2]:
            data["gateway_isp2"] = isp_1
    except:
        print("Ошибка шлюза")
        pass

    request = f"UPDATE zabbix SET ISP1 = '{data['ISP1']}', ISP2 = '{data['ISP2']}', vlan100 = '{data['Vlan100']}', " \
              f"vlan200 = '{data['Vlan200']}', vlan300 = '{data['Vlan300']}', vlan400 = '{data['Vlan400']}', " \
              f"vlan500 = '{data['Vlan500']}', gateway_isp1 = '{data['gateway_isp1']}', gateway_isp2 = '{data['gateway_isp2']}' WHERE loopback = '{loopback}'"
    await sql_insert(request)


async def isp_name_cisco(loopback):
    command = "sh int GigabitEthernet0/0/0 "
    user = 'operator'
    secret = '71LtkJnrYjn'
    kod = "537"
    port = 22
    data = {}
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    open(PATH + 'n.txt', 'wb').write(f)
    await asyncio.sleep(1)
    with open(PATH + 'n.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() != []:
                if line.split()[0] == "Description:":
                    data["ISP1_NAME"] = line.split()[1]
    command = "sh int GigabitEthernet0/0/1 "
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    open(PATH + 'n.txt', 'wb').write(f)
    await asyncio.sleep(1)
    with open(PATH + 'n.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() != []:
                if line.split()[0] == "Description:":
                    data["ISP2_NAME"] = line.split()[1]
    request = f"UPDATE zabbix SET isp1_name = '{data['ISP1_NAME']}', isp2_name = '{data['ISP2_NAME']}'  " \
              f"WHERE loopback = '{loopback}'"
    await sql_insert(request)


async def cisco_ssh_serial(loopback):
    command = "show ver"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    open(PATH + 'serial.txt', 'wb').write(f)
    await asyncio.sleep(1)
    with open(PATH + 'serial.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() != []:
                if line.split()[0] == "Processor":
                    request = f"UPDATE zabbix SET serial = '{line.split()[3]}' WHERE loopback = '{loopback}'"
                    await sql_insert(request)


async def check_zabbix():
    import urllib3
    urllib3.disable_warnings()

    user = "podkopaev.k"
    password = "z15X3vdy"
    z = ZabbixAPI('https://zabbix.partner.ru/')
    z.session.auth = (user, password)
    z.session.verify = False
    z.timeout = 5.1
    z.login(user=user, password=password)
    print("Connected to Zabbix API Version %s" % z.api_version())
    try:
        rows = await sql_select("SELECT name, loopback FROM zabbix")
    except OperationalError:
        await new_table_zabbix()
        rows = await sql_select("SELECT name, loopback FROM zabbix")
    hrows, frows = [], []
    all_r, all_f = {}, {}
    for row in rows:
        frows.append(row[0])
        all_f[row[0]] = row[1]

    for h in z.host.get():
        hrows.append(h['name'])
        all_r[h['name']] = h['host']
    delete = ['dv-gw-cisco', 'ural-dc1', 'ural-gw-cisco', 'mow-gw-cisco', 'dv-dc1', 'adm-dipex-gw-cisco', 'dv-dc2']
    result = list(set(hrows) - set(frows) - set(delete))
    for h in result:
        text = f"Добавлен в базу {h} - {all_r[h]}"
        await bot.send_message(chat_id=765333440, text=text)
        await asyncio.sleep(2)
        if '.'.join(all_r[h].split(".")[0:2]) == "10.255":
            sdwan = 1
        else:
            sdwan = 0
        await sql_insert(f"INSERT INTO zabbix (loopback, name, sdwan) VALUES ('{all_r[h]}', '{h}', {sdwan})")
        await sql_insert(f"UPDATE zabbix SET kod = (SELECT kod FROM data_full WHERE name = '{h}') WHERE name = '{h}'")

    for key, value in all_r.items():
        for key_old, value_old in all_f.items():
            if key == key_old:
                if value != value_old:
                    text = f"Филиал {key}. Замена микротика {value_old} на циску {value}"
                    await bot.send_message(chat_id=765333440, text=text)
                    logging.info(f"DELETE FROM zabbix WHERE loopback = '{value_old}'")
                    await sql_insert(f"DELETE FROM zabbix WHERE loopback = '{value_old}'")
                    logging.info(f"DELETE FROM zb_st WHERE loopback = '{value_old}'")
                    await sql_insert(f"DELETE FROM zb_st WHERE loopback = '{value_old}'")
                    logging.info(f"INSERT INTO zabbix (loopback, name, sdwan) VALUES ('{value}', '{key}', 1)")
                    await sql_insert(f"INSERT INTO zabbix (loopback, name, sdwan) VALUES ('{value}', '{key}', 1)")
    try:
        await sql_insert("DELETE FROM zb_region")
    except OperationalError:
        await new_table_zb_region()

    for h in z.hostgroup.get():
        id = h['groupid']
        name = h['name'].split("/")[-1]
        if h['name'].split("/")[-1][0] != "-":
            if name[0:3] == "див" or name == 'Восточная Сибирь':
                await sql_insert(f"INSERT INTO zb_region (id, id_monitor, name) VALUES ({id}, 999, '{name}')")
            else:
                await sql_insert(f"INSERT INTO zb_region (id, id_monitor, name) VALUES ({id}, {id}, '{name}')")
            for x in z.host.get(groupids=h['groupid']):
                if x['host'][0:2] == '10':
                    # print(x['name'])
                    if name[0:3] == "див" or name == 'Восточная Сибирь':
                        await sql_insert(f"UPDATE zabbix SET region = {id}, region_mon = 999 WHERE loopback = '{x['host']}'")
                    elif x['name'][0:3] == "Адм" or x['name'][0:3] == "РРС":
                        await sql_insert(f"UPDATE zabbix SET region = 256, region_mon = 999 WHERE loopback = '{x['host']}'")

                    else:
                        await sql_insert(f"UPDATE zabbix SET region = {id}, region_mon = {id} WHERE loopback = '{x['host']}'")


async def update_vlan(kod):
    loopback = await sql_selectone(f"SELECT loopback FROM zabbix WHERE kod = {kod}")
    # print(f"DELETE FROM zb_st WHERE kod = {kod}")
    await sql_insert(f"DELETE FROM zb_st WHERE kod = {kod}")
    await vlan_cisco(loopback[0])




async def new_table_zb_region():
    await sql_insert("""CREATE TABLE zb_region (id      INT, name TEXT, id_monitor, INT);""")


async def new_table_zabbix():
    await sql_insert("""CREATE TABLE zabbix (
                                                      kod          INT,
    loopback     TEXT,
    name         TEXT,
    region       INT,    
    hostname     TEXT,
    ISP1         TEXT,
    ISP2         TEXT,
    vlan100      TEXT,
    vlan200      TEXT,
    vlan300      TEXT,
    vlan400      TEXT,
    vlan500      TEXT,
    isp1_name    TEXT,
    isp2_name    TEXT,
    gateway_isp1 TEXT,
    gateway_isp2 TEXT,
    serial       TEXT,
    sdwan        INT,
    region_mon    INT,
    work        INT
                                                  );"""
                     )
