# dns it VostSib, v4.5
# uptime, ip, cam
"""
<parameters>
	<parameter>
	  <type>integer</type>
	  <id>PORT</id>
	  <name>Порт для подключения (UDP)</name>
	  <value>161</value>
	  <min>1</min>
	  <max>65000</max>
	</parameter>
	<parameter>
		<type>string</type>
		<id>IP_LIST</id>
		<name>Список адресов которым разрешен доступ</name>
		<value>10.0.0.0/8</value>
	</parameter>
</parameters>
"""

import re
from pysnmp.hlapi import *
from pysnmp.proto import api
from subprocess import call
from time import time

REGEXP = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$"
CONFIG = "/etc/snmp/snmpd.conf"

pMod = api.protoModules[api.protoVersion2c]
health = settings("health")


def db_ok():
    return "ERROR" if not health["db_connected"] else "OK" if health["db_connected"] == 1 else ""


def archive_days():
    days = str(int(health["disks_stat_main_days"]))

    priv = health["disks_stat_priv_days"]
    subs = health["disks_stat_subs_days"]

    days += (" / %i" % int(priv)) if priv else ""
    days += (" / %i" % int(subs)) if subs else ""
    return days


def disks_ok():
    if health["disks_error_count"] == -1 or health["disks_is_slow"] == -1:
        return ""
    elif health["disks_error_count"] > 0 or health["disks_is_slow"]:
        return "ERROR"
    else:
        return "OK"


def network_ok():
    if health["ifconfig_error"]:
        return "ERROR"

    elif health["network_really_connected"] == -1:
        return ""

    elif health["network_really_connected"] == health["network_should_be_connected"]:
        return "OK"

    else:
        return "%i / %i" % (health["network_really_connected"], health["network_should_be_connected"])


def cameras():
    cameras_online = health["channels_board_online"] + health["channels_network_online"]
    cameras_enabled = health["channels_board_total"] + health["channels_network_total"]
    return "%i / %i" % (cameras_online, cameras_enabled)


def scripts_ok():
    return "OK" if health["scripts_total"] == health["scripts_ok"] else "ERROR"


def cam_down():
    st = objects_list("IP Device")
    camdown = ''
    for s in st:
        if object(s[0]).state("connection") == "Disconnected":
            camdown = camdown + s[0] + ", "
    return camdown


def name():
    return settings("")["name"]


def ip_address():
    return settings("network_interfaces/enp1s0/stats")["ip"]


def format_seconds_to_hhmmss(seconds):
    day = seconds // (60 * 60 * 24)
    seconds %= (60 * 60 * 24)
    hours = seconds // (60 * 60)
    seconds %= (60 * 60)
    minutes = seconds // 60
    seconds %= 60
    return "%02id %02ih %02im %02is" % (day, hours, minutes, seconds)


def uptime():
    uptime = long(time() - long(settings('health')['startup_ts']) / 1000000)
    return format_seconds_to_hhmmss(uptime)


def firmware():
    return settings("health")["servicepack_level"]


indicators = [
    db_ok,
    archive_days,
    disks_ok,
    network_ok,
    cameras,
    scripts_ok,
    name,
    cam_down,
    ip_address,
    firmware,
    uptime
]


def handle():
    r = ''
    for x in indicators:
        r += "%s\n" % (x())

    if health['custom_indicators']:
        r += "%s" % (";".join([x.split(';')[1] for x in health['custom_indicators'].split("|")]))

    next(
        setCmd(
            SnmpEngine(),
            CommunityData('private'),
            UdpTransportTarget(('localhost', PORT)),
            ContextData(),
            ObjectType(
                ObjectIdentity('.1.3.6.1.4.1.3333.0'),
                pMod.OctetString(r)
            )
        )
    )


def touch_service():
    if not re.findall(REGEXP, IP_LIST):
        raise ValueError('value "%s" must be match to IPv4 CIDR' % IP_LIST)
    if call('sudo sed -i "s/^agentAddress.*/agentAddress udp:%s/g" %s' % (PORT, CONFIG), shell=True):
        raise ValueError('FAIL setup PORT to config file')
    if call('sudo sed -i "s/^com2sec world.*/com2sec world %s dssl/g" %s' % (IP_LIST.replace("/", "\/"), CONFIG),
            shell=True):
        raise ValueError('FAIL to setup IPv4 CIDR value to config file')
    if call("sudo /etc/init.d/snmpd restart", shell=True):
        raise ValueError("Failed to start snmpd service")


touch_service()
handle()
health.activate_on_changes(handle)