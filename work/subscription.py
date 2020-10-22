from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from work import sql
from loader import bot


async def reg_menu():
    keyboard = InlineKeyboardMarkup()
    rows = await sql.sql_select("SELECT id, name FROM region")
    for row in rows:
        keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=f"regionsub_{row[0]}"))
    return keyboard


async def worksub(message, call):
    keyboard = InlineKeyboardMarkup()
    if message.text == "Подписаться на уведомления" or call.data.split("_")[0] == "menusub":
        rows = await sql.sql_select("SELECT id, name FROM region")
        for row in rows:
            keyboard.row(InlineKeyboardButton(text=f"{row[1]}", callback_data=f"regionsub_{row[0]}"))
        return keyboard
    elif call.data.split("_")[0] == "regionsub":
        reg = call.data.split('_')[1]
        user_id = call.message.chat.id
        data = await filialsub(user_id, reg)
        await call.message.edit_text(text="Нажмите для подписки", reply_markup=data)


    elif call.data.split("_")[0] == "filialsub":
        reg = call.data.split('_')[2]
        kod = call.data.split('_')[1]
        user_id = call.message.chat.id
        # print((await sql.sql_selectone(f"SELECT count(kod) from sub Where kod = {kod} and user_id = {user_id}"))[0])
        rows = (await sql.sql_selectone(f"SELECT count(kod) from sub Where kod = {kod} and user_id = {user_id}"))[0]
        if rows == 0:
            await sql.sql_insert(f'INSERT INTO sub (kod, user_id) VALUES ({kod}, {user_id})')
            await bot.answer_callback_query(callback_query_id=call.id, text='Вы подписались на рассылку')
            data = await filialsub(user_id, reg)
            await call.message.edit_text(text="Нажмите для подписки", reply_markup=data)
        elif rows == 1:
            await sql.sql_insert(f'DELETE FROM sub WHERE kod = {kod} and user_id =  {user_id}')
            await bot.answer_callback_query(callback_query_id=call.id, text='Вы отписались от рассылки')
            data = await filialsub(user_id, reg)
            await call.message.edit_text(text="Нажмите для подписки", reply_markup=data)



async def filialsub(user_id, reg):
        text = ""
        keyregion = InlineKeyboardMarkup()
        rows = await sql.sql_select(
            f"SELECT filial.name, filial.kod, status.status_1, status.status_2 FROM filial INNER JOIN status ON filial.loopback=status.loopback WHERE region = {reg} ORDER BY filial.name")
        for row in rows:
            (name, kod, status_1, status_2) = tuple(row)
            rows_2 = await sql.sql_selectone(f"SELECT count(kod) from sub Where kod = {kod} and user_id = {user_id}")
            if rows_2[0] == 1:
                smail = u'\U00002705'
            else:
                smail = ""
            if status_1 == 1 and status_2 == 1:
                text = (smail + " " + name + " " + u'\U0001F535' + " " + u'\U0001F535')
            elif status_1 == 1 and status_2 == 0:
                text = (smail + " " + name + " " + u'\U0001F535' + " " + u'\U0001F534')
            elif status_1 == 0 and status_2 == 1:
                text = (smail + " " + name + " " + u'\U0001F534' + " " + u'\U0001F535')
            elif status_1 == 0 and status_2 == 0:
                text = (smail + " " + name + " " + u'\U0001F534' + " " + u'\U0001F534')
            keyregion.row(InlineKeyboardButton(text, callback_data=f"filialsub_{kod}_{reg}"))
        keyregion.row(InlineKeyboardButton(text="Назад", callback_data="menusub"))
        return keyregion
        # await bot.edit_message_text(text="Нажмите на филиал для подписки", reply_markup=keyregion)