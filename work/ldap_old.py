from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
# server = ldap3.Server('ldap://{}'.format(ip), get_info=ALL)
# conn = ldap.open("partner.ru")
# conn.simple_bind_s("podkopaev.k@partner.ru", "z15X3vdy")
import json
import os
from data import data
from work.sql import sql_select_no, sql_selectone_no, sql_selectone, sql_select
# import ipaddr, ipaddress
import socket
from loader import bot
from work.search import search_ip
from work.zabbix_check_cisco import notif

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'

PATH = find_location()

dat = ['kra', 'abk', 'uln', 'irk', 'ykt', 'cht']
import socket
import dns.resolver
import re

AD_SEARCH_AUTOGROUP = 'OU=autogroup,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
AD_SEARCH_COMPUTERS = 'OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'


async def AD():
    AD_USER = 'podkopaev.k@partner.ru'
    AD_PASSWORD = 'z15X3vdy'
    # AD_SEARCH_TREE = 'OU=autogroup,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
    AD_SEARCH_TREE = 'CN=Computers,DC=partner,DC=ru'
    # server = "partner.ru"
    # AD_SEARCH_TREE =
    # соединяюсь с сервером. всё ОК
    server = Server("dv-dc2.partner.ru")
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    result = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)

    # conn.search(AD_SEARCH_AUTOGROUP, search_filter='(objectCategory=computer)', search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)
    rows = await sql_select(f"SELECT kod FROM zabbix")
    for entry in result:
        dn = entry['attributes']['distinguishedName']
        name = str(entry['attributes']['name'])
        # if 'vs' in name[:2].lower():
        result = re.findall(r'^vs\d', name.lower())
        if result:
            print(name)
            await move_group(name, conn, dn)
        for d in dat:
            if d in name.lower()[0:3]:
                result = re.findall(r'\w{3}\d', name)
                if result:
                    await move_group(name, conn, dn)




async def move_group(name, conn, dn):
    try:
        answer = dns.resolver.query(name, raise_on_no_answer=False)
        an = str(answer.rrset).split()[4]
        filial = await search_ip(an)
        if filial != "Ничего не нашел по ip":
            superior, text = await find_group(filial)
            text = f"{name} перенесен в группу {text}"
            await bot.send_message(chat_id=765333440, text=text, reply_markup=await notif())
            conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
            if conn.result['result'] == 80:
                print("Создать филиал")
                conn.add(superior, 'organizationalUnit')
                if conn.result['description'] == 'noSuchObject':
                    print("Создать регион")
                    region = ','.join(superior.split(",")[1:])
                    conn.add(region, 'organizationalUnit')
                    conn.add(superior, 'organizationalUnit')
                    cn_group, attrs = create_group(filial, superior)
                    conn.add(dn=cn_group, attributes=attrs)
                    conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
                cn_group, attrs = create_group(filial, superior)
                conn.add(dn=cn_group, attributes=attrs)
                print(conn.result)
                conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
            else:
                print("Филиал есть")

    except dns.resolver.NXDOMAIN:
        text = f"{name} не найден филиал, переместите руками"
        await bot.send_message(chat_id=765333440, text=text, reply_markup=await notif())


async def find_group(filial):
    request = f"SELECT zabbix.kod, zb_region.name FROM zabbix LEFT JOIN zb_region ON zabbix.region = zb_region.id WHERE zabbix.name = '{filial}'"
    rows = await sql_selectone(request)
    region = str(rows[1])
    region = region.replace('"', '')
    superior = f'OU={rows[0]} {filial},OU={region},OU=Филиалы,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
    text = f"{region}/{rows[0]} {filial}"
    return superior, text


def create_group(department, superion):
    dn = f'CN=Auto_Администратор компьютера {department},{superion}'
    attrs = {}
    attrs['objectclass'] = ['top', 'Group']
    attrs['cn'] = f'Auto_Администратор компьютера {department}'
    attrs['groupType'] = '-2147483644'
    attrs['sAMAccountName'] = f'Auto_Администратор компьютера {department}'
    return dn, attrs


# async def search_ip(host):
#     try:
#         socket.inet_aton(host)
#         loopback = ''.join(host.split(".")[0:2])
#         ip = '.'.join(host.split(".")[0:3])
#         rows = sql_select_no(
#             f"SELECT vlan100, vlan200, vlan300, vlan400, vlan500, name FROM zabbix WHERE sdwan = 1")
#         for row in rows:
#             for r in row:
#                 ip_search = str(r).split(".")[0:3]
#                 ip_search = '.'.join(ip_search)
#                 # print(ip_search)
#                 if ip == ip_search:
#                     return row[5]
#     except socket.error:
#         return False

        # try:
        #     answer = dns.resolver.query(name, raise_on_no_answer=False)
        #     an = str(answer.rrset).split()[4]
        #     print(an)
        # except dns.resolver.NXDOMAIN:
        #     print("не удалось обнаружить узел")
    #
    # name_old = name.split("-")[0]
    # name_old_3 = name[0:3]
    # print(name_old_3)
    # for i in dat:
    #     if name_old == i:
    #         print("Найден ПК %s\n" % name)
    #         conn.modify_dn('CN=%s,CN=Computers,DC=partner,DC=ru'%name, 'CN=%s'%name, new_superior='OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')
    # for x in range(len(data.pref)):
    #     if name_old_3 == data.pref[x]:
    #         print("Найден ПК %s\n" % name)
    #         conn.modify_dn(f'CN={name},CN=Computers,DC=partner,DC=ru', f'CN={name}', new_superior = f'OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')
    #


# open_dat()
