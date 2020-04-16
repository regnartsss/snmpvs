import telebot
import data

def region():
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    for k, v in data.region.items():
            keyboard.row(v)
    return keyboard
def main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(True, False)
    keyboard.row("Меню")
    keyboard.row("Регистраторы")
    return keyboard
def filial():
    keyboard = telebot.types.ReplyKeyboardMarkup(True, False)
    keyboard.row("Lease")
    keyboard.row("Traffic")
    return keyboard