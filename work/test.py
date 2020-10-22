import paramiko
from work.sql import sql_select, sql_insert, sql_selectone
from sqlite3 import OperationalError


async def scanning_cisco():
    request = f"SELECT ip, hostname FROM cisco"
    user = "itkras"
    passwors = "miccis-96kraS"
    # command = "sh port add"
    command = "show mac address-table"
    rows = await sql_select(request)
    for row in rows:
        ip = row[0]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=ip, username=user, password=passwors, port=22)
        except paramiko.ssh_exception.NoValidConnectionsError:
            print(f"🔴 Нет подключения к циско {ip}")
            # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
            continue
        except paramiko.ssh_exception.AuthenticationException:
            print(f"🔴 Не верный пароль к циско {ip}")
            # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
            continue
        except TimeoutError:
            print(f"🔴 Нет подключения к циско {ip}")
            # await message.answer(f"🔴 Нет подключения к циско {ip} {row[1]}")
            continue
        stdin, stdout, stderr = client.exec_command(command)
        text = stdout.read().decode("utf-8").split("\r\n")
        for line in text:
            try:
                line.split()[3]
            except IndexError:
                continue
            count_vlan = (await sql_selectone(f"SELECT count(ip) FROM cisco_vlan WHERE ip = '{ip}'"))[0]
            if count_vlan == 0:
                await sql_insert(f"INSERT INTO cisco_vlan (ip) VALUES ('{ip}')")
            count_mac = (await sql_selectone(f"SELECT count(ip) FROM cisco_mac WHERE ip = '{ip}'"))[0]
            if count_mac == 0:
                await sql_insert(f"INSERT INTO cisco_mac (ip) VALUES ('{ip}')")
            if line.split()[2] == "STATIC":
                if line.split()[3] != "CPU":
                    mac_old = line.split()[1]
                    mac_old = f"{mac_old.split('.')[0]}{mac_old.split('.')[1]}{mac_old.split('.')[2]}"
                    try:
                        await sql_insert(f"UPDATE cisco_vlan SET '{line.split()[3]}' = '{line.split()[0]}' WHERE ip = '{ip}'")
                        await sql_insert(f"UPDATE cisco_mac SET '{line.split()[3]}' = '{mac_old}' WHERE ip = '{ip}'")
                    except OperationalError as n:
                        if str(n).split(":")[0] == "no such column":
                            await sql_insert(f"ALTER TABLE cisco_vlan ADD '{line.split()[3]}' text")
                            await sql_insert(f"ALTER TABLE cisco_mac ADD '{line.split()[3]}' text")
                            await sql_insert(
                                f"UPDATE cisco_vlan SET '{line.split()[3]}' = '{line.split()[0]}' WHERE ip = '{ip}'")
                            await sql_insert(
                                f"UPDATE cisco_mac SET '{line.split()[3]}' = '{mac_old}' WHERE ip = '{ip}'")
