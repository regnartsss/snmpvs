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


def ad():
    print("ad")
    server = Server(AD_SERVER)
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    result = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)',
                                               search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)
    # rows = await sql_select(f"SELECT kod FROM zabbix")
    for entry in result:
        print(entry)
        dn = entry['attributes']['distinguishedName']
        dnshostname = entry['attributes']['dNSHostName']
        name = str(entry['attributes']['name'])
        result = re.findall(r'^vs\d', name.lower())
        if result:



ad()

