from aiogram.utils.callback_data import CallbackData

send_lease_cb = CallbackData("sendtroops", "war", "lvl", "number")
# send_war_cb = CallbackData("sendwar", "war", "lvl", "number")
region_cb = CallbackData("region", "num")
filials_cb = CallbackData("filials", "region", "kod")
ssh_cb = CallbackData("ssh", "kod", "region")
lease_cb = CallbackData("lease", "data", "kod", "region")
console_ssh_cb = CallbackData("console", "kod")
update_cb = CallbackData("update", "data", "kod", "region")
