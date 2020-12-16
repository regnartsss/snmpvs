from work.sql import sql_select, sql_insert
import asyncssh
from sqlite3 import OperationalError, IntegrityError
from loader import bot


async def counter():
    user = 'operator'
    secret = '71LtkJnrYjn'
    command = "show ip dhcp binding"
    mac_all = ['7085.c24f', '7085.c29e', 'b4a3.822c', '7085.c2a4', '7085.c291', 'b4a3.8201', '7085.c2be', '7085.c259',
               '7085.c263', 'b4a3.8252', '7085.c2ae', '7085.c27d', '7085.c2dd', '7085.c290', '7085.c2dc']
    mac_registrator = ['8ce7', 'b4a3', '7085']
    rows = await sql_select("SELECT loopback, name, kod FROM zabbix WHERE sdwan = 1")
    for row in rows:
        try:
            async with asyncssh.connect(row[0], username=user, password=secret, known_hosts=None) as conn:
                result = await conn.run(command, check=True)
                text = result.stdout.split("\n")
                for line in text:
                    if line.split():
                        mac_old_videoregistrator = '.'.join(line.split()[1].split(".")[0:2])
                        mac = line.split()[1].split(".")[0]
                        if line.split()[1].split(".")[0] == '0050':
                            await write_bd(line, row[1], row[2], 'counter')
                        if line.split()[1].split(".")[0] == '7c2f' or line.split()[1].split(".")[0] == '0c11':
                            await write_bd(line, row[1], row[2], 'phone')
                        if line.split()[1].split(".")[0] == '74da' or line.split()[1].split(".")[0] == 'ap08':
                            await write_bd(line, row[1], row[2], 'edimax')
                        # if mac in mac_registrator:
                        #     if mac_old_videoregistrator not in mac_all:
                        #         await write_bd(line, row[1], row[2], 'registrator')

        except TimeoutError:
            print("timeout", row[0])


async def write_bd(line, name, kod, data):
    ip = line.split()[0]
    mac = line.split()[1]
    lease = line.split()[3]
    temp = line.split()[4]
    try:
        await sql_insert(
            f"INSERT or REPLACE INTO bd_{data} VALUES ('{name}',{kod},'{ip}','{lease}','{temp}','{mac}')")
    except OperationalError:
        await create_bd(data)
        await sql_insert(
            f"INSERT INTO bd_{data} (name, kod, ip, lease, temp, mac) VALUES ('{name}',{kod},'{ip}','{lease}','{temp}','{mac}')")


async def mess(user_id, data):
    rows = await sql_select(f"SELECT name, ip FROM bd_{data} ORDER BY name")
    text = ""
    for row in rows:
        text += f"{row[0]} {row[1]} \n"
        if len(text) > 4000:
            await bot.send_message(user_id, text)
            text = ""
    return text


async def create_bd(data):
    request = f"""CREATE TABLE bd_{data} (
    name  TEXT,
    kod   INT,
    ip    TEXT,
    lease TEXT,
    temp TEXT,
    mac   TEXT
);
"""
    await sql_insert(request)


async def mess_uptime(user_id):
    rows = await sql_select(f"SELECT name, uptime FROM zb_st LEFT JOIN zabbix ON zb_st.kod = zabbix.kod ORDER BY uptime")
    text = ""
    for row in rows:
        text += f"{row[0]} {row[1]} \n"
        if len(text) > 4000:
            await bot.send_message(user_id, text)
            text = ""
    return text
