from work.zabbix_check import check
from work.zabbix_check_cisco import start_snmp, start_snmp_operstatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loader import bot
from work.zabbix_check_registrator import shed, start_check_registrator, start_check_registrator_cam
from loader import dp
import asyncio
import middlewares
from ldap.ldap_group import ad
from ldap.user_group import search_user

middlewares.setup(dp)


async def zabb():
    await bot.send_message(chat_id=765333440, text="Бот запущен")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check, 'interval', hours=4)
    scheduler.add_job(ad, 'interval', hours=4)
    scheduler.add_job(search_user, 'interval', hours=24)
    scheduler.start()


def on_startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(start_snmp("ASC"))
    # asyncio.ensure_future(zabb())
    # asyncio.ensure_future(ad())
    # asyncio.ensure_future(check())
    # asyncio.ensure_future(start_check_registrator())

    loop.run_forever()


if __name__ == '__main__':
    on_startup()
