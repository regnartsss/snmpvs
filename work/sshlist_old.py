import paramiko
import os
import time

def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'

PATH = find_location()

def ssh_serial(loopback):
    print("start2")
    command = "show ver"
    user = 'operator'
    secret = '71LtkJnrYjn'
    port = 22
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=loopback, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    f = stdout.read()
    client.close()
    #        print("test_3")
    open(PATH + 'serial.txt', 'wb').write(f)
    time.sleep(1)
    print("test_3")
    with open(PATH + 'serial.txt') as f:
        lines = f.readlines()
        for line in lines:
            if line.split() != []:
                if line.split()[0] == "Processor":
                    return line.split()[3]
