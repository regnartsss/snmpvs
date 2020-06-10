from aiogram import types
from loader import dp, bot
from data.data import admin_id
from aiogram.dispatcher import FSMContext
from work import sql
from work.keyboard import main_menu
from work.Add_filial import NewFilial, Add_snmp
from work.Statistics import info_filial
from work.keyboard import keyboard_other, region, keyboard_back, keyboard_search
from work.Keyboard_menu import work
from work.sub import worksub
from work.search import SearchFilial, search_name, search_kod, search_serial, search_kod_win, search_name_win, \
    search_serial_win


@dp.message_handler(state=SearchFilial.Filial)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Нет" or message.text == "нет":
        await state.finish()
    else:
        if len(message.text) < 5:
            await message.answer("Мало символов для поиска")
        else:
            text = await search_name_win(message)
            try:
                await message.answer(text=text)
                await state.finish()
            except Exception as n:
                print(n)
                await message.answer("Ничего не найдено")
                await state.finish()


@dp.message_handler(state=SearchFilial.Kod)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Нет" or message.text == "нет":
        await state.finish()
    else:
        text = await search_kod_win(message)
        try:
            await message.answer(text=text)
            await state.finish()
        except Exception as n:
            print(n)
            await message.answer("Ничего не найдено")
            await state.finish()


@dp.message_handler(state=SearchFilial.Serial)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Нет" or message.text == "нет":
        await state.finish()
    else:
        text = await search_serial_win(message)
        try:
            await message.answer(text=text)
            await state.finish()
        except Exception as n:
            print(n)
            await message.answer("Ничего не найдено")
            await state.finish()


data = {}


@dp.message_handler(state=NewFilial.loopback)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "111":
        await message.answer("Отмена", reply_markup=main_menu())
        await state.finish()
    else:
        request = f"SELECT count(kod) FROM filial WHERE loopback = '{message.text}'"
        print(await sql.sql_selectone(request))
        if (await sql.sql_selectone(request))[0] == 1:
            await message.answer("Филиал уже добавлен", reply_markup=main_menu())
            await state.finish()
        else:
            data['loopback'] = message.text
            await NewFilial.next()
            await message.answer(f"Loopback: {data['loopback']}\nВведите название филиала как в карточке 1С")


@dp.message_handler(state=NewFilial.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "111":
        await message.answer("Отмена", reply_markup=main_menu())
        await state.finish()
    else:
        data['name'] = message.text
        await NewFilial.next()
        await message.answer(f"Loopback: {data['loopback']}\nФилиал: {data['name']}\nВыберите регион",
                             reply_markup=await region())


@dp.message_handler(state=NewFilial.region)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "111":
        await message.answer("Отмена", reply_markup=main_menu())
        await state.finish()
    else:
        data['region'] = message.text
        await state.finish()
        await message.answer(f"Идет добавление филиала\n"
                             f"Loopback: {data['loopback']}\n"
                             f"Филиал: {data['name']}\n"
                             f"Регион: {data['region']}", reply_markup=main_menu())
        kod = await Add_snmp(message=message, data=data).snmp_sysName()
        status = await info_filial(kod)
        await message.answer(status)


# @dp.message_handler(state=Shop.Form.coordinates)
# async def process_name(message: types.Message, state: FSMContext):
#     if message.text == "11":
#         await message.answer("Отмена")
#         await state.finish()
#     else:
#         if await Shop.moving_heroes_win(message) is True:
#             await state.finish()


@dp.message_handler(content_types=types.ContentTypes.ANY)
# @rate_limit(0.5)
async def all_other_messages(message: types.Message, state: FSMContext):
    print(message.from_user.id)
    if message.chat.id in admin_id:
        if message.text == "Разное":
            await message.answer("Разное", reply_markup=keyboard_other())
        elif message.text == "Добавить":
            await NewFilial.loopback.set()
            await message.answer(text="Введите Loopback адрес или наберите 111 для отмены",
                                 reply_markup=keyboard_back())
        elif message.text == "Назад":
            await state.finish()
            await message.answer("Главное меню", reply_markup=main_menu())
        elif message.text == "Филиалы":
            # bot.send_message(message.chat.id, "Меню", reply_markup=main_menu())
            await message.answer("Выберите регион", reply_markup=await work(message))
        elif message.text == "Просканировать":
            await sql.sql_insert(f'DELETE FROM cisco')
            await sql.sql_insert(f'DELETE FROM registrator')
            await sql.sql_insert(f'DELETE FROM status')
            request = f"SELECT loopback, name, region FROM filial ORDER by name"
            rows = await sql.sql_select(request)
            for row in rows:
                data['loopback'] = row[0]
                data['name'] = row[1]
                data['region'] = (await sql.sql_selectone(f"SELECT name FROM region WHERE id = {row[2]}"))[0]
                await message.answer(f"Идет добавление филиала\n"
                                     f"Loopback: {data['loopback']}\n"
                                     f"Филиал: {data['name']}\n"
                                     f"Регион: {data['region']}", reply_markup=main_menu())
                status = await Add_snmp(message=message, data=data).snmp_sysName()
                await message.answer(status)
        elif message.text == "Подписаться на уведомления":
            await message.answer("Выберите регион", reply_markup=await worksub(message, call=""))
        elif message.text == "Поиск":
            await message.answer("Поиск", reply_markup=keyboard_search())
        elif message.text == "Поиск по названию":
            await search_name(message)
        elif message.text == "Поиск по коду":
            await search_kod(message)
        elif message.text == "Поиск по серийнику":

            await search_serial(message)
    else:
        if message.text == "Подписаться на уведомления":
            await message.answer("Выберите регион", reply_markup=await worksub(message, call=""))