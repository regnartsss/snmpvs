from work import sql
from pysnmp.hlapi import *
import time
trassir = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11',
    'Не работает камера:': '1.3.6.1.4.1.3333.1.8',
    'ip address ': '1.3.6.1.4.1.3333.1.9',
    'Прошивка ': '1.3.6.1.4.1.3333.1.10'

}
trassirusercam = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11',
    u'\U0001F50D' + ' Не работает камера:': '1.3.6.1.4.1.3333.1.8'
}
trassiruser = {
    u'\U0001F4BB' + ' Сервер': '1.3.6.1.4.1.3333.1.7',
    u'\U0001F4BD' + ' Диски': '1.3.6.1.4.1.3333.1.3',
    u'\U0001F4C3' + ' Глубина архива дней': '1.3.6.1.4.1.3333.1.2',
    u'\U0001F3A5' + ' Камеры': '1.3.6.1.4.1.3333.1.5',
    u'\U0000231B' + ' Время работы сервера ': '1.3.6.1.4.1.3333.1.11'

}
def snmpregist(ip):
            d = []
            for r in trassir:
                #        print(r)
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(), CommunityData('dssl'), UdpTransportTarget((ip, 161)),
                           ContextData(), ObjectType(ObjectIdentity(trassir[r]))))
                if errorIndication:
                    #                print(errorIndication)
                    st = "0"
                    break
                elif errorStatus:
                    print('%s at %s' % (
                    errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    continue
                else:
                    for varBind in varBinds:
                        status = (' ='.join([x.prettyPrint() for x in varBind])).split("=")[1]
                        # print(status)
                        d.append(status)
            return d

async def start_check_regisatrator():
    # try:
    rows = sql.sql_select_no_await("SELECT ip FROM registrator")
    # except:
    #     time.sleep(300)
    #     start_check()
    for row in rows:
        # print(snmpregist(row[0]))
        reg = snmpregist(row[0])
        # print(reg)
        if reg == []:
            pass
        else:
            sql.sql_insert_no_await(f"Update registrator SET disk = '{reg[1]}', arhive = '{reg[2]}', cam = '{reg[3]}', cam_down ='{reg[5]}', uptime = '{reg[4]}', firmware = '{reg[7]}' WHERE ip = '{row[0]}'")
        # try:
        #     (ip, name, registr, stregistr) = tuple(row)
        #     st, statusall = "", ""
        #     s, r = 0, 0
        #     #        if len(registr.split(";")) > 1:
        #     #            print("Больше двух")
        #     #       print("registra " + registr)
        #     #        print(len(registr.split(";")))
        #     if stregistr == "1":
        #         #            print(registr + " не проверяется")
        #         continue
        #     else:
        #         while r < len(registr.split(";")):
        #             st = snmpregist(registr.split(";")[r])[1]
        #             statusall = statusall + st
        #             r += 1
        #
        #         #        print(statusall)
        #         if statusall == stregistr:
        #             continue
        #         else:
        #             r = 0
        #             stsend = ''
        #             while r < len(statusall.split(";")) - 1:
        #                 if stregistr == "":
        #
        #                     stsend = statusall
        #
        #                     # sendreg(statusall, name, reg=registr, st=1)
        #                     break
        #                 elif statusall.split(";")[r] == "0":
        #                     if statusall.split(";")[r] == stregistr.split(";")[r]:
        #                         stsend = stsend + statusall.split(";")[r] + ";"
        #                         r += 1
        #                         continue
        #                     else:
        #                         name_server = stregistr.split(";")[r].split(":")[4]
        #                         stsend = stsend + statusall.split(";")[r]
        #                         #                        print('Не доступен '+name_server)
        #
        #                         # sendreg(statusall.split(";")[r], name, reg=registr)
        #                 elif stregistr.split(";")[r] == "0":
        #                     stsend = stsend + statusall.split(";")[r]
        #                     #                    print('Доступен')
        #                     # sendreg(statusall.split(";")[r], name, text="Доступен", reg=registr, st=1)
        #
        #                 else:
        #                     if statusall.split(";")[r] == stregistr.split(";")[r]:
        #                         stsend = stsend + statusall.split(";")[r] + ";"
        #                         r += 1
        #                         continue
        #                     else:
        #                         stat = statusall.split(";")[r]
        #                         stre = stregistr.split(";")[r]
        #                         #                        print(stat+" = "+ stregistr)
        #                         if stat.split(":")[2] != stre.split(":")[2]:
        #                             if stat.split(":")[2] == "OK":
        #                                 #                                print("нет ошибка диска")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 #                                print(registr)
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с жестким диском решена",
        #                                 #         reg=registr, st=1)
        #                             else:
        #                                 #                                print("Ошибка диска")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 #                                print (stsend)
        #                                 #                                print(registr)
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с жестким диском",
        #                                 #         reg=registr, st=1)
        #                         elif stat.split(":")[4] != stre.split(":")[4]:
        #                             camdown = re.findall('\d+', stat.split(":")[4].split("/")[0])
        #                             cam = re.findall('\d+', stat.split(":")[4].split("/")[1])
        #                             #                            print (camdown)
        #                             #                            print (cam)
        #                             if camdown < cam:
        #                                 #                                print("Ошибка камеры")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 # sendreg(statusall.split(";")[r], name, text="Проблема с камерой", reg=registr,
        #                                 #         st=2)
        #                             elif camdown == cam:
        #                                 #                                print("Камеры ОК")
        #                                 stsend = stsend + statusall.split(";")[r]
        #                                 # sendreg(statusall.split(";")[r], name, text="Камеры работают", reg=registr,
        #                                 #         st=1)
        #                         else:
        #                             stsend = stsend + statusall.split(";")[r]
        #
        #                 stsend = stsend + ";"
        #                 #                print("r1" + str(r))
        #                 r += 1
        #             #                print("r2" + str(r))
        #             #
        #             # sql_insert("UPDATE snmp SET stregistr = '" + stsend + "' WHERE registr = '" + registr + "'")
        # except Exception as e:
        #     print(e)
            # if str(e) == "list index out of range":
            #     bot.send_message(ADMIN, "Ошибка проверки регистратора, добавлен новый регистратор " + registr)
            #     sql_insert("UPDATE snmp SET stregistr = '' WHERE registr = '" + str(registr) + "'")
            # #         print("Ошибка проверки регистратора "+ str(e))
            # else:
            #     bot.send_message(ADMIN, "Ошибка проверки регистратора " + str(registr) + " " + str(e))
            #     sql_insert("UPDATE snmp SET stregistr = '' WHERE registr = '" + str(registr) + "'")
            #     continue
    # sr += 1
    # savestatus(sr, timesr, p=2)
    # select_registr()


# check()

