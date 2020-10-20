from pyzabbix import ZabbixAPI
from work.sql import sql_select_no_await, sql_insert_no_await
from pprint import pprint
from sqlite3 import OperationalError


# def table():
#     rows = sql_select_no_await("SELECT loopback, kod FROM filial")
#     for row in rows:
#         print(f"UPDATE kod = {row[1]} WHERE loopback = '{row[0]}'")
#         sql_insert_no_await(f"UPDATE zabbix SET kod = {row[1]} WHERE loopback = '{row[0]}'")
#
# table()
#
#
# async def check_zabbix():
#     z = ZabbixAPI('https://zabbix.partner.ru/')
#     z.session.auth = ("podkopaev.k", "z15X3vdy")
#     z.session.verify = False
#     z.timeout = 5.1
#     z.login(user="podkopaev.k", password="z15X3vdy")
#     print("Connected to Zabbix API Version %s" % z.api_version())
#     try:
#         rows = sql_select_no_await("SELECT name, loopback FROM zabbix")
#     except OperationalError:
#         sql_insert_no_await("""CREATE TABLE zabbix (
#                                                       name     TEXT,
#                                                       kod      INT,
#                                                       loopback TEXT,
#                                                       sdwan    INT
#                                                   );"""
#                             )
#         rows = sql_select_no_await("SELECT name, loopback FROM zabbix")
#     hrows, frows = [], []
#     all_r, all_f = {}, {}
#     for row in rows:
#         frows.append(row[0])
#         all_f[row[0]] = row[1]
#
#     for h in z.host.get():
#         hrows.append(h['name'])
#         all_r[h['name']] = [h['host'], h['hostid']]
#     delete = ['dv-gw-cisco', 'ural-dc1', 'ural-gw-cisco', 'mow-gw-cisco', 'dv-dc1', 'adm-dipex-gw-cisco', 'dv-dc2']
#     result = list(set(hrows) - set(frows) - set(delete))
#     for h in result:
#         print(f"Добавлен в базу {h} - {all_r[h]}")
#         if '.'.join(all_r[h][0].split(".")[0:2]) == "10.255":
#             sdwan = 1
#         else:
#             sdwan = 0
#         sql_insert_no_await(f"INSERT INTO zabbix (loopback, name, sdwan, hostid) VALUES ('{all_r[h][0]}', '{h}', {sdwan},{all_r[h][1]})")
#     for key, value in all_r.items():
#         for key_old, value_old in all_f.items():
#             if key == key_old:
#                 if value[0] != value_old:
#                     print(f"Филиал {key}. Замена микротика {value_old} на циску {value[0]}")
#                     sql_insert_no_await(f"DELETE FROM zabbix WHERE loopback = '{value_old}'")
#                     sql_insert_no_await(f"INSERT INTO zabbix (loopback, name, sdwan, hostid) "
#                                         f"VALUES ('{value}', '{key}', 1, {value[1]})")


# check_zabbix()


def check_region():
     z = ZabbixAPI('https://zabbix.partner.ru/')
     z.session.auth = ("podkopaev.k", "z15X3vdy")
     z.session.verify = False
     z.timeout = 5.1
     z.login(user="podkopaev.k", password="z15X3vdy")
     print("Connected to Zabbix API Version %s" % z.api_version())
     try:
          sql_insert_no_await("DELETE FROM zb_region")
     except OperationalError:
          new_zb_region()
     for h in z.hostgroup.get():
          id = h['groupid']
          name = h['name'].split("/")[-1]
          print(id, name)
          region = ["див", "Вос", "Адм."]
          if h['name'].split("/")[-1][0] != "-":
               if name[0:3] is region:
                    sql_insert_no_await(f"INSERT INTO zb_region (id, name) VALUES (111, '{name}')")
               else:
                    sql_insert_no_await(f"INSERT INTO zb_region (id, name) VALUES ({id}, '{name}')")
               for x in z.host.get(groupids=id):
                    if x['host'][0:2] == '10':
                         if name[0:3] is region:
                              sql_insert_no_await(f"UPDATE zabbix SET region = 111 WHERE loopback = '{x['host']}'")
                         else:
                              sql_insert_no_await(f"UPDATE zabbix SET region = {id} WHERE loopback = '{x['host']}'")



def new_zb_region():
        sql_insert_no_await("""CREATE TABLE zb_region (id      INT, name TEXT);""")


check_region()
# result = list(set(frows) - set(hrows))
# for h in result:
#     print(f"Нет в забиксе {h} - {all_f[h]}")


# for h in z.host.get():
#      print(h['host'], h['name'])
#      sql_insert_no_await(f"INSERT INTO zabbix (loopback, name) VALUES ('{h['host']}', '{h['name']}')")


# result = list(set(frows) - set(hrows) - set(delete))
# for h in result:
#      print(h)
# for h in z.screenitem.get(hostids=14043):
#      print(h)
