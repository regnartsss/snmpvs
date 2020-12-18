from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES, MODIFY_DELETE, MODIFY_REPLACE, MODIFY_ADD
from work.sql import sql_select_no, sql_selectone_no
import re
from data.config import AD_USER, AD_PASSWORD, AD_SERVER, admin_id
from ldap.ldap_group import send_message_ldap
AD_SEARCH_TREE = 'OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'

server = Server(AD_SERVER)
conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
conn.bind()
filt = "(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(title=*правляющ*))"

def search_user():

    filt = "(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(title=*правляющ*))"
    g = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter=filt, search_scope=SUBTREE,
                                          attributes=ALL_ATTRIBUTES)

    filt = f"(&(objectCategory=group)(CN=*Auto_*))"
    groups = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter=filt, search_scope=SUBTREE,
                                               attributes=ALL_ATTRIBUTES)
    groups = list(groups)
    print(groups)
    for t in g:
        department_user = t['attributes']['department']
        member = t['attributes']['distinguishedName']
        gro = t['attributes']['memberof']
        gr = f'Auto_Администратор компьютера {department_user}'
        l = 1
        le = len(gro)
        for group in groups:
            department = group['attributes']['cn']
            cn = group['attributes']['distinguishedName']
            if gr == department:
                for g in gro:
                    g = g.split(",")[0][3:]
                    if le == l:
                        text = f"Пользователь в группе не состоит {g}\n"
                        print("Пользователь в группе не состоит", cn)
                        for g in gro:
                            result = re.findall(r'Auto_', g)
                            if result:
                                text += f"Удален из группы {g.split(',')[0]}"
                                conn.modify(g, {'member': [(MODIFY_DELETE, member)]})
                            text += f"Добавлен в группу {cn.split(',')[0]}"
                            conn.modify(cn, {'member': [(MODIFY_ADD, member)]})
                            print(text)
                            # await send_message_ldap(text)
                        break
                    elif g == gr:
                        print("Пользователь состоит в группе", gr)
                        break
                    l += 1

search_user()