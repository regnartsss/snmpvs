from work.sql import sql_insert, sql_selectone
from work.keyboard import main_menu, main_menu_user
from data.data import admin_id


async def new_user(message):
    user = (await sql_selectone("select count(id) from users where id = %s" % message.chat.id))[0]
    if user == 1:
        if message.chat.id in admin_id:
            await message.answer(text="Пользователь есть", reply_markup=main_menu())
        else:
            await message.answer(text="Пользователь есть", reply_markup=main_menu_user())
    else:
        await register_user(message)
        await message.answer(text="Пользователь зарегистрирован", reply_markup=main_menu_user())


async def register_user(message):
    username = message.from_user.username
    firstname = message.from_user.first_name
    lastname = message.from_user.last_name
    request = f"INSERT INTO users (id, username, first_name, lastname) VALUES ({message.chat.id}, '{username}', '{firstname}', '{lastname}')"
    print(request)
    await sql_insert(request)
