from work.sql import sql_select, sql_insert
import asyncssh
from sqlite3 import OperationalError, IntegrityError
from loader import bot

async def counter():
    user = 'operator'
    secret = '71LtkJnrYjn'
    command = "show ip dhcp binding"
    rows = await sql_select("SELECT loopback, name, kod FROM zabbix WHERE sdwan = 1")
    for row in rows:
            try:
                async with asyncssh.connect(row[0], username=user, password=secret, known_hosts=None) as conn:
                    result = await conn.run(command, check=True)
                    text = result.stdout.split("\n")
                    for line in text:
                        if line.split():
                            if line.split()[1].split(".")[0] == '0050':
                                print(line.split())
                                ip = line.split()[0]
                                mac = line.split()[1]
                                lease = line.split()[3]
                                temp = line.split()[4]
                                try:
                                    await sql_insert(f"INSERT or REPLACE INTO bd_counter (name, kod, ip, lease, temp, mac) VALUES ('{row[1]}',{row[2]},'{ip}','{lease}','{temp}','{mac}')")
                                except OperationalError:
                                    await create_bd_counter()
                                    await sql_insert(f"INSERT INTO bd_counter (name, kod, ip, lease, temp, mac) VALUES ('{row[1]}',{row[2]},'{ip}','{lease}','{temp}','{mac}')")

                                    # print(f"UPDATE bd_counter SET ip = '{ip}', lease = '{lease}', temp = '{temp}' WHERE mac = '{mac}'")
                                    # await sql_insert(f"UPDATE bd_counter SET ip = '{ip}', lease = '{lease}', temp = '{temp}' WHERE mac = '{mac}'")
                                    # print("ff")
                            if line.split()[1].split(".")[0] == '7c2f' or line.split()[1].split(".")[0] == '0c11':
                                ip = line.split()[0]
                                mac = line.split()[1]
                                lease = line.split()[3]
                                temp = line.split()[4]
                                try:
                                    await sql_insert(f"INSERT or REPLACE INTO bd_phone VALUES ('{row[1]}',{row[2]},'{ip}','{lease}','{temp}','{mac}')")
                                except OperationalError:
                                    await create_bd_phone()
                                    await sql_insert(f"INSERT INTO bd_phone (name, kod, ip, lease, temp, mac) VALUES ('{row[1]}',{row[2]},'{ip}','{lease}','{temp}','{mac}')")


            except TimeoutError:
                print("timeout", row[0])


async def counter_mess(user_id):
    rows = await sql_select("SELECT name, ip FROM bd_counter ORDER BY name")
    text = ""
    for row in rows:
        text += f"{row[0]} {row[1]} \n"
        if len(text) > 4000:
            await bot.send_message(user_id, text)
            text = ""
    print(len(text))
    return text

async def phone_mess(user_id):
    rows = await sql_select("SELECT name, ip FROM bd_phone ORDER BY name")
    text = ""
    for row in rows:
        text += f"{row[0]} {row[1]} \n"
        if len(text) > 4000:
            await bot.send_message(user_id, text)
            text = ""
    print(len(text))
    return text

async def create_bd_counter():
    request = """CREATE TABLE bd_counter (
    name  TEXT,
    kod   INT,
    ip    TEXT,
    lease TEXT,
    temp TEXT,
    mac   TEXT PRIMARY KEY
);
"""
    await sql_insert(request)


async def create_bd_phone():
    request = """CREATE TABLE bd_phone (
    name  TEXT,
    kod   INT,
    ip    TEXT,
    lease TEXT,
    temp TEXT,
    mac   TEXT PRIMARY KEY
);
"""
    await sql_insert(request)