from aiogram import types
from loader import dp, bot
from data.data import admin_id
from aiogram.dispatcher import FSMContext
from work import sql
from work.Ssh import ssh_console, Ssh_console, ssh_console_command, search_mac
from work.admin import mess, AllMessage
from work.keyboard import main_menu
from work.Add_filial import NewFilial, Add_snmp
from work.Statistics import info_filial, check_registrator, link, version_po
from work.keyboard import keyboard_other, region, keyboard_back, keyboard_search, main_menu_user
from work.Keyboard_menu import key_registrator, menu_region, menu_filials, menu_filial
from work.sub import worksub, reg_menu
from work.search import SearchFilial, search_name, search_kod, search_serial, search_kod_win, search_name_win, \
    search_serial_win
from middlewares.middleware_and_antiflood import rate_limit
from filters.loc import region_cb, send_lease_cb, filials_cb


@dp.message_handler(state=Ssh_console.command)
async def process_name(message: types.Message, state: FSMContext):
    text = await ssh_console_command(message, state)
    await message.answer(text=text)


@dp.message_handler(state=AllMessage.message)
async def process_name(message: types.Message, state: FSMContext):
    await mess(message, state)


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
        # ip = message.text.split(".")[1:3]
        # print(ip)
        request = f"SELECT count(kod) FROM filial WHERE loopback = '{message.text}' and sdwan = 1"
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


@dp.message_handler(text="Филиалы")
async def menu(message: types.Message):
    await message.answer("Выберите регион", reply_markup=await menu_region())


@dp.callback_query_handler(text="menu")
async def market(call: types.CallbackQuery):
    await call.message.edit_text(text="Выберите регион", reply_markup=await menu_region())


@dp.callback_query_handler(region_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    print(callback_data)
    await call.message.edit_text(text="Выберите филиал", reply_markup=await menu_filials(callback_data))


@dp.callback_query_handler(filials_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    print(callback_data)
    kod = callback_data["kod"]
    await sql.sql_insert(f"UPDATE users SET ssh_kod = {kod} WHERE id = {call.from_user.id}")
    text = await info_filial(kod)
    keyboard = await menu_filial(callback_data)
    await call.message.edit_text(text=text, reply_markup=keyboard)


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Разное")
async def work(message: types.Message):
    await message.answer("Разное", reply_markup=keyboard_other())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Добавить")
async def work(message: types.Message):
    await NewFilial.loopback.set()
    await message.answer(text="Введите Loopback адрес или наберите 111 для отмены",
                         reply_markup=keyboard_back())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Назад")
async def work(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Главное меню", reply_markup=main_menu())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Кнопки пользователя")
async def work(message: types.Message):
    await message.answer("Для возврата к основному меню введите /start или нажмите сюда", reply_markup=main_menu_user())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="🚫 Отмена")
async def work(message: types.Message):
    await message.answer("🚫 Отмена", reply_markup=main_menu())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Версия ПО регистраторов")
async def work(message: types.Message):
    await message.answer(text=await version_po(message))


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск")
async def work(message: types.Message):
    await message.answer("Поиск", reply_markup=keyboard_search())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по названию")
async def work(message: types.Message):
    await search_name(message)


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по коду")
async def work(message: types.Message):
    await search_kod(message)


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по серийнику")
async def work(message: types.Message):
    await search_serial(message)


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Регистраторы")
async def work(message: types.Message):
    await message.answer("Регистраторы", reply_markup=await key_registrator(message))


@dp.message_handler(text="Подписаться на уведомления")
async def work(message: types.Message):
    await message.answer("Выберите регион", reply_markup=await worksub(message, call=""))


@dp.message_handler(text="Проверить регистратор")
async def work(message: types.Message):
    await message.answer(await check_registrator(message))


@dp.message_handler(text="Инструкции")
async def work(message: types.Message):
    text = "Возможны проблемы с открытием через браузер компьютера\n" \
           "Попробуйте открыть с мобильного приложения"
    await message.answer(text=text, reply_markup=await link())


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def work(message: types.Message):
    if message.text[:1] == "/":
        text = message.text[1:]
        kod = (await sql.sql_selectone(f"SELECT ssh_kod FROM users WHERE id = {message.from_user.id}"))[0]
        text = await search_mac(message.from_user.id, kod, text, message)
        await message.answer(text)
    else:
        await message.answer("Повторите попытку")

# elif message.text == "Просканировать":
#     await sql.sql_insert(f'DELETE FROM cisco')
#     await sql.sql_insert(f'DELETE FROM registrator')
#     await sql.sql_insert(f'DELETE FROM status')
#     request = f"SELECT loopback, name, region, kod FROM filial ORDER by name"
#     rows = await sql.sql_select(request)
#     for row in rows:
#         data['loopback'] = row[0]
#         data['name'] = row[1]
#         data['region'] = (await sql.sql_selectone(f"SELECT name FROM region WHERE id = {row[2]}"))[0]
#         data['kod'] = row[3]
#         await message.answer(f"Идет добавление филиала\n"
#                              f"Loopback: {data['loopback']}\n"
#                              f"Филиал: {data['name']}\n"
#                              f"Регион: {data['region']}", reply_markup=main_menu())
#         status = await Add_snmp(message=message, data=data).snmp_sysName()
#         await message.answer(status)
# elif message.text == "Поиск":
#     await message.answer("Поиск", reply_markup=keyboard_search())
#
# elif message.text == "Кнопки пользователя":
#     await message.answer("Для возврата к основному меню введите /start или нажмите сюда",
#     reply_markup=main_menu_user())
# elif message.text == "Регистраторы":
#     await message.answer("Регистраторы", reply_markup=await key_registrator(message))
# elif message.text == "Подписаться на уведомления":
#     await message.answer("Выберите регион", reply_markup=await worksub(message, call=""))
# elif message.text == "Проверить регистратор":
#     await message.answer(await check_registrator(message))
# elif message.text == "🚫 Отмена":
#
# elif message.text == "Инструкции":
#     text = "Возможны проблемы с открытием через браузер компьютера\n" \
#            "Попробуйте открыть с мобильного приложения"
#     await message.answer(text=text, reply_markup=await link())
