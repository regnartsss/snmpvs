from pysnmp.hlapi import *
from pprint import pprint
import json
import os
import telebot
from config import bot
import time
from datetime import datetime, timedelta

mib = { #   "ifInOctets_isp1": "1.3.6.1.2.1.31.1.1.1.6.1",
        #   "ifOutOctets_isp1": "1.3.6.1.2.1.31.1.1.1.10.1",
        #   "ifInOctets_isp2": "1.3.6.1.2.1.31.1.1.1.6.2",
        #   "ifOutOctets_isp2": "1.3.6.1.2.1.31.1.1.1.10.2",

           "ifInOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.6.%s",
           "ifOutOctets_isp1_tunnel": "1.3.6.1.2.1.31.1.1.1.10.%s",
           "ifInOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.6",
           "ifOutOctets_isp2_tunnel": "1.3.6.1.2.1.31.1.1.1.10"
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


def oid(kod):
    oid = "1.3.6.1.2.1.31.1.1.1.1"
    i = 0
    print(kod)
    while i < 35:
        i+=1
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk',

                               authProtocol=usmHMACSHAAuthProtocol
                               ),
                   UdpTransportTarget((dat[kod]["loopback"], 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity("%s.%s" %(oid, i)))
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
                    print(numoid)
                    stat[kod]["oid"]["ifInOctets_isp1_tunnel"] = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    stat[kod]["oid"]["ifOutOctets_isp1_tunnel"] = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                elif oi == "Tu1":
                    numoid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    print(numoid)
                    stat[kod]["oid"]["ifInOctets_isp2_tunnel"] = "1.3.6.1.2.1.31.1.1.1.6.%s" % numoid
                    stat[kod]["oid"]["ifOutOctets_isp2_tunnel"] = "1.3.6.1.2.1.31.1.1.1.10.%s" % numoid
                else:

                    pass
    save_stat()
    #    print(stat[kod])
# open_all()
# oid("3615")

def snmp(kod):

    try:
        stat[kod]["0"]
    except:
        stat[kod] = {"0": {},
                          "1": {}}
    try:
        stat[kod]["oid"]
    except:
        stat[kod]["oid"] = {}
        oid(kod)

    d = {}
    for i, v in stat[kod]["oid"].items():
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
            # "No SNMP response received before timeout"
            d = stat[kod]["1"]
            break
#            for k in subscrib[kod]:
#                bot.send_message(chat_id=k, text="%s\n  %s" % (dat[kod]["name"], text))
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

                #"No SNMP response received before timeout"
                Intunnel1 = int(stat[kod]["1"]["ifInOctets_isp1_tunnel"]) - int(stat[kod]["0"]["ifInOctets_isp1_tunnel"])
                Intunnel2 = int(stat[kod]["1"]["ifInOctets_isp2_tunnel"]) - int(stat[kod]["0"]["ifInOctets_isp2_tunnel"])
                Outtunnel1 = int(stat[kod]["1"]["ifOutOctets_isp1_tunnel"]) - int(stat[kod]["0"]["ifOutOctets_isp1_tunnel"])
                Outtunnel2 = int(stat[kod]["1"]["ifOutOctets_isp2_tunnel"]) - int(stat[kod]["0"]["ifOutOctets_isp2_tunnel"])

                # print(Intunnel1)
                # print(Outtunnel1)
                # print(Intunnel2)
                # print(Outtunnel2)

                if Intunnel1 > 0 or Outtunnel1 >0:
                    status1 = 1
                elif  Intunnel1 == 0 or Outtunnel1 ==0:
                    status1 = 0
                else:
                    print("Ошибка 1")

                if Intunnel2 > 0 or Outtunnel2 >0:
                    status2 = 1
                elif Intunnel2 == 0 or Outtunnel2 ==0:
                    status2 = 0
                else:
                    print("Ошибка 2")
                # print("%s" % status1)
                # print("%s" % status2)


                t = "%s\n%s\n" % (dat[kod]["name"], dat[kod]["sysName"])
                text = "Филиал %s\n" % kod
                try:
                    stat[kod]["status_t1"]
                    stat[kod]["status_t2"]
                except:
                    stat[kod]["status_t1"] = 3
                    stat[kod]["status_t2"] = 3

                if status1 == 0 and status2 == 0:
                    if stat[kod]["status_t1"] == status1 and stat[kod]["status_t2"] == status2:
                        continue
                    else:
                        text += "🔴 🔴 Филиал не доступен \nLoopback: %s\nISP_1: %s\nISP_2: %s" % \
                                (dat[kod]["loopback"], dat[kod]["ISP1"], dat[kod]["ISP2"])
                        print("Филиал не доступен")
                        stat[kod]["status_t1"] = 0
                        stat[kod]["status_t2"] = 0
                        send_mess(kod, text)
                elif status1 == 1 and status2 == 0:
                    if stat[kod]["status_t1"] == status1 and stat[kod]["status_t2"] == status2:
                        continue
                    else:
                        text += "🔵 🔴 Резервный провайдер не работает\n%s\nISP_2: %s"%(dat[kod]["ISP2_NAME"],dat[kod]["ISP2"])

                        print("Резервный не работает")
                        stat[kod]["status_t1"] = 1
                        stat[kod]["status_t2"] = 0
                        send_mess(kod, text)


                elif status1 == 0 and status2 == 1:
                    if stat[kod]["status_t1"] == status1 and stat[kod]["status_t2"] == status2:
                        continue
                    else:
                        text += "🔴 🔵 Основной провайдер не работает\n%s\nISP_1: %s"%(dat[kod]["ISP1_NAME"],dat[kod]["ISP1"])
                        print("Основной не работает")
                        stat[kod]["status_t1"] = 0
                        stat[kod]["status_t2"] = 1
                        send_mess(kod, text)


                elif status1 == 1 and status2 == 1:
                    if stat[kod]["status_t1"] == status1 and stat[kod]["status_t2"] == status2:
                        continue
                    else:
                        text += "🔵 🔵 Филиал работает"
                        print("Филиал работает")
                        stat[kod]["status_t1"] = 1
                        stat[kod]["status_t2"] = 1
                        send_mess(kod, text)
                else:
                    pprint("тест")

                # if text != "Филиал %s\n" % kod:
                #     #      pass
                #     # else:
                #     #      for k in subscrib[kod]:
                #     #
                #     bot.send_message(chat_id=765333440, text="%s\n  %s" % (dat[kod]["name"], text))

            except Exception as n:
                print(n)
                print("Ошибка филиала %s" % kod)
                pass
        save_stat()
        monitoring()
def send_mess(kod, text):
    for k in subscrib[kod]:
        bot.send_message(chat_id=k, text="%s\n  %s" % (dat[kod]["name"], text))

def data_monitor():
    return datetime.today().strftime("%H:%M:%S %d/%m/%Y")


def monitoring():

    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        i = 1
        tab = []
        null = telebot.types.InlineKeyboardButton(text="   ", callback_data="sub")
        #    tab.append(telebot.types.InlineKeyboardButton(text="мониторинг", callback_data="sub"))
        #    keyboard.row(null,null,null,null,null,null,null)
        tab = []
        text = ""
        colum = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]
        colum_old = [3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51]
        for kod, value in dat.items():
            ch1 = "🔵"
            ch2 = "🔵"

            if stat[str(kod)]["status_t1"] == 1:
                 ch1 = "🔵"
            elif stat[str(kod)]["status_t1"] == 0:
                 ch1 = "🔴"
            if stat[str(kod)]["status_t2"] == 1:
                ch2 = "🔵"
            elif stat[str(kod)]["status_t2"] == 0:
                ch2 = "🔴"
            if dat[str(kod)]["ISP1"] == "unassigned":
                ch1 = "⚪"
            if dat[str(kod)]["ISP2"] == "unassigned":
                ch2 = "⚪"
            #
            # print("филиал %s" % kod)
            # print("%s %s "% (ch1, ch2))
            text += "%s%s %s %s\n" % (ch1, ch2, kod, dat[str(kod)]["name"])
            tab.append(telebot.types.InlineKeyboardButton(text="%s %s%s " % (kod, ch1, ch2),callback_data="sub_%s"%kod))
            if i in colum_old:
                keyboard.row(*tab)
                tab = []
            i += 1
        keyboard.row(*tab)
#        bot.send_message(chat_id=765333440, text=text)
        bot.edit_message_text(chat_id="@sdwan_monitoring", message_id=21, text="<---------------->\n Время проверки %s" % data_monitor(), reply_markup=keyboard)
    except:
        pass
    # bot.edit_message_text(chat_id="-462518174", message_id=567 ,text="<---------------->\n Время проверки %s" % data_monitor(), reply_markup=keyboard)
    # bot.send_message(chat_id="765333440", text="<---------------->\n Время проверки %s" % data_monitor(),
    #                  reply_markup=keyboard)


