# from work.check_vs import start_snmp
# from work.check_vs_new import start_snmp
from work.zabbix_check import check
from work.zabbix_check_vs import start_snmp, start_snmp_operstatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loader import bot
from work.check_scan import check_equipment
from work.check_registrator import shed, start_check_registrator, start_check_registrator_cam
from loader import dp
import asyncio
from aiogram import executor
import handlers
import middlewares
from work.zabbix import scanning_cisco

middlewares.setup(dp)


async def zabb():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check, 'interval', hours=24)
    scheduler.start()


def on_startup():
    bot.send_message(765333440, "Бот запущен")
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(start_snmp("ASC"))
    asyncio.ensure_future(zabb())
    asyncio.ensure_future(check())
    asyncio.ensure_future(start_check_registrator())
    loop.run_forever()


if __name__ == '__main__':
    on_startup()

