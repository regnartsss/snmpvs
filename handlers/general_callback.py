from loader import dp, bot
from aiogram import types
from work.Keyboard_menu import ssh
from work.Ssh import ssh_t
from work.Statistics import info_registrator
import asyncio

# from Map import goto
# from Build import build
# from Fight import fight, field_goto
# import sql
# from Training import entry
# import importlib
# import Shop
# from Shop import shop
#
# #
# @dp.callback_query_handler()
# async def handler(call: types.CallbackQuery):
from work.Keyboard_menu import work
from work.sub import worksub
from work.Add_filial import filial_check
from work.check_vs import call_name

@dp.callback_query_handler(lambda callback_query: True)
async def handler(call: types.CallbackQuery):
    print(call.data)
    if call.data.split("_")[0] == "region":
        await call.message.edit_text("Выберите филиал", reply_markup=await work(message=call.message, call=call))
    elif call.data.split("_")[0] == "filial":
        data = await work(message=call.message, call=call)
        await call.message.edit_text(text=data[0], reply_markup=data[1])
    elif call.data.split("_")[0] == "menu":
        await call.message.edit_text("Выберите регион", reply_markup=await work(message=call.message, call=call))

    elif call.data.split("_")[0] == "regionsub":
        await worksub(message=call.message, call=call)
        # await call.message.edit_text("Выберите филиал", reply_markup=await worksub(message=call.message, call=call))

    elif call.data.split("_")[0] == "filialsub":
        await worksub(message=call.message, call=call)

    elif call.data.split("_")[0] == "menusub":
        await call.message.edit_text("Выберите регион", reply_markup=await worksub(message=call.message, call=call))

    elif call.data.split("_")[0] == "check":
        await call.message.answer(await filial_check(call))
    elif call.data.split("_")[0] == "sub":
        await call_name(call)
    elif call.data.split("_")[1] == "trac":
        # asyncio.ensure_future(ssh_t("10.96.25.1"))
        await bot.answer_callback_query(text="Ожидайте, запрос занимает некоторое время", callback_query_id=call.id,
                                  cache_time=100)
        await ssh_t(call)
    elif call.data.split("_")[0] == "ssh":
        data = await ssh(call=call)
        await call.message.edit_text(text=data[0], reply_markup=data[1])
    elif call.data.split("_")[0] == "registrator":
        await call.message.edit_text(await info_registrator(call))


    # if (await sql.sql_selectone("select start_bot from data"))[0] == 1:
    #     print("Бот остановлен")
    #     await call.message.answer("Бот временно остановлен")
    # # else:
    #     print("Игрок %s - %s" % (call.message.chat.id, call.data))
    #     # # list_castle = ["start", "step", "castle", "hit"]
    #     #   buy_bot = Buy(message=call.message, call=call)
    #     if call.data == "null" or call.data == "1":
    #         await bot.answer_callback_query(callback_query_id=call.id)
    #     elif call.data.split("_")[0] == "battle":
    #         pass

    #     elif call.data.split("_")[0] == "fight":
    #         await fight(message=call.message, call=call)
    #
    #     # #   elif call.data == "buy_qiwi":
    #     # #       buy_bot.buy_check_qiwi()
    #     # elif call.data == "null":
    #     #     bot.answer_callback_query(callback_query_id=call.id, text='Не активное поле')
    #     #    elif call.data.split("_")[0] == "help":
    #     #        help(message=call.message, call=call)
    #     #    elif call.data.split("_")[0] == "gotobattle":
    #     #        all_battle()
    #     elif call.data.split("_")[0] == "entry":
    #         # bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    #         await entry(message=call.message, call=call)
    #     elif call.data.split("_")[0] == "training":
    #         await entry(message=call.message, call=call)
    #     elif call.data.split("_")[0] == "train":
    #         await entry(message=call.message, call=call)
    #     # elif call.data.split("_")[0] == "tower" or call.data.split("_")[0] == "towerold":
    #     #     Location(message=call.message, call=call).location()
    #     elif call.data.split("_")[0] == "shop":
    #         await shop(call=call)
    #     elif call.data.split("_")[0] == "field":
    #         await field_goto(call)
    #     # # battle_castle
    #     # elif call.data.split("_")[0] in list_castle:
    #     #     Castle(call=call, message=call.message).castle_pole()
    #     else:
    #         await goto(message=call.message, call=call)




