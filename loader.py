import logging
from aiogram import Bot, Dispatcher
import aiohttp
from data.config import API_TOKEN, PROXY_URL
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.redis import RedisStorage2
# import aioredis

PROXY_AUTH = aiohttp.BasicAuth(login='SsBNpW', password='oTUn9X')
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

# In this example Redis storage is used

bot = Bot(token=API_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
# bot_two = Bot(token=API_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
storage = MemoryStorage()
# storage = RedisStorage2(db=5)
dp = Dispatcher(bot, storage=storage)
# dp_two = Dispatcher(bot_two, storage=storage)