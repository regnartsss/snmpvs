from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
# server = ldap3.Server('ldap://{}'.format(ip), get_info=ALL)
# conn = ldap.open("partner.ru")
# conn.simple_bind_s("podkopaev.k@partner.ru", "z15X3vdy")
import dns.resolver
import socket
import json
import os
import data

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'
global dat

PATH = find_location()

def open_dat():
    global dat
    with open(PATH + 'dat.json', 'rb') as f:
         dat = json.load(f)

def AD():
    AD_USER = 'podkopaev.k@partner.ru'
    AD_PASSWORD = 'z15X3vdy'
    #AD_SEARCH_TREE = 'OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru'
    AD_SEARCH_TREE ='CN=Computers,DC=partner,DC=ru'
    # server = "partner.ru"
    #AD_SEARCH_TREE =
    #соединяюсь с сервером. всё ОК
    server = Server("partner.ru")
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    conn.search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE,paged_size=1000, attributes=ALL_ATTRIBUTES)
    g = conn.extend.standard.paged_search(AD_SEARCH_TREE, search_filter='(objectCategory=computer)', search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)


#Создать контейнер
#   print(conn.add('OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru', 'organizationalUnit'))


    for entry in g:
        name = entry['attributes']['name']
        name_old = name.split("-")[0]
        name_old_3 = name[0:3]
        # print(name_old_3)
        for i in dat:
            if name_old == i:
                print("Найден ПК %s\n" % name)
                conn.modify_dn('CN=%s,CN=Computers,DC=partner,DC=ru'%name, 'CN=%s'%name,
                               new_superior='OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')
        for x in range(len(data.pref)):
            if name_old_3 == data.pref[x]:
                print("Найден ПК %s\n" % name)
                conn.modify_dn('CN=%s,CN=Computers,DC=partner,DC=ru'%name, 'CN=%s'%name,
                new_superior = 'OU=newscript,OU=_Computers,OU=02. Восточная Сибирь,OU=1. Розничная Сеть (ДНС),OU=DNS Users,DC=partner,DC=ru')


# open_dat()
# AD()