from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
from data.config import AD_USER, AD_PASSWORD, AD_SEARCH_TREE, AD_SERVER, admin_id
from work.sql import sql_selectone, sql_select
import logging
from aiogram.utils.exceptions import NetworkError, BotBlocked, ChatNotFound
from loader import bot
from work.search import search_ip
from work.zabbix_check_cisco import notif
import dns.resolver
import re
from data.config import channel_mess

dat = ['kra', 'abk', 'uln', 'irk', 'ykt', 'cht']


async def ad():
    print("ad")
    server = Server(AD_SERVER)
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    result = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)
    # rows = await sql_select(f"SELECT kod FROM zabbix")
    for entry in result:
        dn = entry['attributes']['distinguishedName']
        try:
            name = str(entry['attributes']['dNSHostName'])
        except KeyError:
            name = str(entry['attributes']['name'])
        result = re.findall(r'^vs\d', name.lower())
        if result:
            await move_group(name, conn, dn)
        for d in dat:
            if d in name.lower()[0:3]:
                result = re.findall(r'\w{3}\d', name)
                if result:
                    await move_group(name, conn, dn)


async def move_group(name, conn, dn):
    try:
        answer = dns.resolver.query(name, raise_on_no_answer=False)
        print(answer.rrset)
        an = str(answer.rrset).split()[4]
        filial = await search_ip(an)
        if filial != "Ничего не нашел по ip":
            superior, text = await find_group(filial)
            text = f"{name} перенесен в группу {text}"
            await send_message_ldap(text)
            conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
            if conn.result['result'] == 80:
                conn.add(superior, 'organizationalUnit')
                if conn.result['description'] == 'noSuchObject':
                    region = ','.join(superior.split(",")[1:])
                    conn.add(region, 'organizationalUnit')
                    conn.add(superior, 'organizationalUnit')
                    cn_group, attrs = create_group(filial, superior)
                    conn.add(dn=cn_group, attributes=attrs)
                    conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
                cn_group, attrs = create_group(filial, superior)
                conn.add(dn=cn_group, attributes=attrs)
                conn.modify_dn(str(dn), relative_dn=f'CN={name}', new_superior=superior)
    except dns.resolver.NXDOMAIN:
        text = f"{name} не найден филиал, переместите руками"
        await send_message_ldap(text)


async def find_group(filial):
    request = f"SELECT zabbix.kod, zb_region.name FROM zabbix LEFT JOIN zb_region ON zabbix.region = zb_region.id WHERE zabbix.name = '{filial}'"
    rows = await sql_selectone(request)
    region = str(rows[1])
    region = region.replace('"', '')
    superior = f'OU={rows[0]} {filial},OU={region},OU=Филиалы,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
    text = f"{region}/{rows[0]} {filial}"
    return superior, text


def create_group(department, superion):
    dn = f'CN=_Администратор компьютера {department},{superion}'
    attrs = {}
    attrs['objectclass'] = ['top', 'Group']
    attrs['cn'] = f'_Администратор компьютера {department}'
    attrs['groupType'] = '-2147483644'
    attrs['sAMAccountName'] = f'_Администратор компьютера {department}'
    return dn, attrs


async def send_message_ldap(text):
    if channel_mess == 0:
        await bot.send_message(chat_id='@sdwan_log', text=text, disable_notification=True)
    # print(text)
    # for admin in admin_id:
    #     try:
    #         await bot.send_message(chat_id=admin, text=text, disable_notification=await notif())
    #     except NetworkError:
    #         logging.info(f"Ошибка подключения к серверу телеграм")
    #     except TypeError:
    #         logging.info(f"Ошибка отправки {admin}")
    #     except ChatNotFound:
    #         logging.info(f"Юзер не найден {admin}")
    #     except BotBlocked:
    #         logging.info(f"Юзер заблокировал {admin}")
