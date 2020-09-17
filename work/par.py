from netmiko import ConnectHandler


cisco_router = {'device_type': 'cisco_ios', # предопределенный тип устройства
                'ip': '192.168.1.1', # адрес устройства
                'username': 'user', # имя пользователя
                'password': 'userpass', # пароль пользователя
                'secret': 'enablepass', # пароль режима enable
                'port': 20022, # порт SSH, по умолчанию 22
                 }

ssh = ConnectHandler()
