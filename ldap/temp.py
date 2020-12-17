from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES, MODIFY_DELETE, MODIFY_REPLACE, MODIFY_ADD
from work.sql import sql_select_no, sql_selectone_no
import re
AD_USER = 'podkopaev.k@partner.ru'
AD_PASSWORD = 'z15X3vdy'
AD_SEARCH_TREE = 'OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
# AD_SEARCH_TREE = 'CN=Computers,DC=partner,DC=ru'
# server = "partner.ru"
# AD_SEARCH_TREE =
# соединяюсь с сервером. всё ОК
server = Server("dv-dc2.partner.ru")
conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
conn.bind()
print('Connection Bind Complete!')
# conn.search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE, paged_size=1000,
#             attributes=ALL_ATTRIBUTES)
filt = "(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(title=*правляющ*))"


# filt = "(&(objectCategory=group)(groupType:1.2.840.113556.1.4.803:=4))"


def search_user():
    filt = "(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(title=*правляющ*))"
    # filt = '(&(objectClass=user)(sAMAccountName=podkopaev.k))'
    g = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter=filt, search_scope=SUBTREE,
                                          attributes=ALL_ATTRIBUTES)

    filt = f"(&(objectCategory=group)(CN=*Auto_*))"
    groups = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter=filt, search_scope=SUBTREE,
                                               attributes=ALL_ATTRIBUTES)

from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES, MODIFY_DELETE, MODIFY_REPLACE, MODIFY_ADD
from work.sql import sql_select_no, sql_selectone_no
import re

AD_USER = 'podkopaev.k@partner.ru'
AD_PASSWORD = 'z15X3vdy'
AD_SEARCH_TREE = 'OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
# AD_SEARCH_TREE = 'CN=Computers,DC=partner,DC=ru'
# server = "partner.ru"
# AD_SEARCH_TREE =
# соединяюсь с сервером. всё ОК
server = Server("dv-dc2.partner.ru")
conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
conn.bind()

# filt = "(&(objectCategory=group)(groupType:1.2.840.113556.1.4.803:=4))"
# g = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter=filt, search_scope=SUBTREE,
#                                       attributes=ALL_ATTRIBUTES)
#
# for d in g:
#     print(d['attributes'])
# dn = 'CN=KRA113-UPRAV,OU=KRA113 Кра на Октябрьской ФТ,OU=autogroup,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
# name = 'KRA113-UPRAV'
# superior = 'OU=871 Кра на Октябрьской Гипер,OU=РРС ВС Запад,OU=Филиалы,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
# conn.modify_dn('CN=KRA113-UPRAV,OU=KRA113 Кра на Октябрьской ФТ,OU=autogroup,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru',
#                relative_dn='CN=KRA113-UPRAV',
#                new_superior='OU=871 Кра на Октябрьской Гипер,OU=РРС ВС Запад,OU=Филиалы,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')
member = 'CN=Aleksandr Kazakov,OU=Магазин Кра на Октябрьской Гипер,OU=Красноярск,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
cn = 'CN=Auto,OU=871 Кра на Октябрьской Гипер,OU=РРС ВС Запад,OU=Филиалы,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
conn.modify(cn,
            {'member': [(MODIFY_ADD, [member])]}
            )
print(conn.result)
# # conn.modify_dn(f'CN={name},CN=Computers,DC=partner,DC=ru', f'CN={name}', new_superior=superior)


