from loader import dp, bot
from aiogram import types
from work.Keyboard_menu import ssh
from work.Ssh import ssh_t, ssh_console
from work.Statistics import info_registrator
from work.keyboard import cancel
from work.Keyboard_menu import menu_filial
from work.sub import worksub
from work.Add_filial import filial_check
from work.check_vs import call_name
from filters.loc import ssh_cb, lease_cb, console_ssh_cb
from work.Lease import lease


@dp.callback_query_handler(ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_reply_markup(reply_markup=await ssh(callback_data))


@dp.callback_query_handler(console_ssh_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    await call.message.answer(text=await ssh_console(callback_data, call.from_user.id), reply_markup=cancel())


@dp.callback_query_handler(lease_cb.filter())
async def market(call: types.CallbackQuery, callback_data: dict):
    await call.answer("Ожидайте...", cache_time=10)
    text = await lease(callback_data)
    keyboard = await menu_filial(callback_data)
    await call.message.edit_text(text=text, reply_markup=keyboard)



@dp.callback_query_handler(lambda callback_query: True)
async def handler(call: types.CallbackQuery):
    print(call.data)
    # if call.data.split("_")[0] == "region":
    #     pass
    #     # await call.message.edit_text("Выберите филиал", reply_markup=await work(message=call.message, call=call))
    # # elif call.data.split("_")[0] == "filial":
    # #     data = await work(message=call.message, call=call)
    # #     await call.message.edit_text(text=data[0], reply_markup=data[1])
    # # elif call.data.split("_")[0] == "menu":
    # #     await call.message.edit_text("Выберите регион", reply_markup=await work(message=call.message, call=call))
    #
    if call.data.split("_")[0] == "regionsub":
        await worksub(message=call.message, call=call)
        # await call.message.edit_text("Выберите филиал", reply_markup=await worksub(message=call.message, call=call))

    elif call.data.split("_")[0] == "filialsub":
        await worksub(message=call.message, call=call)

    elif call.data.split("_")[0] == "menusub":
        await call.message.edit_text("Выберите регион", reply_markup=await worksub(message=call.message, call=call))

    # elif call.data.split("_")[0] == "check":
    #     await call.message.answer(await filial_check(call))
    # elif call.data.split("_")[0] == "sub":
    #     await call_name(call)
    # elif call.data.split("_")[1] == "trac":
    #     # asyncio.ensure_future(ssh_t("10.96.25.1"))
    #     await bot.answer_callback_query(text="Ожидайте, запрос занимает некоторое время", callback_query_id=call.id,
    #                               cache_time=100)
    #     await ssh_t(call)
    # # elif call.data.split("_")[0] == "ssh":
    # #     data = await ssh(call=call)
    # #     await call.message.edit_text(text=data[0], reply_markup=data[1])
    # elif call.data.split("_")[0] == "registrator":
    #     await call.message.edit_text(await info_registrator(call))
    # elif call.data.split("_")[0] == "console":
    #     await call.message.answer(text=await ssh_console(call), reply_markup=cancel())


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




