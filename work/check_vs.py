from pysnmp.hlapi import *
from pprint import pprint
import os
from datetime import datetime
from work import sql
# from loader_telebot import bot
from loader import bot
import asyncio
import time
import paramiko
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

async def start_snmp():
    print("stop")
    # await bot.send_message(chat_id=765333440, text="dddddd")
    i = 0
    while i < 2:
        rows = await sql.sql_select("SELECT loopback, kod FROM filial")
        for row in rows:
            if (await sql.sql_selectone(f"SELECT count(loopback) FROM status WHERE loopback = '{row[0]}'"))[0] == 0:
                await sql.sql_insert(f"INSERT INTO status (loopback, kod) VALUES ('{row[0]}', {row[1]})")
            else:
                await ssh_tunnel(row[0])
        await monitoring()

async def ssh_tunnel(loopback):
        command = "show int"
        user = 'operator'
        secret = '71LtkJnrYjn'
        port = 22
        d = []
        i_1, i_2 = 0, 0
        st_1, st_2 = 1, 1
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=loopback, username=user, password=secret, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        f = stdout.read()
        client.close()
        #        print("test_3")
        open('tunnel.txt', 'wb').write(f)
        time.sleep(1)
        print(f"ssh_tunnel_{loopback}")
        with open('tunnel.txt') as f:
            lines = f.readlines()
            for line in lines:
                if line.split() != []:
                    # print(line.split())
                    if line.split()[0] == "Tunnel0":
                        # print("Туннель")
                        st_1 = 0
                    elif line.split()[0] == "Tunnel1":
                        # print("Туннель2")
                        st_2 = 0
                    elif i_1 == 29:
                        st_1 = 1
                    elif st_1 == 0:
                        if i_1 == 23:
                            d.append(line.split()[3])
                            # print(line.split())
                        elif i_1 == 27:
                            d.append(line.split()[3])
                            # print(line.split())
                            # i_1 = 0
                            st_1 = 1
                        i_1 += 1
                    elif i_2 == 29:
                         st_2 = 1
                    elif st_2 == 0:
                        # print(line.split())
                        if i_2 == 23:
                            d.append(line.split()[3])
                             # print(line.split())
                        elif i_2 == 27:
                            d.append(line.split()[3])
                             # print(line.split())
                    #         i_2 = 0
                            st_2 = 1
                        i_2 += 1

        request = f"UPDATE status SET In1_one = In1_two, Out1_one = Out1_two, In2_one = In2_two, Out2_one = Out2_two, " \
                              f"In1_two = {d[0]}, Out1_two = {d[1]},In2_two = {d[2]}, Out2_two = {d[3]} WHERE loopback = '{loopback}'"
        await sql.sql_insert(request)

                    #     return line.split()[3]

async def check(loopback):
    await asyncio.sleep(1)
    # print(loopback)
    request = f"""SELECT In1_two, In2_two, Out1_two, Out2_two, In1_one,  In2_one, Out1_one, Out2_one
                FROM status WHERE loopback = '{loopback}'"""
    # print(loopback)
    st = await sql.sql_selectone(request)
    Intunnel1 = st[0] - st[4]
    Intunnel2 = st[1] - st[5]
    Outtunnel1 = st[2] - st[6]
    Outtunnel2 = st[3] - st[7]
    # print(Intunnel1)
    # print(Outtunnel1)
    # print(Intunnel2)
    # print(Outtunnel2)
    status1, status2 = 3, 3
    if Intunnel1 > 0 or Outtunnel1 > 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status1 = 1 WHERE loopback = '{loopback}'")
        status1 = 1
    elif Intunnel1 == 0 or Outtunnel1 == 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status1 = 0 WHERE loopback = '{loopback}'")
        status1 = 0
    else:
        print("Ошибка 1")
    if Intunnel2 > 0 or Outtunnel2 > 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status2 = 1 WHERE loopback = '{loopback}'")
        status2 = 1
    elif Intunnel2 == 0 or Outtunnel2 == 0:
        # sql.sql_insert_no_await(f"UPDATE status SET status2 = 0 WHERE loopback = '{loopback}'")
        status2 = 0
    else:
        print("Ошибка 2")
    # print("%s" % status1)
    # print("%s" % status2)
    status_t1, status_t2, kod = await sql.sql_selectone(
        f"SELECT status_1, status_2, kod FROM status WHERE loopback = '{loopback}'")
    # print(status_t1)
    # print(status_t2)
    # t = "%s\n%s\n" % (dat[kod]["name"], dat[kod]["sysName"])
    # text = "Филиал %s\n" % kod
    # try:
    #     stat[kod]["status_t1"]
    #     stat[kod]["status_t2"]
    # except:
    #     stat[kod]["status_t1"] = 3
    #     stat[kod]["status_t2"] = 3
    if status1 == 0 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            # print("ok")
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔴 Филиал не доступен \nLoopback: {data[2]}\n{data[5]}\n" \
                   f"ISP_1: {data[3]}\n" \
                   f"{data[6]}\nISP_2: {data[4]}"
            print("Филиал не доступен")
            # stat[kod]["status_t1"] = 0
            # stat[kod]["status_t2"] = 0
            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 0 WHERE loopback = '{loopback}'")
            print(text)
            await send_mess(kod, text)
    elif status1 == 1 and status2 == 0:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔴 Резервный провайдер не работает \n" \
                   f"Loopback: {data[2]}\n{data[6]}\nISP_2: {data[4]}"
            # text += "🔵 🔴 Резервный провайдер не работает\n%s\nISP_2: %s"%(dat[kod]["ISP2_NAME"],dat[kod]["ISP2"])
            print("Резервный не работает")
            # stat[kod]["status_t1"] = 1
            # stat[kod]["status_t2"] = 0
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 0 WHERE loopback = '{loopback}'")
            print(text)

            await send_mess(kod, text)

    elif status1 == 0 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            data = await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name "
                f"FROM filial WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔴 🔵 Основной провайдер не работает\n\n" \
                   f"Loopback: {data[2]}\n{data[5]}\nISP_1: {data[3]}\n"
            # text += "🔴 🔵 Основной провайдер не работает\n%s\nISP_1: %s"%(dat[kod]["ISP1_NAME"],dat[kod]["ISP1"])
            print("Основной не работает")
            # stat[kod]["status_t1"] = 0
            # stat[kod]["status_t2"] = 1
            await sql.sql_insert(f"UPDATE status SET status_1 = 0, status_2 = 1 WHERE loopback = '{loopback}'")
            print(text)


            await send_mess(kod, text)

    elif status1 == 1 and status2 == 1:
        if status_t1 == status1 and status_t2 == status2:
            pass
        else:
            # text += "🔵 🔵 Филиал работает"
            print("Филиал работает")
            data =await sql.sql_selectone(
                f"SELECT name, kod, loopback, ISP1, ISP2, isp1_name, isp2_name FROM filial "
                f"WHERE loopback = '{loopback}'")
            text = f"{data[0]}\nКод: {data[1]}\n🔵 🔵 Филиал работает"
            # stat[kod]["status_t1"] = 1
            # stat[kod]["status_t2"] = 1
            await sql.sql_insert(f"UPDATE status SET status_1 = 1, status_2 = 1 WHERE loopback = '{loopback}'")
            print(text)


            await send_mess(kod, text)
    else:
        pprint("тест")


async def send_mess(kod, text):
    try:
        rows = await sql.sql_selectone(f"SELECT user_id FROM sub WHERE kod = {kod}")
        # print(rows)
        for row in rows:
            # print(row)
                 await bot.send_message(chat_id=row, text=text)
    except TypeError:
        print("Ошибка отправки")


def data_monitor():
    return datetime.today().strftime("%H:%M:%S %d/%m/%Y")


async def monitoring():
    keyboard = InlineKeyboardMarkup()
    i = 1
    # tab = []
    # null = InlineKeyboardButton(text="   ", callback_data="sub")
    # #    tab.append(telebot.types.InlineKeyboardButton(text="мониторинг", callback_data="sub"))
    # #    keyboard.row(null,null,null,null,null,null,null)
    tab = []
    text = ""
    colum = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60]
    # colum_old = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51]
    request = f"SELECT filial.kod, status_1, status_2, ISP1, ISP2 FROM status INNER JOIN filial ON status.kod = filial.kod ORDER BY flilial.kod"
    # print(request)
    rows = await sql.sql_select(request)
    for row in rows:
        ch1 = "🔵"
        ch2 = "🔵"
        if row[1] == 1:
            ch1 = "🔵"
        elif row[1] == 0:
            ch1 = "🔴"
        if row[2] == 1:
            ch2 = "🔵"
        elif row[2] == 0:
            ch2 = "🔴"
        if row[3] == "unassigned":
            ch1 = "⚪"
        if row[4] == "unassigned":
            ch2 = "⚪"
        tab.append(InlineKeyboardButton(text=f"{ch1}{ch2}{row[0]} ", callback_data=f"sub_{row[0]}"))
        if i in colum:
            keyboard.row(*tab)
            tab = []
        i += 1
    keyboard.row(*tab)
    await bot.edit_message_text(chat_id="@sdwan_monitoring", message_id=21,
                          text="<---------------->\n Время проверки %s" % data_monitor(), reply_markup=keyboard)


async def call_name(call):
    kod = call.data.split("_")[1]
    name = (await sql.sql_selectone(f"SELECT name FROM filial WHERE kod = {kod}"))[0]
    try:
        await bot.answer_callback_query(callback_query_id=call.id, text=f"{name}")
    except Exception as n:
        print(n)

asyncio.run(start_snmp())