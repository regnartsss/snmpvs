from pysnmp.hlapi import getCmd, SnmpEngine, UsmUserData, usmHMACSHAAuthProtocol, UdpTransportTarget, ContextData, \
    ObjectType, ObjectIdentity, CommunityData, bulkCmd
from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql
import paramiko
import os
import time
from loader import bot
import asyncio
import aiosnmp
# import aioping


def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()


class NewFilial(StatesGroup):
    loopback = State()
    name = State()
    region = State()


class Add_snmp():
    def __init__(self, message, data):
        print(data)
        self.loopback = data['loopback']
        self.name = data['name']
        self.region = data['region']
        try:
            self.kod = data['kod']
        except KeyError:
            pass

    # Начальная информация о филиале
    async def snmp_sysName(self):
            print(self.loopback)
            old = self.loopback.split(".")[1:2]
            if old[0] == '255':
                print("cisco")
                await self.cisco()
                return self.kod
            else:
                print("mikorik")
                await self.mikrotik()
                return self.kod
        #     request = f"SELECT sdwan FROM filial WHERE loopback = '{self.loopback}'"
        #     print(request)
        #     sdwan = (await sql.sql_selectone(request))[0]
        #     print(sdwan)
        # except TypeError:
        #     request = f"INSERT INTO filial (kod, loopback, name, region) VALUES ({self.kod},'{self.loopback}','{self.name}',(SELECT id FROM region WHERE name = '{self.region}'))"
        #     await sql.sql_insert(request)
        #     return f"Проверьте поле sdwan {self.kod} {self.loopback}"
        #     # await bot.send_message(chat_id=765333440, text=f"Проверьте поле sdwan {self.kod} {self.loopback}")
        #     # return
        # else:
        #     print("всё ок")
        #     if sdwan == 1:
        #         print("Проверка cisco")

        #     else:
        #         print("Проверка микротика")
        #         await self.mikrotik()
        #         return self.kod

    async def cisco(self):
        print("Hostname")
        sysName = "None"
        errorIndication, errorStatus, errorIndex, varBinds = next(getCmd(SnmpEngine(),
                                                                         UsmUserData(userName='dvsnmp',
                                                                                     authKey='55GjnJwtPfk',
                                                                                     authProtocol=usmHMACSHAAuthProtocol),
                                                                         UdpTransportTarget((self.loopback, 161)),
                                                                         ContextData(),
                                                                         ObjectType(
                                                                             ObjectIdentity("1.3.6.1.2.1.1.5.0"))))
        for varBind in varBinds:
            sysName = ' = '.join([x.prettyPrint() for x in varBind])
            # print(sysName)
        try:
            self.kod = sysName.split("= ")[1].split("-")[2]
            try:
                self.kod = self.kod.split(".")[0]
            except Exception as n:
                print(f"Удаление старого филиала {self.kod}")
            try:
                request = f"DELETE FROM filial WHERE kod = {self.kod}"
                print(request)
                await sql.sql_insert(request)
            except Exception as n:
                print(self.kod)
                await bot.send_message(chat_id=765333440, text=f"Удаление старого филиала {self.kod} - {n}")
        except IndexError:
            return "Ошибка в loopback или адрес не доступен"

        # try:
        #     self.kod = self.kod.split(".")[0]
        # except Exception as n:
        #     self.kod = self.kod
        try:
            hostname = sysName.split("= ")[1].split(".")[0]
        except Exception as n:
            print(n)
            hostname = sysName.split("= ")[1]

        request = f"INSERT INTO filial (kod, loopback, name, region, hostname, sdwan) VALUES ({self.kod},'{self.loopback}','{self.name}', (SELECT id FROM region WHERE name = '{self.region}'), '{hostname}', 1)"
        await sql.sql_insert(request)
        # print("Получаем все айпи на интерфейса")
        ip = await self.ssh_ip_int()
        serial = await self.ssh_serial()
        request = f"UPDATE filial  SET ISP1 = '{ip['ISP1']}', ISP2 = '{ip['ISP2']}', vlan100 = '{ip['Vlan100']}', " \
                  f"vlan200 = '{ip['Vlan200']}', vlan300 = '{ip['Vlan300']}', vlan400 = '{ip['Vlan400']}', " \
                  f"vlan500 = '{ip['Vlan500']}', gateway_isp1 = '{ip['gateway_isp1']}', gateway_isp2 = '{ip['gateway_isp2']}', serial = '{serial}', sdwan = 1 WHERE kod = {self.kod}"
        await sql.sql_insert(request)
        for k, v in ip['registrator'].items():
            request = f"INSERT INTO registrator (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
            await sql.sql_insert(request)
        for k, v in ip['cisco'].items():
            request = f"INSERT INTO cisco (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
            await sql.sql_insert(request)

        # print("Получаем description провайдера")
        isp_name = await self.ssh_sh_int()
        await sql.sql_insert(f"UPDATE filial "
                             f"SET isp1_name = '{isp_name['ISP1_NAME']}', isp2_name = '{isp_name['ISP2_NAME']}' "
                             f"WHERE kod = {self.kod}")
        # print("Получаем шлюз провайдера")

    async def mikrotik(self):
        request = f"DELETE FROM filial WHERE kod = {self.kod}"
        print(request)
        await sql.sql_insert(request)
        hostname = await self.mikrotik_hostname()
        request = f"INSERT INTO filial (kod, loopback, name, region, hostname, sdwan) VALUES ({self.kod},'{self.loopback}','{self.name}', (SELECT id FROM region WHERE name = '{self.region}'), '{hostname}', 0)"
        await sql.sql_insert(request)
        await self.mikrotik_gre()
        ip = await self.mikrotik_cisco()
        for k, v in ip['registrator'].items():
            request = f"INSERT INTO registrator (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
            await sql.sql_insert(request)
        for k, v in ip['cisco'].items():
            request = f"INSERT INTO cisco (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
            await sql.sql_insert(request)

    async def mikrotik_hostname(self):
        mibname = '1.3.6.1.2.1.1.5.0'
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData('public'),
                   UdpTransportTarget((self.loopback, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(mibname)))
        )
        for varBind in varBinds:
            namerou = (' ='.join([x.prettyPrint() for x in varBind])).split("=")[1]
            return namerou

    async def mikrotik_cisco(self):
        data = {}
        data["cisco"] = {}
        data["registrator"] = {}
        ip = self.loopback
        with aiosnmp.Snmp(host=ip, port=161, community="public", timeout=10, retries=2, max_repetitions=2, ) as snmp:
            try:
                results = await snmp.bulk_walk(".1.3.6.1.2.1.4.22.1.3")
                for res in results:
                    ip_old = str(res.value)
                    if 1 < int(ip_old.split(".")[3]) < 20:
                        ip_n = ip.split(".")[1:3]
                        ip_cisco = f"10.{ip_n[0]}.{ip_n[1]}.0"
                        ip_reg = f"19.{ip_n[0]}.{ip_n[1]}.0"
                        if ip_cisco.split(".")[0:3] == ip_old.split(".")[0:3]:
                            await self.snmp_cisco_v2(ip_old, data)
                        elif ip_reg.split(".")[0:3] == ip_old.split(".")[0:3]:
                            await self.snmp_trassir(ip_old, data)
            except:
                pass
        return data

    async def mikrotik_gre(self):
        i = 9
        oid = '1.3.6.1.2.1.2.2.1.2.'
        while i < 30:
            i += 1
            with aiosnmp.Snmp(host=self.loopback, port=161, community="public", timeout=5, retries=2,
                              max_repetitions=1, ) as snmp:
                try:
                    try:
                        for res in await snmp.get(f"{oid}{i}"):
                            namerou = res.value.decode('UTF-8')
                    except AttributeError:
                        continue
                except Exception as n:
                    print("Устройство не доступно")
                    break
                name = namerou.find("gre")
                # print(name)
                if name == 0:
                    print(namerou)
                    id = namerou.split("_")[3]
                    if id == "rou1":
                        await sql.sql_insert(
                            f"UPDATE filial SET isp1_name = '{namerou}' WHERE loopback = '{self.loopback}'")
                    elif id == "rou2":
                        await sql.sql_insert(
                            f"UPDATE filial SET isp2_name = '{namerou}' WHERE loopback = '{self.loopback}'")
                else:
                    pass

    async def ssh_ip_int(self):
        command = "sh ip int br"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        data = {}
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        open(PATH + 'leas.txt', 'wb').write(f)
        time.sleep(1)
        with open(PATH + 'leas.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    line.split()
                    try:
                        # print(line.split()[1])
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
                        # print(data)
                    except Exception as n:
                        print(n)

        data["cisco"] = {}
        data["registrator"] = {}

        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in bulkCmd(SnmpEngine(),
                                  UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
                                              authProtocol=usmHMACSHAAuthProtocol
                                              ),
                                  UdpTransportTarget((self.loopback, 161)),
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
                        if data["Vlan100"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 10:
                                await asyncio.sleep(1)
                                # print("cisco")
                                await self.snmp_cisco_v2(ip, data)
                        elif data["Vlan400"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                await asyncio.sleep(1)
                                await self.snmp_trassir(ip, data)
                        elif data["Vlan500"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                await asyncio.sleep(1)
                                await self.snmp_cisco_v2(ip, data)
                    else:
                        pass
        command = "show ip route"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        print("test_3")
        open(PATH + 'g.txt', 'wb').write(f)
        time.sleep(1)
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

        return data

    async def snmp_cisco_v2(self, ip, data):
        print(ip)
        with aiosnmp.Snmp(host=ip, port=161, community="read", timeout=10, retries=2, max_repetitions=2, ) as snmp:
            try:
                for res in await snmp.get(".1.3.6.1.4.1.9.2.1.3.0"):
                    data["cisco"][ip] = res.value.decode('UTF-8')

            except Exception as n:
                print(f"Ошибка_cisco {n}")


    async def snmp_trassir(self, ip, data):
        print(ip)
        with aiosnmp.Snmp(host=ip, port=161, community="dssl", timeout=10, retries=2, max_repetitions=2, ) as snmp:
            try:
                for res in await snmp.get("1.3.6.1.4.1.3333.1.7"):
                    data["registrator"][ip] = res.value.decode('UTF-8')
            except Exception as n:
                print(f"Ошибка_trassir {n}")


    async def ssh_sh_int(self):
        command = "sh int GigabitEthernet0/0/0 "
        user = 'operator'
        secret = '71LtkJnrYjn'
        kod = "537"
        port = 22
        data = {}
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        open(PATH + 'n.txt', 'wb').write(f)
        time.sleep(1)
        with open(PATH + 'n.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    if line.split()[0] == "Description:":
                        data["ISP1_NAME"] = line.split()[1]
        command = "sh int GigabitEthernet0/0/1 "
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        #        print("test_3")
        open(PATH + 'n.txt', 'wb').write(f)
        time.sleep(1)
        with open(PATH + 'n.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    if line.split()[0] == "Description:":
                        data["ISP2_NAME"] = line.split()[1]
        return data

    async def ssh_serial(self):
        print("start2")
        command = "show ver"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        #        print("test_3")
        open(PATH + 'serial.txt', 'wb').write(f)
        time.sleep(1)
        print("test_3")
        with open(PATH + 'serial.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    if line.split()[0] == "Processor":
                        return line.split()[3]


async def filial_check(call):
    data = {}
    kod = call.data.split("_")[1]
    request = f"SELECT loopback, name, region, kod FROM filial WHERE kod = {kod}"
    # print(request)
    row = await sql.sql_selectone(request)
    data['loopback'] = row[0]
    data['name'] = row[1]
    data['region'] = (await sql.sql_selectone(f"SELECT name FROM region WHERE id = {row[2]}"))[0]
    data['kod'] = row[3]
    await sql.sql_insert(f'DELETE FROM cisco WHERE kod = {kod}')
    await sql.sql_insert(f'DELETE FROM registrator WHERE kod = {kod}')
    await sql.sql_insert(f'DELETE FROM status WHERE kod = {kod}')
    await sql.sql_insert(f'DELETE FROM filial WHERE kod = {kod}')
    await call.message.answer(f"Идет обновление филиала\n"
                              f"Loopback: {data['loopback']}\n"
                              f"Филиал: {data['name']}\n"
                              f"Регион: {data['region']}")
    status = await Add_snmp(message=call.message, data=data).snmp_sysName()
    # if status is None:
    #     return "Ошибка"
    return status
