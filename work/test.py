import asyncio
import aiosnmp
from pysnmp.hlapi import *


def oid():
    loopback = "10.255.64.46"
    mib = "1.3.6.1.2.1.31.1.1.1.1"
    i = 0
    in_isp1, out_isp1, in_isp2, out_isp2 = "0", "0", "0", "0"
    while i < 35:
        i += 1
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   UsmUserData(userName='dvsnmp', authKey='55GjnJwtPfk', authProtocol=usmHMACSHAAuthProtocol),
                   UdpTransportTarget((str(loopback), 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(f"{mib}.{i}"))
                   ))

        if error_indication:
            print(error_indication)
        elif error_status:
            print('%s at %s' % (error_status.prettyPrint(),
                                error_index and var_binds[int(error_index) - 1][0] or '?'))
        else:
            for varBind in var_binds:

                oi = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[1])
                #                print(oi)
                if oi == "Tu0":
                    num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    in_isp1 = "1.3.6.1.2.1.31.1.1.1.6.%s" % num_oid
                    out_isp1 = "1.3.6.1.2.1.31.1.1.1.10.%s" % num_oid
                elif oi == "Tu1":
                    num_oid = (' = '.join([x.prettyPrint() for x in varBind]).split("= ")[0].split(".")[6])
                    in_isp2 = "1.3.6.1.2.1.31.1.1.1.6.%s" % num_oid
                    out_isp2 = "1.3.6.1.2.1.31.1.1.1.10.%s" % num_oid
                else:
                    pass
                print(in_isp1)
                print(in_isp2)
                print(out_isp1)
                print(out_isp2)


oid()