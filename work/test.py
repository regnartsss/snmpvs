import paramiko
from work.sql import sql_select, sql_insert, sql_selectone
from sqlite3 import OperationalError
from pyzabbix import ZabbixAPI
import aioping
import time
#
# async def scanning_cisco():
#     request = f"SELECT ip, hostname FROM cisco"
#     user = "itkras"
#     passwors = "miccis-96kraS"
#     # command = "sh port add"
#     command = "show mac address-table"
#     rows = await sql_select(request)
#     for row in rows:
#         ip = row[0]
#         client = paramiko.SSHClient()
#         client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         try:
#             client.connect(hostname=ip, username=user, password=passwors, port=22)
#         except paramiko.ssh_exception.NoValidConnectionsError:
#             print(f"🔴 Нет подключения к циско {ip}")
#             # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
#             continue
#         except paramiko.ssh_exception.AuthenticationException:
#             print(f"🔴 Не верный пароль к циско {ip}")
#             # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
#             continue
#         except TimeoutError:
#             print(f"🔴 Нет подключения к циско {ip}")
#             # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
#             continue
#         stdin, stdout, stderr = client.exec_command(command)
#         text = stdout.read().decode("utf-8").split("\r\n")
#         for line in text:
#             try:
#                 line.split()[3]
#             except IndexError:
#                 continue
#             count_vlan = (await sql_selectone(f"SELECT count(ip) FROM cisco_vlan WHERE ip = '{ip}'"))[0]
#             if count_vlan == 0:
#                 await sql_insert(f"INSERT INTO cisco_vlan (ip) VALUES ('{ip}')")
#             count_mac = (await sql_selectone(f"SELECT count(ip) FROM cisco_mac WHERE ip = '{ip}'"))[0]
#             if count_mac == 0:
#                 await sql_insert(f"INSERT INTO cisco_mac (ip) VALUES ('{ip}')")
#             if line.split()[2] == "STATIC":
#                 if line.split()[3] != "CPU":
#                     mac_old = line.split()[1]
#                     mac_old = f"{mac_old.split('.')[0]}{mac_old.split('.')[1]}{mac_old.split('.')[2]}"
#                     try:
#                         await sql_insert(f"UPDATE cisco_vlan SET '{line.split()[3]}' = '{line.split()[0]}' WHERE ip = '{ip}'")
#                         await sql_insert(f"UPDATE cisco_mac SET '{line.split()[3]}' = '{mac_old}' WHERE ip = '{ip}'")
#                     except OperationalError as n:
#                         if str(n).split(":")[0] == "no such column":
#                             await sql_insert(f"ALTER TABLE cisco_vlan ADD '{line.split()[3]}' text")
#                             await sql_insert(f"ALTER TABLE cisco_mac ADD '{line.split()[3]}' text")
#                             await sql_insert(
#                                 f"UPDATE cisco_vlan SET '{line.split()[3]}' = '{line.split()[0]}' WHERE ip = '{ip}'")
#                             await sql_insert(
#                                 f"UPDATE cisco_mac SET '{line.split()[3]}' = '{mac_old}' WHERE ip = '{ip}'")
status_old = -1

async def test():
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
    data = {}

    while True:
        for h in z.host.get():
            # print(h)
            for f in z.problem.get(hostids=h['hostid'], severities=[4, 5], recent=True):
                # print(f)
            # print(f['name'], f['acknowledged'], f['suppressed'])
                await check(f['name'], f['r_eventid'], h['name'], h['host'])
        print("-----------------------")
        time.sleep(60)


    #         try:
    #             data[h['name']].append(f['name'])
    #         except KeyError:
    #             data[h['name']]=[]
    #             data[h['name']].append(f['name'])
    # for key, value in data.items():
    #     print(key)
    #     print(value)
    #     if len(value) > 1:
    #         for v in value:
    #             await check(v)
    #             # row = await sql_selectone(f"SELECT loopback FROM zabbix WHERE name = '{key}'")
    #     else:
    #         await check(value[0])


            # row = await sql_selectone(f"SELECT loopback FROM zabbix WHERE name = '{key}'")


async def check(error, done, name, loopback):
    status_old = await sql_selectone(f"SELECT Provider1, Provider2 FROM zb_st_new WHERE loopback = '{loopback}'")
    if status_old is None or status_old == []:
        await sql_insert(f"INSERT INTO zb_st_new (loopback, Provider1, Provider2) VALUES ('{loopback}', -1, -1)")
        status_old = [-1, -1]

    if "Provider 1 недоступен" in error or "(Tu0) недоступен" in error:
        if done == '0':
            if status_old[0] != 0:
                print(f'{name} Основной провайдер не доступен')
                await sql_insert(f"UPDATE zb_st_new SET Provider1 = 0 WHERE loopback = '{loopback}'")
        else:
            if status_old[0] != 1:
                print(f'{name} Основной провайдер работает')
                await sql_insert(f"UPDATE zb_st_new SET Provider1 = 1 WHERE loopback = '{loopback}'")
    elif 'Provider 2 недоступен' in error or "(Tu1) недоступен" in error:
        if done == '0':
            if status_old[1] != 0:
                print(f'{name} Резервный провайдер не доступен')
                await sql_insert(f"UPDATE zb_st_new SET  Provider2 = 0 WHERE loopback = '{loopback}'")
        else:
            if status_old[1] != 1:
                print(f'{name} Резервный провайдер работает')
                await sql_insert(f"UPDATE zb_st_new SET Provider2 = 1 WHERE loopback = '{loopback}'")
    elif "Филиал недоступен" in error or "no SNMP data" in error:
        if done == '0':
            if status_old[0] != 0 or status_old[1] != 0:
                print(f'{name} Филиал не доступен')
                await sql_insert(f"UPDATE zb_st_new SET Provider1 = 0, Provider2 = 0 WHERE loopback = '{loopback}'")
        else:
            if status_old[0] != 1 or status_old[1] != 1:
                print(f'{name} Филиал работает')
                await sql_insert(f"UPDATE zb_st_new SET Provider1 = 1, Provider2 = 1 WHERE loopback = '{loopback}'")
        # print("st 2 down")
    elif "Temperature" in error:
        pass

    # elif "rou1" in error:
    #     pass
    #     # print("st_rou 1 down")
    # elif 'rou2' in error:
    #     pass
    #     # print("st_rou 2 down")
    # elif "Gi0/0/0" in error and "Link down" in error:
    #     pass
    #     # print("Gi0/0/0 Link down")
    # elif "Gi0/0/1" in error and "Link down" in error:
    #     pass
    #     # print("Gi0/0/1 Link down")
    # elif "Tu0()" in error and "Link down" in error:
    #     pass
    #     # print("Tu0() Link down")
    # elif "Tu1()" in error and "Link down" in error:
    #     pass
    #     # print("Tu1() Link down")
    # elif "(Tu0) недоступен" in error:
    #     pass
    #     # print("tu0", error)
    # elif "(Tu1) недоступен" in error:
    #     pass
    #     # print("tu1", error)
    else:
        print("не найден",loopback, name, error)

