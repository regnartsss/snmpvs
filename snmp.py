from pysnmp.hlapi import *
from pprint import pprint
import json
import os
from config import bot, AD_USER, AD_PASSWORD
import keyboard
import data
from datetime import datetime, timedelta
import logging
import schedule
import telebot
import socket
import paramiko
import time
import russian_kod
import threading
import sshlist
from check_vs import check
from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES


def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()
global dat, users, stat, lease, subscrib


def open_user():
    global users, dat, stat, lease, subscrib
    #    bot.send_message(765333440, "sss")
    with open(PATH + 'users.json', 'rb') as f:
        users = json.load(f)
    with open(PATH + 'dat.json', 'rb') as f:
        dat = json.load(f)

    with open(PATH + 'lease.json', 'rb') as f:
        lease = json.load(f)
    with open(PATH + 'subscrib.json', 'rb') as f:
        subscrib = json.load(f)


def open_stat():
    global stat
    with open(PATH + 'stat.json', 'rb') as f:
        stat = json.load(f)


def save_d():
    global dat, users, stat, lease, subscrib
    with open(PATH + 'dat.json', 'w', encoding="utf-16") as f:
        json.dump(dat, f)
    with open(PATH + 'dat.json', 'rb') as f:
        dat = json.load(f)
    with open(PATH + 'users.json', 'w', encoding="utf-16") as f:
        json.dump(users, f)
    with open(PATH + 'users.json', 'rb') as f:
        users = json.load(f)
    # with open(PATH + 'stat.json', 'w', encoding="utf-16") as f:
    #     json.dump(stat, f)
    # with open(PATH + 'stat.json', 'rb') as f:
    #     stat = json.load(f)
    with open(PATH + 'lease.json', 'w', encoding="utf-16") as f:
        json.dump(lease, f)
    with open(PATH + 'lease.json', 'rb') as f:
        lease = json.load(f)
    with open(PATH + 'subscrib.json', 'w', encoding="utf-16") as f:
        json.dump(subscrib, f)
    with open(PATH + 'subscrib.json', 'rb') as f:
        subscrib = json.load(f)


open_user()


class Snmp():
    def __init__(self, message):

        try:
            self.loopback = message.text
        except:
            pass

        try:
            self.loopback = message.text.split("_")[1]
        except:
            pass

    # Начальная информация о филиале
    def snmp_sysName(self):
        print("Hostname")
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
        self.kod = sysName.split("= ")[1].split("-")[2]
        try:
            self.kod = self.kod.split(".")[0]
        except Exception as n:
            print(n)
            pass
        print("Создаем карточку")
        dat[self.kod] = {}
        lease[self.kod] = {"cisco": {}, "registrator": {}}
        try:
            dat[self.kod]["sysName"] = sysName.split("= ")[1].split(".")[0]
        except:
            dat[self.kod]["sysName"] = sysName.split("= ")[1]
        dat[self.kod]["kod"] = self.kod
        print("Получаем все айпи на интерфейса")
        self.ssh_ip_int()
        print("Получаем шлюз провайдера")
        self.ssh_sh_int()
        print("Получаем description провайдера")
        self.ssh_gateway()
        print("hostname cisco registrator")
        self.snmp_ipNetToMediaNEtAddress()
        dat[self.kod]["serial"] = sshlist.ssh_serial(self.loopback)
        save_d()

        try:
            bot.send_message(chat_id=765333440, text="Филиал добавлен %s " % self.kod)
        except:
            pass

    def snmp_ifEntry(self):

        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in bulkCmd(SnmpEngine(),
                                  UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
                                              authProtocol=usmHMACSHAAuthProtocol
                                              ),
                                  UdpTransportTarget((self.loopback, 161)),
                                  ContextData(),
                                  1, 25,
                                  ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),
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
                    print(' = '.join([x.prettyPrint() for x in varBind]))
                    vl = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
                    index = ' = '.join([x.prettyPrint() for x in varBind]).split(" =")[0].split(".")[5]
                    if vl == "Vlan100":
                        dat[self.kod]["vlan100"] = index
                    elif vl == "Vlan400":
                        dat[self.kod]["vlan400"] = index
                    elif vl == "Vlan500":
                        dat[self.kod]["vlan500"] = index

    def snmp_ipAddrEntry(self):
        dat[self.kod]["ISP1"] = "0.0.0.0"
        dat[self.kod]["ISP2"] = "0.0.0.0"
        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in bulkCmd(SnmpEngine(),
                                  UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',
                                              authProtocol=usmHMACSHAAuthProtocol
                                              ),
                                  UdpTransportTarget((self.loopback, 161)),
                                  ContextData(),
                                  1, 25,
                                  ObjectType(ObjectIdentity('IP-MIB', 'ipAddrEntry', 2)),
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
                    print(' = '.join([x.prettyPrint() for x in varBind]))
                    s = ' = '.join([x.prettyPrint() for x in varBind])
                    print(s.split("= ")[1])
                    d = s.split(" =")[0].split(".")[1:5]
                    s = s.split("= ")[1]
                    d = "%s.%s.%s.%s" % (d[0], d[1], d[2], d[3])

                    if s == "1":
                        dat[self.kod]["ISP1"] = d
                    elif s == "2":
                        dat[self.kod]["ISP2"] = d
                    elif s == dat[self.kod]["vlan100"]:
                        if d.split(".")[0] == "169":
                            dat[self.kod]["IP_100"] = "null"
                        else:
                            dat[self.kod]["IP_100"] = d
                    elif s == dat[self.kod]["vlan400"]:
                        dat[self.kod]["IP_400"] = d
                    elif s == dat[self.kod]["vlan500"]:
                        print(d.split(".")[0])
                        if d.split(".")[0] == "169":
                            dat[self.kod]["IP_500"] = "null"
                        else:
                            dat[self.kod]["IP_500"] = d

    def snmp_ipNetToMediaNEtAddress(self):
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
                                  #                                  ObjectType(ObjectIdentity('IP-MIB', 'ipNetToMediaPhysAddress', index)),
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
                        if dat[self.kod]["Vlan100"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 10:
                                print("cisco")
                                self.snmp_cisco_v2(ip)
                        elif dat[self.kod]["Vlan400"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                self.snmp_trassir(ip)
                        elif dat[self.kod]["Vlan500"].split(".")[0:3] == ip.split(".")[0:3]:
                            if 1 < int(ip.split(".")[3]) < 15:
                                self.snmp_cisco_v2(ip)
                    else:
                        pass

    def snmp_cisco_v2(self, ip):
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
                lease[self.kod]["cisco"][ip] = hostname_cisco

    def snmp_trassir(self, ip):
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
                lease[self.kod]["registrator"][ip] = hostname_trassir

    # "show ip route"
    def ssh_gateway(self):
        command = "show ip route"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        #
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

        dat[self.kod]["gateway_isp1"] = "0.0.0.0"
        dat[self.kod]["gateway_isp2"] = "0.0.0.0"

        try:
            if dat[self.kod]["ISP1"].split(".")[0:2] == isp_1.split(".")[0:2]:
                dat[self.kod]["gateway_isp1"] = isp_1
            elif dat[self.kod]["ISP1"].split(".")[0:2] == isp_2.split(".")[0:2]:
                dat[self.kod]["gateway_isp1"] = isp_2

            if dat[self.kod]["ISP2"].split(".")[0:2] == isp_2.split(".")[0:2]:
                dat[self.kod]["gateway_isp2"] = isp_2
            elif dat[self.kod]["ISP2"].split(".")[0:2] == isp_1.split(".")[0:2]:
                dat[self.kod]["gateway_isp2"] = isp_1
        except:
            print("Ошибка шлюза")
            pass

    # "sh ip int br"
    def ssh_ip_int(self):
        command = "sh ip int br"
        user = 'operator'
        secret = '71LtkJnrYjn'
        kod = "537"
        port = 22
        #
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        #        print("test_3")
        open(PATH + 'leas.txt', 'wb').write(f)
        time.sleep(1)
        print("test_3")
        with open(PATH + 'leas.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    #                    print(line.split())
                    try:
                        if line.split()[0] == 'Tunnel0':
                            dat[self.kod]["ISP1"] = line.split()[1]

                        elif line.split()[0] == 'Tunnel1':
                            dat[self.kod]["ISP2"] = line.split()[1]

                        elif line.split()[0] == 'Loopback0':
                            dat[self.kod]["loopback"] = line.split()[1]

                        elif line.split()[0] == 'Vlan100':

                            if line.split()[1].split(".")[0] == "169":
                                dat[self.kod]["Vlan100"] = "null"
                            else:
                                dat[self.kod]["Vlan100"] = line.split()[1]

                        elif line.split()[0] == 'Vlan200':
                            if line.split()[1].split(".")[0] == "169":
                                dat[self.kod]["Vlan200"] = "null"
                            else:
                                dat[self.kod]["Vlan200"] = line.split()[1]

                        elif line.split()[0] == 'Vlan300':
                            if line.split()[1].split(".")[0] == "169":
                                dat[self.kod]["Vlan300"] = "null"
                            else:
                                dat[self.kod]["Vlan300"] = line.split()[1]

                        elif line.split()[0] == 'Vlan400':
                            if line.split()[1].split(".")[0] == "169":
                                dat[self.kod]["Vlan400"] = "null"
                            else:
                                dat[self.kod]["Vlan400"] = line.split()[1]

                        elif line.split()[0] == 'Vlan500':
                            if line.split()[1].split(".")[0] == "169":
                                dat[self.kod]["Vlan500"] = "null"
                            else:
                                dat[self.kod]["Vlan500"] = line.split()[1]

                        # elif line.split()[0] == 'Dialer100':
                        #     #if dat[self.kod]["ISP2"] == "unassigned":
                        #         dat[self.kod]["ISP2"] = line.split()[1]

                    except Exception as n:
                        print(n)
                        pass

    def ssh_sh_int(self):
        command = "sh int GigabitEthernet0/0/0 "
        user = 'operator'
        secret = '71LtkJnrYjn'
        kod = "537"
        port = 22
        #
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        #        print("test_3")
        open(PATH + 'n.txt', 'wb').write(f)
        time.sleep(1)
        print("test_3")
        with open(PATH + 'n.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    if line.split()[0] == "Description:":
                        print(line.split()[1])
                        dat[self.kod]["ISP1_NAME"] = line.split()[1]

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
        print("test_3")
        with open(PATH + 'n.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    if line.split()[0] == "Description:":
                        print(line.split()[1])
                        dat[self.kod]["ISP2_NAME"] = line.split()[1]


def GetTime(s):
    sec = timedelta(seconds=int(s) / 100)
    d = datetime(1, 1, 1) + sec
    #   print("%d:%d:%d:%d" % (d.day - 1, d.hour, d.minute, d.second))
    return "%dd:%dh:%dm:%ds" % (d.day - 1, d.hour, d.minute, d.second)


class traffic():
    global dat, stat

    def __init__(self, call):
        self.kod = call.data.split("_")[1]
        self.call = call

    def snmp(self):
        try:
            stat[self.kod]["0"]
        except:
            stat[self.kod] = {"0": {},
                              "1": {}}
        d = {}
        for i, v in data.mib_all.items():
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',

                                   authProtocol=usmHMACSHAAuthProtocol
                                   ),
                       UdpTransportTarget((dat[self.kod]["loopback"], 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity(v)))
            )

            if errorIndication:
                print(errorIndication)
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            else:
                for varBind in varBinds:
                    print(' = '.join([x.prettyPrint() for x in varBind]))
                    m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                    d[i] = m

        stat[self.kod]["0"] = stat[self.kod]["1"]
        stat[self.kod]["1"] = d
        save_d()

    def user_st(self):
        self.snmp()
        self.uptime()
        Intunnel1 = int(stat[self.kod]["1"]["ifInOctets_isp1_tunnel"]) - int(
            stat[self.kod]["0"]["ifInOctets_unnel"])
        Intunnel2 = int(stat[self.kod]["1"]["ifInOctets_isp2_tunnel"]) - int(
            stat[self.kod]["0"]["ifInOctets_isp2_tunnel"])
        Outtunnel1 = int(stat[self.kod]["1"]["ifOutOctets_isp1_tunnel"]) - int(
            stat[self.kod]["0"]["ifOutOctets_isp1_tunneisp1_tl"])
        Outtunnel2 = int(stat[self.kod]["1"]["ifOutOctets_isp2_tunnel"]) - int(
            stat[self.kod]["0"]["ifOutOctets_isp2_tunnel"])
        t = "%s\n%s\n" % (dat[self.kod]["name"], dat[self.kod]["sysName"])
        t += "\nUptime %s\n\n" % (GetTime(stat[self.kod]["1"]["sysUpTime"]))
        t += "🔵 Основной провайдер\n⬇️ In %s MB |⬆️ Out %s MB\n\n🔴 Резервный провайдер\n ⬇️ In %s MB |⬆️ Out %s MB\n" % \
             (int(int(stat[self.kod]["1"]["ifInOctets_isp1"]) / 1048576),
              int(int(stat[self.kod]["1"]["ifOutOctets_isp1"]) / 1048576),
              int(int(stat[self.kod]["1"]["ifInOctets_isp2"]) / 1048576),
              int(int(stat[self.kod]["1"]["ifOutOctets_isp2"]) / 1048576))

        t += "\n🔵 Tunnel 1\n ⬇️ In %s MB | ⬆️ Out %s MB\n ⏬ In %.2f MB | ⏫ Out %.2f MB \n" % (
            int(int(stat[self.kod]["1"]["ifInOctets_isp1_tunnel"]) / 1048576),
            int(int(stat[self.kod]["1"]["ifOutOctets_isp1_tunnel"]) / 1048576),
            Intunnel1 / 1048576, Outtunnel1 / 1048576)

        t += "\n🔴 Tunnel 2\n ⬇️ In %s MB | ⬆️ Out %s MB\n ⏬ In %.2f MB | ⏫ Out %.2f MB" % (
            int(int(stat[self.kod]["1"]["ifInOctets_isp2_tunnel"]) / 1048576),
            int(int(stat[self.kod]["1"]["ifOutOctets_isp2_tunnel"]) / 1048576),
            Intunnel2 / 1048576, Outtunnel2 / 1048576)

        keyboard = telebot.types.InlineKeyboardMarkup()

        bot.edit_message_text(chat_id=self.call.message.chat.id, message_id=self.call.message.message_id, text=t)

        keyboard.row(telebot.types.InlineKeyboardButton(text="Lease", callback_data="lease_%s" % self.kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="Traffic", callback_data="traffic_%s" % self.kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="ssh", callback_data="ssh_%s" % self.kod))
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="Назад", callback_data="region_%s" % dat[self.kod]["region"]))
        bot.send_message(chat_id=self.call.message.chat.id, text=info_filial(self.kod, "fil"), reply_markup=keyboard)

    def uptime(self):
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',

                               authProtocol=usmHMACSHAAuthProtocol
                               ),
                   UdpTransportTarget((dat[self.kod]["loopback"], 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")))
        )

        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))
                m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                stat[self.kod]["1"]["sysUpTime"] = m

    def info_filial(self, st="all"):
        print("err")
        if st == "all":
            text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nIP_LAN: %s\nIP_CAM: %s\nIP_SC: %s\nISP1: %s\nISP2: %s\n" % \
                   (dat[self.kod]["name"], dat[self.kod]["kod"], data.region[int(dat[self.kod]["region"])],
                    dat[self.kod]["sysName"],
                    dat[self.kod]["IP_100"],
                    dat[self.kod]["IP_400"],
                    dat[self.kod]["IP_500"],
                    dat[self.kod]["ISP1"], dat[self.kod]["ISP2"])
            print("error_m_2")
            try:
                text += "Cisco:\n"
                for k_l, v_l in lease[self.kod]["cisco"].items():
                    text += "%s %s\n" % (k_l, v_l)

                text += "Registrator:\n"
                for k_l, v_l in lease[self.kod]["registrator"].items():
                    text += "%s %s\n" % (k_l, v_l)
            except:
                pass

            return text
        elif st == "fil":
            text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nIP_LAN: %s\nIP_CAM: %s\nIP_SC: %s\n" % \
                   (dat[self.kod]["name"], dat[self.kod]["kod"], data.region[int(dat[self.kod]["region"])],
                    dat[self.kod]["sysName"],
                    dat[self.kod]["IP_100"],
                    dat[self.kod]["IP_400"],
                    dat[self.kod]["IP_500"]
                    )
            return text


# Новый юзер
def new_user(message):
    if str(message.chat.id) in users:
        print(users[str(message.chat.id)]["admin"])
        try:
            if users[str(message.chat.id)]["admin"] == 1:
                bot.send_message(chat_id=message.chat.id, text="Пользователь есть", reply_markup=keyboard.main_menu())
            else:
                bot.send_message(message.chat.id, "Пользователь есть", reply_markup=keyboard.main_menu_user())
        except:
            bot.send_message(message.chat.id, "Пользователь есть", reply_markup=keyboard.main_menu_user())
    else:
        username = message.from_user.username
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name
        users[message.chat.id] = {"id": message.chat.id,
                                  "username": username,
                                  "firstname": firstname,
                                  "lastname": lastname,
                                  "ssh": 0,
                                  "subscribe": []}

        bot.send_message(message.chat.id, "Пользователь зарегистрирован", reply_markup=keyboard.main_menu_user())
    save_d()


# Вывод лизов
def snmp_lease(kod, index):
    loopback = dat[kod]["loopback"]
    lease[kod] = {}
    text, stop = "", 0
    print(11)
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
                              ObjectType(ObjectIdentity('IP-MIB', 'ipNetToMediaNetAddress', index)),
                              ObjectType(ObjectIdentity('IP-MIB', 'ipNetToMediaPhysAddress', index)),
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
                print(' = '.join([x.prettyPrint() for x in varBind]))
                s = ' = '.join([x.prettyPrint() for x in varBind])
                d = s.split(" =")[0].split(".")[0]
                print(d)
                if s.split("= ")[1] == "No more variables left in this MIB View":
                    pass
                elif d == "IP-MIB::ipNetToMediaNetAddress":
                    net = s.split("= ")[1]
                elif d == "IP-MIB::ipNetToMediaPhysAddress":
                    phys = s.split("= ")[1]

            if s.split("= ")[1] == "No more variables left in this MIB View":
                print("error_101")
                break
            else:
                text += "ip %s   mac %s\n" % (net, phys)
    return text


# snmp_lease("10.96.13.1", 23)
def new_filial(message):
    global dat
    if message.text == "111":
        users[str(message.chat.id)]["new_filial"] = 0
        bot.send_message(message.chat.id, "Отмена")
    elif message.text == "Добавить":
        users[str(message.chat.id)]["new_filial"] = 1
        #        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
        bot.send_message(message.chat.id, "Введите Loopback адрес или наберите 111 для отмены")

    elif users[str(message.chat.id)]["new_filial"] == 1:
        #       try:
        print("Добавить")
        for kod, value in dat.items():
            if dat[kod]["loopback"] == message.text:
                users[str(message.chat.id)]["new_filial"] = 0
                bot.send_message(message.chat.id, "Филиал уже добавлен")

        users[str(message.chat.id)]["new_filial"] = 2
        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
        Snmp(message=message).snmp_sysName()
        bot.send_message(message.chat.id, "Loopback: %s\nВведите название филиала как в карточке 1С" % message.text)

    # except:
    #     users[str(message.chat.id)]["new_filial"] = 2
    #     #        dat[message.text {}}
    #     bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
    #     Snmp(message=message).snmp_sysName()
    #     bot.send_message(message.chat.id, "Loopback: %s\nВведите название филиала как в карточке 1С" % message.text)
    elif users[str(message.chat.id)]["new_filial"] == 2:
        users[str(message.chat.id)]["new_filial"] = 3
        for k, v in dat.items():
            try:
                dat[k]["name"]

            except:
                print("error_1")
                dat[k]["name"] = message.text
                bot.send_message(message.chat.id, "Выберите регион", reply_markup=keyboard.region())
    elif users[str(message.chat.id)]["new_filial"] == 3:
        users[str(message.chat.id)]["new_filial"] = 0

        for key, value in dat.items():
            try:
                dat[key]["region"]
            except KeyError:
                print("error_2")
                for k, v in data.region.items():

                    if v == message.text:
                        dat[key]["region"] = k
                        bot.send_message(message.chat.id, info_filial(key), reply_markup=keyboard.main_menu())

    save_d()


def info_lease(call):
    kod = call.data.split("_")[1]
    lease = call.data.split("_")[2]

    if lease == "LAN":
        index = dat[kod]["vlan100"]
        if dat[kod]["IP_100"] == "null":
            return "На данном филиале нет LAN", "null"
        else:
            return 'Ожидайте, запрос может занять до 1 мин', index
    elif lease == "CAM":
        index = dat[kod]["vlan400"]
        return 'Ожидайте, запрос может занять до 1 мин', index
    elif lease == "SC":
        index = dat[kod]["vlan500"]
        if dat[kod]["IP_500"] == "null":
            return "На данном филиале нет SC", "null"
        else:
            return 'Ожидайте, запрос может занять до 1 мин', index


def info_market(call):
    print("error_m")
    kod = call.data.split("_")[1]
    loopback = dat[kod]["loopback"]

    if call.data.split("_")[0] == "market":
        print("error_marker_1")
        users[str(call.message.chat.id)]["kod"] = kod
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(telebot.types.InlineKeyboardButton(text="Lease", callback_data="lease_%s" % kod))
        #        keyboard.row(telebot.types.InlineKeyboardButton(text="Traffic", callback_data="traffic_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="ssh", callback_data="ssh_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="show ip interface brief", callback_data="sship_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="traceroute vrf 100 ya.ru", callback_data="traceroute_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="Назад", callback_data="region_%s" % dat[kod]["region"]))

        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=info_filial(kod),
                                  reply_markup=keyboard)
        except:
            pass

    elif call.data.split("_")[0] == "lease":
        text = "Выберите подсеть. Запрос может занять несколько секунд"
        try:
            if call.data.split("_")[2] == "LAN":
                #                text = ssh_lease(kod, "Vlan100")
                text = thread_ssh_lease(kod, "Vlan100")

            elif call.data.split("_")[2] == "CAM":
                #                text = ssh_lease(kod, "Vlan400")
                text = thread_ssh_lease(kod, "Vlan400")
            elif call.data.split("_")[2] == "SC":
                #                text = ssh_lease(kod, "Vlan500")
                text = thread_ssh_lease(kod, "Vlan500")
            elif call.data.split("_")[2] == "KIOSK":
                #                text = ssh_lease(kod, "Vlan200")
                text = thread_ssh_lease(kod, "Vlan200")
        except:
            pass

        keyboard = telebot.types.InlineKeyboardMarkup()
        LAN = telebot.types.InlineKeyboardButton(text="LAN", callback_data="lease_%s_LAN" % kod)
        CAM = telebot.types.InlineKeyboardButton(text="CAM", callback_data="lease_%s_CAM" % kod)
        SC = telebot.types.InlineKeyboardButton(text="SC", callback_data="lease_%s_SC" % kod)
        KIOSK = telebot.types.InlineKeyboardButton(text="Kiosk", callback_data="lease_%s_KIOSK" % kod)
        keyboard.row(LAN, CAM, SC, KIOSK)
        #        keyboard.row(telebot.types.InlineKeyboardButton(text="Traffic", callback_data="traffic_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="ssh", callback_data="ssh_%s" % kod))
        keyboard.row(telebot.types.InlineKeyboardButton(text="Назад", callback_data="region_%s" % dat[kod]["region"]))
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
                                  reply_markup=keyboard)
        except:
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Нет лизов",
                                      reply_markup=keyboard)
            except:
                bot.send_message(call.message.chat.id, text="Нет лизов")
    elif call.data.split("_")[0] == "traffic":
        bot.answer_callback_query(callback_query_id=call.id, text='Ожидайте, запрос может занять до 1 мин',
                                  show_alert=True)
        traffic(call).user_st()


def info_filial(kod, st="all"):
    text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nloopback %s\n" \
           "IP_LAN: %s\nIP_Kiosk: %s\nIP_CAM: %s\nIP_SC: %s\nISP1_NAME: %s\nISP1: %s\ngateway_isp1: %s\nISP2_NAME: %s\nISP2: %s\ngateway_isp2: %s\nserila: %s" % \
           (dat[kod]["name"],
            dat[kod]["kod"],
            data.region[int(dat[kod]["region"])],
            dat[kod]["sysName"],
            dat[kod]["loopback"],
            dat[kod]["Vlan100"],
            dat[kod]["Vlan200"],
            dat[kod]["Vlan400"],
            dat[kod]["Vlan500"],
            dat[kod]["ISP1_NAME"],
            dat[kod]["ISP1"],
            dat[kod]["gateway_isp1"],
            dat[kod]["ISP2_NAME"],
            dat[kod]["ISP2"],
            dat[kod]["gateway_isp2"],
            dat[kod]["serial"])
    print("error_m_2")
    try:
        text += "Cisco:\n"
        for k_l, v_l in lease[kod]["cisco"].items():
            text += "%s %s\n" % (k_l, v_l)

        text += "Registrator:\n"
        for k_l, v_l in lease[kod]["registrator"].items():
            text += "%s %s\n" % (k_l, v_l)
    except:
        pass

    return text


def work(message, call=""):
    keyboard = telebot.types.InlineKeyboardMarkup()
    if message.text == "Меню":
        for k, v in data.region.items():
            num = 0
            for key, value in dat.items():
                if int(k) == value["region"]:
                    num += 1

            keyboard.row(telebot.types.InlineKeyboardButton(text="%s %s" % (v, num), callback_data="region_%s" % k))
        try:
            bot.send_message(message.chat.id, "Выберите регион:", reply_markup=keyboard)
        except:
            pass
    elif message.text == "Выберите филиал:":
        for k, v in data.region.items():
            keyboard.row(telebot.types.InlineKeyboardButton(text=v, callback_data="region_%s" % k))

        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="Выберите регион:",
                                  reply_markup=keyboard)
        except:
            pass
    elif call.data.split("_")[0] == "region":
        for key, value in dat.items():
            if value["region"] == int(call.data.split("_")[1]):
                keyboard.row(telebot.types.InlineKeyboardButton(text="%s %s" % (key, dat[key]["name"]),
                                                                callback_data="market_%s" % dat[key]["kod"]))
        keyboard.row(telebot.types.InlineKeyboardButton(text="Назад", callback_data="back_back"))
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="Выберите филиал:",
                                  reply_markup=keyboard)
        except:
            pass


def registrator(message, call=""):
    print(111)
    keyboard = telebot.types.InlineKeyboardMarkup()
    if message.text == "Регистраторы":
        for k, v in data.region.items():
            keyboard.row(telebot.types.InlineKeyboardButton(text=v, callback_data="registrator_%s" % k))
        bot.send_message(message.chat.id, "Выберите регион:", reply_markup=keyboard)
    elif call.data.split("_")[0] == "registrator":
        text = "Registrator:\n"
        for kod, value in dat.items():
            print(kod)
            if dat[kod]["region"] == int(call.data.split("_")[1]):
                text += "%s %s\n" % (kod, dat[kod]["name"])
                for key, va in lease.items():
                    if kod == key:
                        for k_l, v_l in lease[kod]["registrator"].items():
                            text += "     %s %s\n" % (k_l, v_l)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text)


def update_cisco():
    for kod, value in lease.items():
        for ip, v in value["cisco"].items():
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
                    lease[kod]["cisco"][ip] = hostname_cisco


def update_registrator():
    for kod, value in lease.items():
        for ip, v in value["registrator"].items():
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
                    print(' = '.join([x.prettyPrint() for x in varBind]))
                    hostname_trassir = ' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1]
                    lease[kod]["registrator"][ip] = hostname_trassir


def update_gateway():
    # print(dat)
    for kod, value in dat.items():
        # print(kod)
        try:
            # print(dat)
            loopback = dat[kod]["loopback"]

        except KeyError:
            print("update_gateway Шлюз не верный")
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
        time.sleep(1)
        isp_1, isp_2 = "0.0.0.0", "0.0.0.0"
        with open(PATH + 'g.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() == []:
                    pass
                else:
                    print(line.split())
                    if line.split()[0] == 'S*':
                        isp_1 = line.split()[4]
                    elif line.split()[0] == '[1/0]':
                        isp_2 = line.split()[2]

        # print(dat[kod]["ISP1"])
        # print(isp_1)
        # print(dat[kod]["ISP2"])
        # print(isp_2)

        try:
            if dat[kod]["ISP1"].split(".")[0:2] == isp_1.split(".")[0:2]:
                dat[kod]["gateway_isp1"] = isp_1
            elif dat[kod]["ISP1"].split(".")[0:2] == isp_2.split(".")[0:2]:
                dat[kod]["gateway_isp1"] = isp_2

            if dat[kod]["ISP2"].split(".")[0:2] == isp_2.split(".")[0:2]:
                dat[kod]["gateway_isp2"] = isp_2
            elif dat[kod]["ISP2"].split(".")[0:2] == isp_1.split(".")[0:2]:
                dat[kod]["gateway_isp2"] = isp_1

        except:
            print("gateway_error_1")
            pass

    save_d()


# update_gateway()
# update_cisco()
# update_registrator()

def ssh(message, call=""):
    command = message.text
    kod = users[str(message.chat.id)]["ssh_loopback"]
    loopback = dat[kod]["loopback"]
    print(loopback)
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    #
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    # #    print(stderr.read())
    #
    t = stdout.read()
    #    print(stderr.read())
    #    print(stdin.read())
    #    print(t)
    #    data = stdout.read() + stderr.read()
    #    print(data)
    bot.send_message(message.chat.id, t)
    client.close()
    text = "Введите команду SSH для отправки на циску или 444 для отмены\n" \
           "vlan 100 - ping vrf 100 'ip addreess'\nvlan 200 - ping vrf 200 'ip addreess'\n" \
           "vlan 400 - ping vrf 100 'ip addreess'\nvlan 500 - ping vrf 6 'ip addreess'\n" \
           "isp gateway - ping 'ip address'\nsh ip int br"


# "show ip dhcp binding"
def ssh_lease(kod, lea):
    print("ssh_lease_start")
    loopback = dat[kod]["loopback"]
    command = "show ip dhcp binding"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    print("ssh_lease_command_1")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    print("ssh_lease_command_read")
    t = stdout.read()
    client.close()
    open(PATH + 't.txt', 'wb').write(t)
    print("ssh_lease_end")


def ssh_ip_int_br(call):
    kod = call.data.split("_")[1]
    command = "show ip interface brief"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=dat[kod]["loopback"], username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    #        print("test_3")
    open(PATH + 'leas.txt', 'wb').write(f)
    time.sleep(1)
    print("test_3")
    with open(PATH + 'leas.txt') as f:
        lines = f.readlines()
        text = ""
        for line in lines:
            if line.split() != []:

                column = line.split()[0]
                if column == "Interface":
                    text += line
                elif column == "GigabitEthernet0/0/0":
                    text += line
                elif column == "GigabitEthernet0/0/1":
                    text += line
                elif column == "GigabitEthernet0/1/0":
                     text += line
                # elif column == "Loopback0":
                #     text += line
                # elif column == "Tunnel0":
                #     text += line
                # elif column == "Tunnel1":
                #     text += line
                # elif column == "Vlan100":
                #     text += line
                # elif column == "Vlan200":
                #     text += line
                # elif column == "Vlan300":
                #     text += line
                # elif column == "Vlan400":
                #     text += line
                # elif column == "Vlan500":
                #     text += line
                elif column == "Dialer100":
                    text += line
                elif column == "Dialer110":
                    text += line
        bot.send_message(call.message.chat.id, text)

def ssh_traceroute_vrf(call):
    kod = call.data.split("_")[1]
    command = "traceroute vrf 100 ya.ru"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=dat[kod]["loopback"], username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    #        print("test_3")
    open(PATH + 'leas.txt', 'wb').write(f)
    time.sleep(1)
    print("test_3")
    with open(PATH + 'leas.txt') as f:
        lines = f.readlines()
        text = ""
        for line in lines:
            if line.split() != []:
                text += line

        bot.send_message(call.message.chat.id, text)


def thread_ssh_lease(kod, lea):
    print("thread_ssh_lease_start")
    t = threading.Thread(target=ssh_lease, args=(kod, lea))
    t.start()
    t.join()

    text = ""
    with open(PATH + 't.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() == []:
                pass
            else:
                if line.split()[0].split(".")[0:3] == dat[kod][lea].split(".")[0:3]:
                    text += leas_print(line.split())
                else:
                    pass
            pass
    print("thread_ssh_lease_end")
    return text


def leas_print(t):
    ip = t[0]
    mac = "%s%s%s" % (t[1].split(".")[0], t[1].split(".")[1], t[1].split(".")[2])
    try:
        if t[7] == 'Automatic':
            if t[6] == "PM":
                ss = int(t[5].split(":")[0]) + 12
                ss = "%s:%s" % (ss, t[5].split(":")[1])
                data = "%s/%s/%s %s" % (t[2], t[3], t[4], ss)
            else:
                data = "%s/%s/%s %s" % (t[2], t[3], t[4], t[5])
    except:
        data = "Статик"
        pass
    return "%s /%s %s\n" % (ip, mac, data)


def snmp_cisco_mac(message):
    print(message.text)
    mac = message.text.split("/")[1]
    kod = users[str(message.chat.id)]["kod"]
    print("sh port add")
    for ip, v in lease[kod]["cisco"].items():
        print(ip)
        command = "sh port add"
        user = 'itkras'
        secret = 'miccis-96kraS'
        port = 22
        print("ssh_err_mac_1")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=ip, username=user, password=secret, port=port)
            stdin, stdout, stderr = client.exec_command(command)
            print("ssh_err_mac_2")
            t = stdout.read()
            client.close()
            open(PATH + 'l.txt', 'wb').write(t)
            time.sleep(1)
            text = ""
            with open(PATH + 'l.txt') as f:
                lines = f.readlines()
                for line in lines:
                    if line.split()[0] == "100" or line.split()[0] == "200" or line.split()[0] == "300" or line.split()[
                        0] == "400":
                        mac_old = "%s%s%s" % (
                            line.split()[1].split(".")[0], line.split()[1].split(".")[1], line.split()[1].split(".")[2])
                        #                    print(mac)
                        #                    print(mac_old)
                        if mac == mac_old:
                            #                        print(line.split()[3])
                            text = "Mac на порту %s" % line.split()[3]
                            #                        bot.send_message(message.chat.id, text)
                            bot.send_message(chat_id=message.chat.id, text=text)
                            return

            bot.send_message(message.chat.id, "Не найдено на %s" % v)
        except:
            bot.send_message(chat_id=message.chat.id, text="Установлена cisco 3550. Проверить порт не возможно")


def thread_snmp_cisco_mac(message):
    print("thread_ssh_lease_start")

    t = threading.Thread(target=snmp_cisco_mac, args=(message,))
    t.start()
    t.join()


# snmp_cisco_mac()


def search_kod(message):
    print("sea_1")
    if message.text == "Нет" or message.text == "нет":
        users[str(message.chat.id)]["new_filial"] = 0
        users[str(message.chat.id)]["search_kod"] = 0
        bot.send_message(message.chat.id, "Отмена")
    elif message.text == "Найти по коду":
        users[str(message.chat.id)]["search_kod"] = 1
        #        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
        bot.send_message(message.chat.id, "Введите код филиала или наберите Нет для отмены")
    elif users[str(message.chat.id)]["search_kod"] == 1:
        print("sea_err")
        for kod, value in russian_kod.full_filial.items():
            if kod == message.text:
                print("поиск завершен")
                for k, v in dat.items():
                    print("kod %s" % k)
                    print(message.text)
                    if k == message.text:
                        print("rrrr")
                        text = info_filial(kod)
                        break
                    else:
                        text = "Филиал %s\n Город %s\n Регион %s" % \
                               (russian_kod.full_filial[kod]["name"],
                                russian_kod.full_filial[kod]["city"],
                                russian_kod.full_filial[kod]["region"])

        bot.send_message(message.chat.id, text)
        users[str(message.chat.id)]["search_kod"] = 0

def search_serial(message):
    if message.text == "Нет" or message.text == "нет":
        users[str(message.chat.id)]["search_serial"] = 0
        bot.send_message(message.chat.id, "Отмена")
    elif message.text == "Найти serial":
        users[str(message.chat.id)]["search_serial"] = 1
        #        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
        bot.send_message(message.chat.id, "Введите серийный номер или наберите Нет для отмены")
    elif users[str(message.chat.id)]["search_serial"] == 1:
        print("sea_err")
        for k, v in dat.items():
            # print("kod %s" % k)
            # print(message.text)
            print(v["serial"])
            if v["serial"] == message.text:

                text = "Филиал %s\n" % \
                       (v["name"])
        bot.send_message(message.chat.id, text)
        users[str(message.chat.id)]["search_serial"] = 0

def thread_search_kod(message):
    th = threading.Thread(target=search_kod, args=(message,))
    th.start()
    th.join()


def search_name(message):
    print("sea_1")
    if message.text == "Нет" or message.text == "нет":
        users[str(message.chat.id)]["new_filial"] = 0
        users[str(message.chat.id)]["search_name"] = 0
        bot.send_message(message.chat.id, "Отмена")
    elif message.text == "Найти по названию":
        users[str(message.chat.id)]["search_name"] = 1
        #        bot.send_message(message.chat.id, "Ожидайте, идет опрос устройства")
        bot.send_message(message.chat.id, "Введите название филиала или наберите Нет для отмены")
    elif users[str(message.chat.id)]["search_name"] == 1:
        print("sea_err")
        text = ""
        for kod, value in russian_kod.full_filial.items():
            #            print(value["name"].find(message.text))
            if len(message.text) < 5:
                bot.send_message(message.chat.id, "Мало символов для поиска")
            elif value["name"].lower().find(message.text.lower()) >= 0:
                print(value["name"])
                text += "%s %s\n" % (kod, value["name"])
        bot.send_message(message.chat.id, text)
        users[str(message.chat.id)]["search_name"] = 0


def subscribe(message, call=""):
    keyboard = telebot.types.InlineKeyboardMarkup()
    print("subscribe_start")
    if message.text == "Подписаться на уведомления":
        for k, v in data.region.items():
            keyboard.row(telebot.types.InlineKeyboardButton(text="%s" % v, callback_data="subscribe_%s" % k))
        try:
            bot.send_message(message.chat.id, "Выберите регион:", reply_markup=keyboard)
        except:
            pass
    elif call.data == "subscribe_back":
        for k, v in data.region.items():
            keyboard.row(telebot.types.InlineKeyboardButton(text="%s" % v, callback_data="subscribe_%s" % k))
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="Выберите регион:",
                                  reply_markup=keyboard)
        except:
            pass
    elif call.data.split("_")[0] == "subscribe":
        region = int(call.data.split("_")[1])
        key(message, region)

    elif call.data.split("_")[0] == "subscribefilial":
        print(call.data)
        kod = call.data.split("_")[1]
        region = call.data.split("_")[2]
        bot.answer_callback_query(call.id, text="Вы подписались")
        try:
            subscrib[kod]
        except:
            subscrib[kod] = []
        try:
            subscrib[kod].remove(message.chat.id)
            print("Вы отписались")
            key(message, region)
        except ValueError:
            print("Вы подписались")
            subscrib[kod].append(message.chat.id)
            key(message, region)

        save_d()


def key(message, region):
    print("key_start")
    open_stat()
    keyboard = telebot.types.InlineKeyboardMarkup()

    for kod, value in dat.items():
        if value["region"] == int(region):
            if stat[kod]["status_t1"] == 1:
                ch1 = "🔵"
            elif stat[kod]["status_t1"] == 0:
                ch1 = "🔴"
            if stat[kod]["status_t2"] == 1:
                ch2 = "🔵"
            elif stat[kod]["status_t2"] == 0:
                ch2 = "🔴"
            try:
                if subscrib[kod].count(message.chat.id) == 1:
                    status = "✅"
                    keyboard.row(
                        telebot.types.InlineKeyboardButton(text="%s%s %s %s" % (ch1, ch2, status, dat[kod]["name"]),
                                                           callback_data="subscribefilial_%s_%s" % (kod, region)))
                else:
                    keyboard.row(telebot.types.InlineKeyboardButton(text="%s%s %s" % (ch1, ch2, dat[kod]["name"]),
                                                                    callback_data="subscribefilial_%s_%s" % (
                                                                    kod, region)))
            except:
                keyboard.row(telebot.types.InlineKeyboardButton(text="%s" % dat[kod]["name"],
                                                                callback_data="subscribefilial_%s_%s" % (kod, region)))

    keyboard.row(telebot.types.InlineKeyboardButton(text="Назад", callback_data="subscribe_back"))
    print("key_stop")
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id,
                              text="Выберите филиал, чтобы подписаться:",
                              reply_markup=keyboard)
    except Exception as n:
        print(n)


def thread_check():
    traceroute()
    threading.Thread(target=check).start()



def ldap_move(message):
    # AD_SEARCH_TREE = 'OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
    AD_SEARCH_TREE = 'CN=Computers,DC=partner,DC=ru'
    # server = "partner.ru"
    # AD_SEARCH_TREE =
    # соединяюсь с сервером. всё ОК
    server = Server("partner.ru")
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    conn.search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE, paged_size=1000,
                attributes=ALL_ATTRIBUTES)
    g = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)',
                                          search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)

    # Создать контейнер
    #   print(conn.add('OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru', 'organizationalUnit'))
    t = ""
    for entry in g:
        name = entry['attributes']['name']
        name_old = name.split("-")[0]
        name_old_3 = name[0:3]
        #        print(name_old_3)
        for i in dat:
            if name_old == i:
                print("Найдет ПК %s" % name)
                t += "Найдет ПК %s" % name
                conn.modify_dn('CN=%s,CN=Computers,DC=partner,DC=ru' % name, 'CN=%s' % name,
                               new_superior='OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')
        for x in range(len(data.pref)):
            if name_old_3 == data.pref[x]:
                print("Найдет ПК %s" % name)
                t += "Найдет ПК %s" % name
                conn.modify_dn('CN=%s,CN=Computers,DC=partner,DC=ru' % name, 'CN=%s' % name,
                               new_superior='OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')

    bot.send_message(message.chat.id, t)


def thread_ldap_move(message):
    threading.Thread(target=ldap_move, args=(message,)).start()



def traceroute():
     threading.Thread(target=tra_timer).start()


def tra_timer():
    bot.send_message(chat_id=765333440, text="Трассировка филиалов начата")
    schedule.every().hour.do(tracer)
    while True:
        schedule.run_pending()
        time.sleep(1)

def tracer():
    kk = ["1", "2", "3", "4", "5"]
    # bot.send_message(chat_id=message.chat.id, text="Трассировка филиалов начата")
    for kod, value in dat.items():
        st_print = 0
        all_text = "Код: %s\nФилиал: %s\nLoopback: %s\n" % (kod, value["name"], value["loopback"])
        text = "Код: %s\nLoopback: %s\n" % (kod, value["loopback"])
        command = "traceroute vrf 100 ya.ru"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=value["loopback"], username=user, password=secret, port=port)
            stdin, stdout, stderr = client.exec_command(command)
            f = stdout.read()
            client.close()
            open(PATH + 'tr.txt', 'wb').write(f)
            time.sleep(1)
            with open(PATH + 'tr.txt') as f:
                lines = f.readlines()
                for line in lines:
                    all_text += line
                    if line.split() == []:
                        pass
                    else:
                        if line.split()[0] in kk:
                            # text += "%s %s\n" % (line.split()[0], line.split()[1])
                            if line.split()[0] == "2" and line.split()[1].split(".")[2] != "33":
                                    st_print = 1
            if st_print == 1:
                print(text)
                bot.send_message(chat_id=765333440, text=all_text)
        except:
            pass
        print(text)
    # bot.send_message(chat_id=765333440, text="Трассировка филиалов заверешена")

def search_serial_all():
    # print("start")
    for key, value in dat.items():
        # print(value["loopback"])
        # sshlist.ssh_serial("10.255.64.2")
        # print(sshlist.ssh_serial("10.255.64.2"))
        dat[key]["serial"] = sshlist.ssh_serial(value["loopback"])

    save_d()

# thread_check()


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.text == "/start":
        new_user(message)


@bot.message_handler(content_types=['text'])
def send_text(message):
    try:
        if users[str(message.chat.id)]["new_filial"] == 1 or users[str(message.chat.id)]["new_filial"] == 2 or \
                users[str(message.chat.id)]["new_filial"] == 3:
            print("newfilial")
            new_filial(message)
    except KeyError:
        print("Mess_err")
        pass

    try:
        if message.text == "Подписаться на уведомления":
            users[str(message.chat.id)]["kod"] = "null"
            subscribe(message)
        elif message.text == "444":
            users[str(message.chat.id)]["ssh"] = 0
            bot.send_message(chat_id=message.chat.id, text="Отмена")
        elif users[str(message.chat.id)]["ssh"] == 1:
            users[str(message.chat.id)]["kod"] = "null"
            users[str(message.chat.id)]["ssh"] = 0
            ssh(message)
        elif message.text == "Добавить":
            new_filial(message)
        elif message.text == "Меню":
            bot.send_message(message.chat.id, "Меню", reply_markup=keyboard.main_menu())
            users[str(message.chat.id)]["kod"] = "null"
            work(message)
        elif message.text == "Регистраторы":
            users[str(message.chat.id)]["kod"] = "null"
            registrator(message)
        elif message.text == "Проверка":
            update_cisco()
            update_registrator()
            bot.send_message(chat_id=message.chat.id, text="Завершено")
        elif message.text.split("_")[0] == "Удалить":
            kod = str(message.text.split("_")[1])
            print(kod)
            dat.pop(kod)
            lease.pop(kod)
            stat.pop(kod)
            save_d()
            bot.send_message(chat_id=message.chat.id, text="Удалено")
        elif message.text == "Проверить ад":
            users[str(message.chat.id)]["kod"] = "null"
            thread_ldap_move(message)
        # elif message.text == "Провайдеры":
        #     ssh_sh_int()

        elif message.text == "Найти по коду":
            users[str(message.chat.id)]["kod"] = "null"
            search_kod(message)
        elif users[str(message.chat.id)]["search_kod"] == 1:
            search_kod(message)
        elif message.text == "Найти по названию":
            search_name(message)

        elif message.text == "Серийник":
            search_serial_all()

        elif users[str(message.chat.id)]["search_serial"] == 1:
            search_serial(message)
        elif message.text == "Найти serial":
            search_serial(message)
        elif users[str(message.chat.id)]["search_name"] == 1:
            search_name(message)
        elif users[str(message.chat.id)]["kod"] != "null":
            print("Ищем мак")
            thread_snmp_cisco_mac(message)
            users[str(message.chat.id)]["kod"] = "null"
        else:
            print("Не известная команда")
    except:
        users[str(message.chat.id)]["search_kod"] = 0
        users[str(message.chat.id)]["search_name"] = 0
        users[str(message.chat.id)]["search_serial"] = 0
        users[str(message.chat.id)]["kod"] = "null"
        users[str(message.chat.id)]["ssh"] = 0


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    #   buy_bot = Buy(message=call.message, call=call)
    if call.data.split("_")[0] == "region":
        work(call.message, call)
    elif call.data.split("_")[0] == "back":
        work(call.message, call)
    elif call.data.split("_")[0] == "market" or call.data.split("_")[0] == "lease" or call.data.split("_")[
        0] == "traffic":
        info_market(call)
    elif call.data.split("_")[0] == "registrator":
        registrator(call.message, call)
    elif call.data.split("_")[0] == "ssh":
        users[str(call.message.chat.id)]["ssh"] = 1
        users[str(call.message.chat.id)]["ssh_loopback"] = call.data.split("_")[1]
        text = "Введите команду SSH для отправки на циску или 444 для отмены\n" \
               "vlan 100 - ping vrf 100 'ip address'\nvlan 200 - ping vrf 200 'ip address'\n" \
               "vlan 400 - ping vrf 100 'ip address'\nvlan 500 - ping vrf 6 'ip address'\n" \
               "isp gateway - ping 'ip address'\n" \
               "sh ip int br - 'Посмотреть айпи на интерфейсе'\n" \
               "sh ip route - 'Посмотреть роуты'"
        bot.send_message(call.message.chat.id, text=text)
    elif call.data.split("_")[0] == "sship":
        ssh_ip_int_br(call)
    elif call.data.split("_")[0] == "traceroute":
        bot.answer_callback_query(text="Ожидайте, запрос занимает некоторое время", callback_query_id=call.id, cache_time=100)
        ssh_traceroute_vrf(call)
    elif call.data.split("_")[0] == "subscribe" or call.data.split("_")[0] == "subscribefilial":
        subscribe(call.message, call)
    elif call.data.split("_")[0] == "sub":
        kod = call.data.split("_")[1]
        try:
            bot.answer_callback_query(callback_query_id=call.id, text=dat[kod]["name"])
        except:
            pass


# bot.infinity_polling(True)
bot.polling()