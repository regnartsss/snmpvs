from loader import dp, bot
from aiogram import types
from work.search import SearchFilial, search_kod_win, search_name_win, search_serial_win, search_ip
from aiogram.dispatcher import FSMContext
from data.data import admin_id


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по названию")
async def work(message: types.Message):
    await message.answer("Введите название филиала или наберите Нет для отмены")
    await SearchFilial.Filial.set()


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по коду")
async def work(message: types.Message):
    await message.answer("Введите код филиала или наберите Нет для отмены")
    await SearchFilial.Kod.set()


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по серийнику")
async def work(message: types.Message):
    await message.answer("Введите серийный номер или наберите Нет для отмены")
    await SearchFilial.Serial.set()


@dp.message_handler(lambda c: c.from_user.id in admin_id, text="Поиск по ip")
async def work(message: types.Message):
    await message.answer("Введите айпи адрес")
    await SearchFilial.Ip.set()



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


@dp.message_handler(state=SearchFilial.Ip)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Нет" or message.text == "нет":
        await state.finish()
    else:
        text = await search_ip(message.text)
        if text is not False:
            await message.answer(text=text)
            await state.finish()
        else:
            await message.answer(text="Введите корректный айпи адрес")


