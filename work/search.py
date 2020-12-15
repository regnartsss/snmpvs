from aiogram.dispatcher.filters.state import State, StatesGroup
from work import sql
import re, ipaddress
import socket


class SearchFilial(StatesGroup):
    Filial = State()
    Kod = State()
    Serial = State()
    Ip = State()
    Search = State()


async def check_search(text):
    try:
        ipaddress.ip_address(text)
        return await search_ip(text)
    except ValueError:
        result = re.findall(r'\d', text)
        if result and len(text) <= 4:
            return await search_kod_win(text)
        elif len(text) == 11 and text[:3] == "FGL":
            return await search_serial_win(text)
        else:
            name = await search_name_win(text)
            if name:
                return name
            else:
                return "Ничего не найдено"


async def search_name_win(name):
    # name = message.text
    rows = await sql.sql_select(f"SELECT * FROM data_full WHERE data_full.name_reg LIKE '%{name.lower()}%'")
    text = ""
    for row in rows:
        text += f"{row[1]} {row[0]}\n"
    return text


async def search_kod_win(kod):
    rows = await sql.sql_selectone(f"SELECT * FROM data_full WHERE kod = {kod}")
    if rows is None:
        row = await sql.sql_selectone(f"SELECT kod, name, loopback FROM zabbix WHERE kod = {kod}")
        if row is not None:
            text = f"{row[1]} {row[0]} {row[2]}\n"
            return text
        else:
            return "Ничего не найдено"
    else:
        text = f"{rows[1]} {rows[0]}\n"
        return text


async def search_serial_win(serial):
    try:
        row = await sql.sql_selectone(f"SELECT kod, name FROM zabbix WHERE serial = '{serial}'")
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
            rows = await sql.sql_select(f"SELECT loopback, vlan100, vlan200, vlan300, vlan400, vlan500, name FROM zabbix")
            for row in rows:
                for r in row:
                    ip_search = str(r).split(".")[0:3]
                    ip_search = '.'.join(ip_search)
                    if ip == ip_search:
                        return row[6]
            return "Ничего не нашел по ip"
    except socket.error:
        return False





    # try:
    #     # row = await sql.sql_selectone(f"SELECT kod, name FROM zabbix WHERE serial = '{message.text}'")
    #     text = f"{row[1]} {row[0]}\n"
    #     return text
    # except TypeError:
    #     return "Ничего не найдено"