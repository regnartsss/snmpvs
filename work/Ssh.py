import asyncssh, sys
import os
from work.sql import sql_selectone, sql_select, sql_insert
from aiogram.dispatcher.filters.state import State, StatesGroup
from work.keyboard import main_menu
from loader import bot
import asyncio
import socket
import os
# import wmi
# import wmi_client_wrapper as wmi

#
# def find_location():
#     return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'
#
# PATH = find_location()


class Ssh_console(StatesGroup):
    command = State()


async def ssh_traceroute_vrf(call):
    loopback = await kod_loopback(call)
    command = "traceroute vrf 100 10.10.33.5"
    user = 'operator'
    secret = '71LtkJnrYjn'
    f = f"""traceroute vrf 100 10.10.33.5
loopback: {loopback}"""
    async with asyncssh.connect(loopback, username=user, password=secret, known_hosts=None) as conn:
        result = await conn.run(command, check=True)
        f += result.stdout
        await call.message.answer(f)


async def ssh_t(call):
    try:
        await ssh_traceroute_vrf(call)
    except (OSError, asyncssh.Error) as exc:
        await call.message.answer('SSH connection failed: ' + str(exc))
        sys.exit('SSH connection failed: ' + str(exc))


async def kod_loopback(call):
    kod = call.data.split("_")[2]
    print(kod)
    loopback = await sql_selectone(f"SELECT loopback FROM filial Where kod = {kod}")
    return loopback[0]


async def ssh_console(call):
    kod = call.data.split("_")[1]
    user_id = call.message.chat.id
    await Ssh_console.command.set()
    await sql_insert(f"UPDATE users SET ssh_kod = {kod} WHERE id = {user_id}")
    text = "Введите команду SSH для отправки на циску или 444 для отмены\n" \
           "vlan 100 - ping vrf 100 'ip addreess'\nvlan 200 - ping vrf 200 'ip addreess'\n" \
           "vlan 400 - ping vrf 100 'ip addreess'\nvlan 500 - ping vrf 6 'ip addreess'\n" \
           "isp gateway - ping 'ip address'\nsh ip int br"
    return text


async def ssh_console_command(message, state):
    if message.text == "🚫 Отмена":
        await message.answer("🚫 Отмена", reply_markup=main_menu())
        await state.finish()
    else:
        return await console_command(message)


async def console_command(message):
    loopback = (await sql_selectone(f"SELECT loopback FROM users LEFT JOIN filial "
                                    f"ON users.ssh_kod = filial.kod WHERE users.id = {message.chat.id}"))[0]
    command = message.text
    user = 'operator'
    secret = '71LtkJnrYjn'
    async with asyncssh.connect(loopback, username=user, password=secret, known_hosts=None) as conn:
        result = await conn.run(command, check=True)
        text = result.stdout
        while len(text) > 4000:
            await bot.send_message(chat_id=message.chat.id, text = text[:4000])
            text = text[4000:]
        return text


# async def ip_dhcp_binding():
#     loopback = "10.255.64.1"
#     command = "show ip dhcp binding"
#     user = 'operator'
#     secret = '71LtkJnrYjn'
#     async with asyncssh.connect(loopback, username=user, password=secret, known_hosts=None) as conn:
#         result = await conn.run(command, check=True)
#         text = result.stdout.split("\n")
#         for line in text:
#             if line.split() != []:
#                 if line.split()[0].split(".")[0] == '10':
#                     try:
#                         ip = line.split()[0]
#                         mac = line.split()[1]
#                         hostname = (socket.gethostbyaddr(ip))[0]
#                         try:
#
#                             # wmic = wmi.WmiClientWrapper(host=ip,)
#                             # output = wmic.query("SELECT * FROM Win32_Processor")
#                             # print(output)
#                             c = wmi.WMI(ip)
#                             for osi in c.query("SELECT * FROM Win32_ComputerSystem"):
#                             # for osi in c.Win32_OperatingSystem():
#                                 print(osi)
#                                 os = os.Caption
#                         except:
#                             os="null"
#                             pass
#                         # await sql_insert(f"INSERT INTO mac_hostname (ip, mac, hostname, os) VALUES ('{ip}','{mac}','{hostname}', '{os}')")
#                     except socket.error:
#                         pass
#
#
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(ip_dhcp_binding())

#         command = "sh port add"
#         user = 'itkras'
#         secret = 'miccis-96kraS'
#         port = 22
#         print("ssh_err_mac_1")
#         async with asyncssh.connect(row[0], username=user, password=secret, known_hosts=None) as conn:
#             result = await conn.run(command, check=True)
#             text = result.stdout.split("\n")
#             for line in text:

# #         client.close()


async def snmp_cisco_mac():
    rows = await sql_select(f"SELECT ip FROM cisco WHERE kod = 1769")
    for row in rows:
        command = "sh port add"
        user = 'itkras'
        secret = 'miccis-96kraS'
        port = 22
        print("ssh_err_mac_1")
        async with asyncssh.connect(row[0], username=user, password=secret, known_hosts=None) as conn:
            result = await conn.run(command, check=True)
            text = result.stdout.split("\n")
            for line in text:
                if line.split() != []:
                    print(line.split())
#         client.close()
#         open(PATH + 'l.txt', 'wb').write(t)
#         text = ""
#         with open(PATH + 'l.txt') as f:
#             lines = f.readlines()
#             for line in lines:
#                 print(line)
#                     # if line.split()[0] == "100" or line.split()[0] == "200" or line.split()[0] == "300" or \
#                     #         line.split()[
#                     #             0] == "400":
#                     #     mac_old = "%s%s%s" % (
#                     #         line.split()[1].split(".")[0], line.split()[1].split(".")[1],
#                     #         line.split()[1].split(".")[2])
#                     #     #                    print(mac)
#                     #     #                    print(mac_old)
#                     #     if mac == mac_old:
#                     #         #                        print(line.split()[3])
#                     #         text = "Mac на порту %s" % line.split()[3]
#                     #         #                        bot.send_message(message.chat.id, text)
#                     #         return
# loop = asyncio.get_event_loop()
# loop.run_until_complete(snmp_cisco_mac())
#
#     # client = paramiko.SSHClient()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.connect(hostname=loopback, username=user, password=secret, port=port)
    # stdin, stdout, stderr = client.exec_command(command)
    # f = stdout.read()
    # client.close()
    # open(PATH + 'temp/leas.txt', 'wb').write(f)
    # await asyncio.sleep(1)
    # print("test_3")
    # with open(PATH + 'temp/leas.txt') as f:
    #     lines = f.readlines()
    #     text = ""
    #     for line in lines:
    #         if line.split() != []:
    #             text += line
    # await call.message.answer(text)


# async def ssh_lease():
#     loopback = "10.255.64.32"
#     command = " "
#     user = 'operator'
#     secret = '71LtkJnrYjn'
#     port = 22
#     print("ssh_lease_command_1")
#     async with asyncssh.connect(loopback, username=user, password=secret, known_hosts=None) as conn:
#         result = await conn.run(command, check=True)
#         # print(result)
#         text = result.stdout.split("\n")
#         for line in text:
#             if line.split() != []:
#                 print(line.split())
#                 if line.split()[0].split(".")[0] == 10:
#                     print(line.split())

    # client = paramiko.SSHClient()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.connect(hostname=loopback, username=user, password=secret, port=port)
    # stdin, stdout, stderr = client.exec_command(command)
    # print("ssh_lease_command_read")
    # t = stdout.read()
    # client.close()
    # open(PATH + 't.txt', 'wb').write(t)
    # print("ssh_lease_end")
    # text = ""
    # with open(PATH + 't.txt') as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         if line.split() == []:
    #             pass
    #         else:
    #             print(line)
    #             # if line.split()[0].split(".")[0:3] == dat[kod][lea].split(".")[0:3]:
    #             #     text += leas_print(line.split())
    #             # else:
    #             #     pass
    #         pass

