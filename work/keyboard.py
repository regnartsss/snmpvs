from aiogram.types import ReplyKeyboardMarkup
from work.sql import sql_select


async def region():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    rows = await sql_select("SELECT name FROM region")
    for row in rows:
        keyboard.row(row[0])
    return keyboard


def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Филиалы")
    keyboard.row("Регистратор", "Счетчик", "Телефон", "Edimax")
    keyboard.row("Поиск")
    keyboard.row("Кнопки пользователя")
    return keyboard


def keyboard_search():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Поиск по названию", "Поиск по коду")
    keyboard.row("Поиск по серийнику")
    keyboard.row("Поиск по ip адресу")
    keyboard.row("Назад")
    return keyboard


def keyboard_other():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Добавить")
    keyboard.row("Назад")
    return keyboard


def keyboard_back():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Назад")
    return keyboard


def filial():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Lease")
    keyboard.row("Traffic")
    return keyboard


def main_menu_user():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Проверить регистратор")
    keyboard.row("Подписаться на уведомления")
    keyboard.row("Инструкции")
    return keyboard


def cancel():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🚫 Отмена")
    return keyboard
