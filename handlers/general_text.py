from aiogram import types
from loader import dp, bot
from data.data import admin_id
from aiogram.dispatcher import FSMContext
from work import sql
from work.Ssh import ssh_console, Ssh_console, search_mac
from work.admin import mess, AllMessage
from work.keyboard import main_menu
# from work.Add_filial import NewFilial, Add_snmp
from work.Statistics import info_filial, check_registrator, link, version_po
from work.keyboard import keyboard_other, region, keyboard_back, keyboard_search, main_menu_user
from work.Keyboard_menu import key_registrator, menu_region, menu_filials, menu_filial
from work.subscription import worksub, reg_menu
from work.counter_check import counter, mess, mess_uptime
from ldap.ldap_group import ad
from ldap.user_group import search_user



@dp.message_handler(state=AllMessage.message)
async def process_name(message: types.Message, state: FSMContext):
    await mess(message, state)

data = {}


@dp.callback_query_handler(text="menu")
async def market(call: types.CallbackQuery):
    await call.message.edit_text(text="Выберите регион", reply_markup=await menu_region())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Разное")
async def work(message: types.Message):
    await message.answer("Разное", reply_markup=keyboard_other())


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




@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Регистратор")
async def work(message: types.Message):
    await message.answer("Регистраторы", reply_markup=await key_registrator())


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Регистраторы")
async def work(message: types.Message):
    await message.answer("Регистраторы", reply_markup=await key_registrator())
    await message.answer("null", reply_markup=main_menu())


@dp.message_handler(text="Подписаться на уведомления")
async def work(message: types.Message):
    await message.answer("Выберите регион", reply_markup=await worksub(message, call=""))


@dp.message_handler(text="Проверить регистратор")
async def work(message: types.Message):
    await message.answer(await check_registrator(message))


@dp.message_handler(text="123")
async def work(message: types.Message):
    await counter()


@dp.message_handler(text="456")
async def work(message: types.Message):
    await ad()
    await search_user()


@dp.message_handler(text="Счетчик")
async def work(message: types.Message):
    await message.answer(await mess(message.from_user.id, "counter"))


@dp.message_handler(text="Телефон")
async def work(message: types.Message):
    await message.answer(await mess(message.from_user.id, "phone"))


@dp.message_handler(text="Edimax")
async def work(message: types.Message):
    await message.answer(await mess(message.from_user.id, "edimax"))


@dp.message_handler(text="Uptime")
async def work(message: types.Message):
    await message.answer(await mess_uptime(message.from_user.id))


@dp.message_handler(text="Инструкции")
async def work(message: types.Message):
    text = "Возможны проблемы с открытием через браузер компьютера\n" \
           "Попробуйте открыть с мобильного приложения"
    await message.answer(text=text, reply_markup=await link())


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def work(message: types.Message):
    print("test")
    if message.text[:1] == "/":
        text = message.text[1:]
        kod = (await sql.sql_selectone(f"SELECT ssh_kod FROM users WHERE id = {message.from_user.id}"))[0]
        text = await search_mac(message.from_user.id, kod, text, message)
        await message.answer(text)
    else:
        pass
        # await message.answer("Команда не распознана")

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
