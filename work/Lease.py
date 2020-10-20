import asyncssh
from work.sql import sql_selectone
import re
from pprint import pprint


async def lease(callback_data):
    print(callback_data)
    kod = callback_data["kod"]
    vlan = callback_data["data"]
    loopback = await sql_selectone(f"SELECT loopback, {vlan} FROM zabbix WHERE kod = {kod}")
    command = "show ip dhcp binding"
    # command = "sh arp vrf 100"

    user = 'operator'
    secret = '71LtkJnrYjn'
    try:
        ip_old = loopback[1].split(".")[:3]
    except AttributeError:
        return "Не возможно получить данные с микротика"
    text_all=""
    async with asyncssh.connect(loopback[0], username=user, password=secret, known_hosts=None) as conn:
        result = await conn.run(command, check=True)
        text = result.stdout.split("\n")
        for line in text:
            if line.split(".")[:3] == ip_old:
                # print(line)
                t = line.split()
                ip = t[0]
                mac = t[1].split(".")
                mac = f"{mac[0]}{mac[1]}{mac[2]}"
                try:
                    if t[7] == 'Automatic':
                        if t[6] == "PM":
                            ss = int(t[5].split(":")[0]) + 12
                            ss = "%s:%s" % (ss, t[5].split(":")[1])
                            data = "%s/%s/%s %s" % (t[3], t[2], t[4], ss)
                        else:
                            data = "%s/%s/%s %s" % (t[3], t[2], t[4], t[5])
                except IndexError:
                    data = ""
                text_all += "%s /%s %s\n" % (ip, mac, data)
        if text_all == "":
            return "Нет адресов"
        else:
            return text_all
