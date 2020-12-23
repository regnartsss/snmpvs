import aiosnmp, asyncio


# kod = callback_data["kod"]
# vlan = callback_data["data"]
# loopback = await sql_selectone(f"SELECT loopback, {vlan} FROM zabbix WHERE kod = {kod}")
# command = "show ip dhcp binding"
# # command = "sh arp vrf 100"
# user = 'operator'
# secret = '71LtkJnrYjn'
async def snmp():

    with aiosnmp.Snmp(host='10.97.18.2', port=161, community="read") as snmp:
        try:
            result = await snmp.bulk_walk(".1.3.6.1.2.1.17.1.4")
            print(result)
            for res in result:
                print(res.oid, res.value)
        except Exception as n:
            print(f"Ошибка_cisco {n}")

loop = asyncio.get_event_loop()
asyncio.ensure_future(snmp())
loop.run_forever()

