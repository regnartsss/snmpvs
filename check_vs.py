from pysnmp.hlapi import *
from pprint import pprint
import json
import os
import telebot
from config import bot
import time


mib = { #   "ifInOctets_isp1": "1.3.6.1.2.1.31.1.1.1.6.1",
        #   "ifOutOctets_isp1": "1.3.6.1.2.1.31.1.1.1.10.1",
        #   "ifInOctets_isp2": "1.3.6.1.2.1.31.1.1.1.6.2",
        #   "ifOutOctets_isp2": "1.3.6.1.2.1.31.1.1.1.10.2",

           "ifInOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.6.25",
           "ifOutOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.10.25",
           "ifInOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.6.26",
           "ifOutOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.10.26"
           }

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'

PATH = find_location()
global dat, users, stat, lease, subscrib



def open_all():
    global users, dat, stat, subscrib
    #    bot.send_message(765333440, "sss")
    with open(PATH + 'users.json', 'rb') as f:
        users = json.load(f)
    with open(PATH + 'dat.json', 'rb') as f:
        dat = json.load(f)
    with open(PATH + 'stat.json', 'rb') as f:
        stat = json.load(f)
    # with open(PATH + 'lease.json', 'rb') as f:
    #     lease = json.load(f)
    with open(PATH + 'subscrib.json', 'rb') as f:
        subscrib = json.load(f)


def save_stat():
    global stat
    # with open(PATH + 'dat.json', 'w', encoding="utf-16") as f:
    #     json.dump(dat, f)
    # with open(PATH + 'dat.json', 'rb') as f:
    #     dat = json.load(f)
    # with open(PATH + 'users.json', 'w', encoding="utf-16") as f:
    #     json.dump(users, f)
    # with open(PATH + 'users.json', 'rb') as f:
    #     users = json.load(f)
    with open(PATH + 'stat.json', 'w', encoding="utf-16") as f:
        json.dump(stat, f)
    with open(PATH + 'stat.json', 'rb') as f:
        stat = json.load(f)
    # with open(PATH + 'lease.json', 'w', encoding="utf-16") as f:
    #     json.dump(lease, f)
    # with open(PATH + 'lease.json', 'rb') as f:
    #     lease = json.load(f)



def snmp(kod):
    try:
        stat[kod]["0"]
    except:
        stat[kod] = {"0": {},
                          "1": {}}
    d = {}
#    print("филиал %s" % kod)
    for i, v in mib.items():
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',

                               authProtocol=usmHMACSHAAuthProtocol
                               ),
                   UdpTransportTarget((dat[kod]["loopback"], 161)),
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
#                print(' = '.join([x.prettyPrint() for x in varBind]))
                m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                d[i] = m

    stat[kod]["0"] = stat[kod]["1"]
    stat[kod]["1"] = d


def check():
    i = 0
    while i < 2:
        open_all()
#        time.sleep(30)
        for kod, v in dat.items():
            snmp(kod)
            try:
                Intunnel1 = int(stat[kod]["1"]["ifInOctets_isp1_tunnel"]) - int(stat[kod]["0"]["ifInOctets_isp1_tunnel"])
                Intunnel2 = int(stat[kod]["1"]["ifInOctets_isp2_tunnel"]) - int(stat[kod]["0"]["ifInOctets_isp2_tunnel"])
                Outtunnel1 = int(stat[kod]["1"]["ifOutOctets_isp1_tunnel"]) - int(stat[kod]["0"]["ifOutOctets_isp1_tunnel"])
                Outtunnel2 = int(stat[kod]["1"]["ifOutOctets_isp2_tunnel"]) - int(stat[kod]["0"]["ifOutOctets_isp2_tunnel"])
                t = "%s\n%s\n" % (dat[kod]["name"], dat[kod]["sysName"])
                #         print("%s нет траффика" % t)
                # print("Входящий 1 - %s" % Intunnel1)
                # print("Исходящий 1 - %s" % Outtunnel1)
                # print("Входящий 2 - %s" % Intunnel2)
                # print("Исходящий 2 - %s" % Outtunnel2)
                text = "Филиал %s\n" % kod
                try:
                    stat[kod]["status_t1"]
                    stat[kod]["status_t2"]
                except:
                    stat[kod]["status_t1"] = 3
                    stat[kod]["status_t2"] = 3
                if Intunnel1 > 0 and Outtunnel1 > 0:
                     status = 1

                     if stat[kod]["status_t1"] ==  status:
                         pass
                     else:
                         text +="🔵 Основной провайдер работает"
                         stat[kod]["status_t1"] = 1
                if Intunnel2 > 0 and Outtunnel2 > 0:
                    status = 1
                    if stat[kod]["status_t2"] == status:
                       pass
                    else:
                       text += "🔵 Резервный провайдер работает"
                       stat[kod]["status_t2"] = 1
                if Intunnel1 == 0 and Outtunnel1 == 0:
                    status = 0
                    if stat[kod]["status_t1"] == status:
                        pass
                    else:
                        text += "🔴 🔵 Основной провайдер не работает"
                        stat[kod]["status_t1"] = 0
                if Intunnel2 == 0 and Outtunnel2 == 0:
                    status = 0
                    if stat[kod]["status_t2"] == status:
                        pass
                    else:
                        text += "🔵 🔴 Резервный провайдер не работает"
                        stat[kod]["status_t2"] = 0

                # if stat[kod]["status_t1"] == 0 and stat[kod]["status_t2"] == 0:
                #     text += "🔴 🔴 не доступен"
                # if stat[kod]["status_t1"] == 1 and stat[kod]["status_t2"] == 1:
                #     text += "🔵 🔵 доступен"


                if text == "Филиал %s\n" % kod:
                    pass
                else:
                    for k in subscrib[kod]:

                        bot.send_message(chat_id=k, text="%s\n  %s" %(dat[kod]["name"], text))

            except Exception as n:
                print(n)
                print("Ошибка филиала %s"%kod)
                pass
        save_stat()

 #        t += "\nUptime %s\n\n" % (GetTime(stat[kod]["1"]["sysUpTime"]))
#          t += "🔵 Основной провайдер\n⬇️ In %s MB |⬆️ Out %s MB\n\n🔴 Резервный провайдер\n ⬇️ In %s MB |⬆️ Out %s MB\n" % \
#               (int(int(stat[kod]["1"]["ifInOctets_isp1"]) / 1048576),
#                int(int(stat[kod]["1"]["ifOutOctets_isp1"]) / 1048576),
#                int(int(stat[kod]["1"]["ifInOctets_isp2"]) / 1048576),
#                int(int(stat[kod]["1"]["ifOutOctets_isp2"]) / 1048576))
#
#          t += "\n🔵 Tunnel 1\n ⬇️ In %s MB | ⬆️ Out %s MB\n ⏬ In %.2f MB | ⏫ Out %.2f MB \n" % (
#              int(int(stat[kod]["1"]["ifInOctets_isp1_tunnel"]) / 1048576),
#              int(int(stat[kod]["1"]["ifOutOctets_isp1_tunnel"]) / 1048576),
#              Intunnel1 / 1048576, Outtunnel1 / 1048576)
# #
#          t += "\n🔴 Tunnel 2\n ⬇️ In %s MB | ⬆️ Out %s MB\n ⏬ In %.2f MB | ⏫ Out %.2f MB" % (
#              int(int(stat[kod]["1"]["ifInOctets_isp2_tunnel"]) / 1048576),
#              int(int(stat[kod]["1"]["ifOutOctets_isp2_tunnel"]) / 1048576),
#              Intunnel2 / 1048576, Outtunnel2 / 1048576)
#
#         bot.send_message(chat_id=765333440, text=t)


