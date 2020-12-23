import asyncssh
from work.sql import sql_selectone, sql_select
import re
from pprint import pprint
import paramiko
import sys
import telnetlib


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
        return await search_mac(kod, vlan, text_all)


async def search_mac(kod, vlan, text_all):
    request = f"SELECT ip, hostname FROM cisco WHERE kod = {kod}"
    user = "itkras"
    passwors = "miccis-96kraS"
    # command = "sh port add"
    command_one = "show mac address-table"
    command_two = "show int status"
    rows = await sql_select(request)
    t = ""
    mac = []
    for row in rows:
        temp = []
        ip = row[0]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=ip, username=user, password=passwors, port=22)
        except paramiko.ssh_exception.NoValidConnectionsError:
            print(f"Нет подключения к циско {ip} {row[1]}")
            continue
        stdin, stdout, stderr = client.exec_command(command_two)
        text = stdout.read().decode("utf-8").split("\r\n")
        for line in text:
            # print(line)
            try:
                if line.split()[-4] == 'trunk':
                    temp.append(line.split()[0])
                    # print(line)
                # print(line.split()[-4])
            except IndexError:
                print("temp")
        # try:
        #     client.connect(hostname=ip, username=user, password=passwors, port=22)
        # except paramiko.ssh_exception.NoValidConnectionsError:
        #     print(f"Нет подключения к циско {ip} {row[1]}")
        #     continue
        print(temp)
        try:
            client.connect(hostname=ip, username=user, password=passwors, port=22)
        except paramiko.ssh_exception.NoValidConnectionsError:
            print(f"Нет подключения к циско {ip} {row[1]}")
            continue
        stdin, stdout, stderr = client.exec_command(command_one)
        text = stdout.read().decode("utf-8").split("\r\n")
        for line in text:

            try:
                if str(line.split()[0]) == str(vlan[4:7]):
                    if str(line.split()[3]) not in temp:
                        # print(line)
                        # print(text_all.split("\n"))
                        text_list = text_all.split("\n")
                        # print(text_list)
                        text_all = ''
                        for text in text_list:
                            mac = text.split()[1][1:]
                            mac_old = ''.join(line.split()[1].split("."))
                            if mac_old == mac:
                                text += f" {ip} {line.split()[3]}"
                            text_all += text + '\n'

                            # mac.append()
            except IndexError:
                pass
    return text_all

