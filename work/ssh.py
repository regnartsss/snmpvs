import asyncssh, sys
import os
import asyncio
from work.sql import sql_selectone

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()



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


async def ssh(call):
    try:
        asyncio.get_event_loop().run_until_complete(ssh_traceroute_vrf(call))
    except (OSError, asyncssh.Error) as exc:
        await call.message.answer('SSH connection failed: ' + str(exc))
        sys.exit('SSH connection failed: ' + str(exc))


    # client = paramiko.SSHClient()
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


async def kod_loopback(call):
    kod = call.data.split("_")[1]
    loopback = await sql_selectone(f"SELECT loopback FROM filial Where kod = {kod}")
    return loopback[0]
