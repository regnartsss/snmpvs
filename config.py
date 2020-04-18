import telebot
from telebot import apihelper
import socks
#TOKEN = '1225386946:AAEzxslBD9BNeEnS_aoyfgsgnfiBD55hBtA'
TOKEN = '1245176676:AAEq3HN4Ob5Zuo94oD0FDfPaKKc0iVlsLFo' #test
AD_USER = 'podkopaev.k@partner.ru'
AD_PASSWORD = 'z15X3vdy'


try:
    apihelper.proxy = {'https': 'socks5://SsBNpW:oTUn9X@194.242.126.235:8000'}
#    apihelper.proxy = {'https': 'socks5://UFyToM:6vwN31X@185.233.83.61:9300'}

    bot = telebot.TeleBot(TOKEN, threaded=False)
except Exception as e:
    print(e)


