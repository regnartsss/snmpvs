from pysnmp.hlapi import getCmd, SnmpEngine,UsmUserData, usmHMACSHAAuthProtocol, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity,CommunityData,bulkCmd
from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql
import paramiko
import os
import time

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()
class NewFilial(StatesGroup):
        loopback = State()
        name = State()
        region = State()


    #
    #     for key, value in dat.items():
    #         try:
    #             dat[key]["region"]
    #         except KeyError:
    #             print("error_2")
    #             for k, v in data.region.items():
    #
    #                 if v == message.text:
    #                     dat[key]["region"] = k
    #                     bot.send_message(message.chat.id, info_filial(key), reply_markup=keyboard.main_menu()


class Add_snmp():
    def __init__(self, message, data):
        self.loopback = data['loopback']
        self.name = data['name']
        self.region = data['region']

    # Начальная информация о филиале
    async def snmp_sysName(self):

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
            try:
                self.kod = sysName.split("= ")[1].split("-")[2]
            except IndexError:
                return "Ошибка в loopback или адрес не доступен"
            try:
                self.kod = self.kod.split(".")[0]
            except Exception as n:
                print(n)
            try:
                hostname = sysName.split("= ")[1].split(".")[0]
            except Exception as n:
                print(n)
                hostname = sysName.split("= ")[1]

            request = f"INSERT INTO filial (kod, loopback, name, region, hostname) VALUES ({self.kod}, '{self.loopback}','{self.name}', (SELECT id FROM region WHERE name = '{self.region}'), '{hostname}')"
            await sql.sql_insert(request)
            print("Получаем все айпи на интерфейса")
            ip = await self.ssh_ip_int()
            serial = await self.ssh_serial()
            request = f"UPDATE filial  SET ISP1 = '{ip['ISP1']}', ISP2 = '{ip['ISP2']}', vlan100 = '{ip['Vlan100']}', " \
                      f"vlan200 = '{ip['Vlan200']}', vlan300 = '{ip['Vlan300']}', vlan400 = '{ip['Vlan400']}', " \
                      f"vlan500 = '{ip['Vlan500']}', gateway_isp1 = '{ip['gateway_isp1']}', gateway_isp2 = '{ip['gateway_isp2']}', serial = '{serial}' WHERE kod = {self.kod}"
            await sql.sql_insert(request)
            for k,v in ip['registrator'].items():
                request = f"INSERT INTO registrator (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
                await sql.sql_insert(request)
            for k,v in ip['cisco'].items():
                request = f"INSERT INTO cisco (kod, ip, hostname) VALUES ({self.kod}, '{k}','{v}')"
                await sql.sql_insert(request)

            print("Получаем description провайдера")
            isp_name = await self.ssh_sh_int()
            await sql.sql_insert(f"UPDATE filial "
                                 f"SET isp1_name = '{isp_name['ISP1_NAME']}', isp2_name = '{isp_name['ISP2_NAME']}' "
                                 f"WHERE kod = {self.kod}")
            print("Получаем шлюз провайдера")


            return self.kod
    #     # "sh ip int br"
    
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

        data["cisco"]={}
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
                                print("cisco")
                                await self.snmp_cisco_v2(ip,data)
                        elif data["Vlan400"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                await self.snmp_trassir(ip,data)
                        elif data["Vlan500"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                await self.snmp_cisco_v2(ip,data)
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
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData('read', mpModel=0),
                   UdpTransportTarget((ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)))
        )

        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))
                hostname_cisco = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
                data["cisco"][ip] = hostname_cisco

    async def snmp_trassir(self, ip, data):
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData('dssl'),
                   UdpTransportTarget((ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('1.3.6.1.4.1.3333.1.7')))
        )
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                #               print(' = '.join([x.prettyPrint() for x in varBind]))
                hostname_trassir = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
                data["registrator"][ip] = hostname_trassir

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
#
#     async def snmp_ifEntry(self):
#
#         for (errorIndication,
#              errorStatus,
#              errorIndex,
#              varBinds) in bulkCmd(SnmpEngine(),
#                                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
#                                               authProtocol=usmHMACSHAAuthProtocol
#                                               ),
#                                   UdpTransportTarget((self.loopback, 161)),
#                                   ContextData(),
#                                   1, 25,
#                                   ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),
#                                   lexicographicMode=False):
#             if errorIndication:
#                 print(errorIndication)
#                 break
#             elif errorStatus:
#                 print('%s at %s' % (errorStatus.prettyPrint(),
#                                     errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
#                 break
#             else:
#                 for varBind in varBinds:
#                     print(' = '.join([x.prettyPrint() for x in varBind]))
#                     vl = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
#                     index = ' = '.join([x.prettyPrint() for x in varBind]).split(" =")[0].split(".")[5]
#                     if vl == "Vlan100":
#                         data["vlan100"] = index
#                     elif vl == "Vlan400":
#                         data["vlan400"] = index
#                     elif vl == "Vlan500":
#                         data["vlan500"] = index
#
#     async def snmp_ipAddrEntry(self):
#         data["ISP1"] = "0.0.0.0"
#         data["ISP2"] = "0.0.0.0"
#         for (errorIndication,
#              errorStatus,
#              errorIndex,
#              varBinds) in bulkCmd(SnmpEngine(),
#                                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
#                                               authProtocol=usmHMACSHAAuthProtocol
#                                               ),
#                                   UdpTransportTarget((self.loopback, 161)),
#                                   ContextData(),
#                                   1, 25,
#                                   ObjectType(ObjectIdentity('IP-MIB', 'ipAddrEntry', 2)),
#                                   lexicographicMode=False):
#             if errorIndication:
#                 print(errorIndication)
#                 break
#             elif errorStatus:
#                 print('%s at %s' % (errorStatus.prettyPrint(),
#                                     errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
#                 break
#             else:
#                 for varBind in varBinds:
#                     print(' = '.join([x.prettyPrint() for x in varBind]))
#                     s = ' = '.join([x.prettyPrint() for x in varBind])
#                     print(s.split("= ")[1])
#                     d = s.split(" =")[0].split(".")[1:5]
#                     s = s.split("= ")[1]
#                     d = "%s.%s.%s.%s" % (d[0], d[1], d[2], d[3])
#
#                     if s == "1":
#                         data["ISP1"] = d
#                     elif s == "2":
#                         data["ISP2"] = d
#                     elif s == data["vlan100"]:
#                         if d.split(".")[0] == "169":
#                             data["IP_100"] = "null"
#                         else:
#                             data["IP_100"] = d
#                     elif s == data["vlan400"]:
#                         data["IP_400"] = d
#                     elif s == data["vlan500"]:
#                         print(d.split(".")[0])
#                         if d.split(".")[0] == "169":
#                             data["IP_500"] = "null"
#                         else:
#                             data["IP_500"] = d
#


#     # "show ip route"

#
#

#
#
# ad = Add_snmp()
#

# async def new(message):
#     result = await snmp_sysName(message)
#     if result is True:
#         await NewFilial.next()
#         await message.answer("Введите название филиала как в карточке 1С")
#     # else:
#     #     await message.answer("Ошибка при опросе устройства, повторите позднее")
#     #     await NewFilial.
#
#
# async def snmp_sysName(message):
#         print("Hostname")
#         # errorIndication, errorStatus, errorIndex, varBinds = next(getCmd(SnmpEngine(),
#         #                                                                  UsmUserData(userName='dvsnmp',
#         #                                                                              authKey='55GjnJwtPfk',
#         #                                                                              authProtocol=usmHMACSHAAuthProtocol),
#         #                                                                  UdpTransportTarget((self.loopback, 161)),
#         #                                                                  ContextData(),
#         #                                                                  ObjectType(
#         #                                                                      ObjectIdentity("1.3.6.1.2.1.1.5.0"))))
#         # for varBind in varBinds:
#         #     sysName = ' = '.join([x.prettyPrint() for x in varBind])
#         # self.kod = sysName.split("= ")[1].split("-")[2]
#         # try:
#         #     self.kod = self.kod.split(".")[0]
#         # except Exception as n:
#         #     print(n)
#         #     pass
#         # print("Создаем карточку")
#         # print(self.kod)
#
#         # data = {}
#         # leasea = {"cisco": {}, "registrator": {}}
#         # try:
#         #     data["sysName"] = sysName.split("= ")[1].split(".")[0]
#         # except:
#         #     data["sysName"] = sysName.split("= ")[1]
#         # data["kod"] = self.kod
#         # print("Получаем все айпи на интерфейса")
#         # self.ssh_ip_int()
#         # print("Получаем шлюз провайдера")
#         # self.ssh_sh_int()
#         # print("Получаем description провайдера")
#         # self.ssh_gateway()
#         # print("hostname cisco registrator")
#         # self.snmp_ipNetToMediaNEtAddress()
#         # data["serial"] = sshlist.ssh_serial(self.loopback)
#         # save_d()
#         return True
#         # try:
#         #     bot.send_message(chat_id=765333440, text="Филиал добавлен %s " % self.kod)
#         # except:
#         #     pass


#
# def new_name():
#     await NewFilial.next()
#
#
#
#     if message.text == "111":
#         users[str(message.chat.id)]["new_filial"] = 0
#         bot.send_message(message.chat.id, "Отмена")
#     elif message.text == "Добавить":
#         users[str(message.chat.id)]["new_filial"] = 1
#         #        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
#         bot.send_message(message.chat.id, "Введите Loopback адрес или наберите 111 для отмены")
#
#     elif users[str(message.chat.id)]["new_filial"] == 1:
#         #       try:
#         print("Добавить")
#         for kod, value in dat.items():
#             if dat[kod]["loopback"] == message.text:
#                 users[str(message.chat.id)]["new_filial"] = 0
#                 bot.send_message(message.chat.id, "Филиал уже добавлен")
#
#         users[str(message.chat.id)]["new_filial"] = 2
#         bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
#         Snmp(message=message).snmp_sysName()
#         bot.send_message(message.chat.id, "Loopback: %s\nВведите название филиала как в карточке 1С" % message.text)

    # except:
    #     users[str(message.chat.id)]["new_filial"] = 2
    #     #        dat[message.text {}}
    #     bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
    #     Snmp(message=message).snmp_sysName()
    # #     bot.send_message(message.chat.id, "Loopback: %s\nВведите название филиала как в карточке 1С" % message.text)
    # elif users[str(message.chat.id)]["new_filial"] == 2:
    #     users[str(message.chat.id)]["new_filial"] = 3
    #     for k, v in dat.items():
    #         try:
    #             dat[k]["name"]
    #
    #         except:
    #             print("error_1")
    #             dat[k]["name"] = message.text
    #             bot.send_message(message.chat.id, "Выберите регион", reply_markup=keyboard.region())
    # elif users[str(message.chat.id)]["new_filial"] == 3:
    #     users[str(message.chat.id)]["new_filial"] = 0
    #
    #     for key, value in dat.items():
    #         try:
    #             dat[key]["region"]
    #         except KeyError:
    #             print("error_2")
    #             for k, v in data.region.items():
    #
    #                 if v == message.text:
    #                     dat[key]["region"] = k
    #                     bot.send_message(message.chat.id, info_filial(key), reply_markup=keyboard.main_menu())
    #





