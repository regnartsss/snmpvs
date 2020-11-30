from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql
import re
import socket


class SearchFilial(StatesGroup):
    Filial = State()
    Kod = State()
    Serial = State()
    Ip = State()


async def search_name_win(message):
    print(message.text)
    name = message.text
    print(f"SELECT * FROM data_full WHERE data_full.name_reg LIKE '%{name.lower()}%'")
    rows = await sql.sql_select(f"SELECT * FROM data_full WHERE data_full.name_reg LIKE '%{name.lower()}%'")
    text = ""
    for row in rows:
        text += f"{row[1]} {row[0]}\n"
    return text


async def search_kod_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT * FROM data_full WHERE kod = {message.text}")
        text = f"{row[1]} {row[0]}\n"
        return text
    except Exception as n:
        print(n)
        return "Ничего не найдено"


async def search_serial_win(message):
    try:
        row = await sql.sql_selectone(f"SELECT kod, name FROM zabbix WHERE serial = '{message.text}'")
        text = f"{row[1]} {row[0]}\n"
        return text
    except TypeError:
        return "Ничего не найдено"


async def search_ip(host):
    try:
        socket.inet_aton(host)
        loopback = ''.join(host.split(".")[0:2])
        if loopback == '10255':
            row = (await sql.sql_selectone(f"SELECT name FROM zabbix WHERE loopback = '{host}'"))[0]
            return row
        else:
            ip = '.'.join(host.split(".")[0:3])
            rows = await sql.sql_select(f"SELECT vlan100, vlan200, vlan300, vlan400, vlan500, name FROM zabbix WHERE sdwan = 1")
            for row in rows:
                for r in row:
                    ip_search = str(r).split(".")[0:3]
                    ip_search = '.'.join(ip_search)
                    # print(ip_search)
                    if ip == ip_search:
                        return row[5]
            return "Ничего не нашел"
    except socket.error:
        return False
    # try:
    #     # row = await sql.sql_selectone(f"SELECT kod, name FROM zabbix WHERE serial = '{message.text}'")
    #     text = f"{row[1]} {row[0]}\n"
    #     return text
    # except TypeError:
    #     return "Ничего не найдено"