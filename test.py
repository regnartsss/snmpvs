import work.sql
from pysnmp.hlapi import *


# oid_all = sql.sql_selectone_no_await(
#         f"SELECT In_isp1, Out_isp1, In_isp2, Out_isp2 FROM status WHERE loopback = '10.255.64.20'")

oid = "1.3.6.1.2.1.31.1.1.1.6.25"
# d = []
# for oid in oid_all:
errorIndication, errorStatus, errorIndex, varBinds = next(
    getCmd(SnmpEngine(),
           UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
           UdpTransportTarget(('10.255.64.21', 161)),
           ContextData(),
           ObjectType(ObjectIdentity(oid)))
)

if errorIndication:
    print(errorIndication)
    # "No SNMP response received before timeout"
    print("тут ошибка")
    # r = await sql.sql_selectone(f"SELECT In1_one, Out1_one,In2_one, Out2_one FROM status WHERE loopback = '{loopback}'")
    # d.append(r[0])
    # d.append(r[1])
    # d.append(r[2])
    # d.append(r[3])

#            for k in subscrib[kod]:
#                bot.send_message(chat_id=k, text="%s\n  %s" % (dat[kod]["name"], text))
elif errorStatus:
    print('%s at %s' % (errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
else:
    for varBind in varBinds:
        #                print(' = '.join([x.prettyPrint() for x in varBind]))
        m = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
        print(m)