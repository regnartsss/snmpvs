import logging
from aiogram import Bot, Dispatcher, types
from data.config import API_TOKEN, PROXY_URL
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# PROXY_AUTH = aiohttp.BasicAuth(login='SsBNpW', password='oTUn9X')
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)


bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
