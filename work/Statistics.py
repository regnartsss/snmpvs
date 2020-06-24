from work.sql import sql_selectone

async def info_filial(kod):
    # if st == "all":
        request = f"SELECT * FROM filial INNER JOIN region ON filial.region = region.id WHERE kod = {kod}"
        # print(await sql_select(request))
        row = await sql_selectone(request)
        print(row)
        text = f"""{row[2]}
Код филиала: {kod}
Регион: {row[17]}
hostname: {row[4]}
loopback: {row[1]}
IP_LAN: {row[7]}
IP_Kiosk: {row[8]}
IP_CAM: {row[10]}
IP_SC: {row[11]}
ISP1_name: {row[12]}
ISP1: {row[5]}
gateway_isp1: {row[14]}
ISP2_name: {row[13]}
ISP2: {row[6]}
gateway_isp2: {row[15]}
serial: {row[16]}
"""
        return text

# def stat(kod)





        # print(text)
        # text += "Cisco:\n"
        # for k_l, v_l in lease[kod]["cisco"].items():
        #     text += "%s %s\n" % (k_l, v_l)
        #
        # text += "Registrator:\n"
        # for k_l, v_l in lease[kod]["registrator"].items():
        #     text += "%s %s\n" % (k_l, v_l)
        #

#
#
# def info_filial(kod, st="all"):
#     text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nloopback %s\n" \
#            "IP_LAN: %s\nIP_Kiosk: %s\nIP_CAM: %s\nIP_SC: %s\nISP1_NAME: %s\nISP1: %s\ngateway_isp1: %s\nISP2_NAME: %s\nISP2: %s\ngateway_isp2: %s\nserial: %s\n" % \
#            (dat[kod]["name"],
#             dat[kod]["kod"],
#             data.region[int(dat[kod]["region"])],
#             dat[kod]["sysName"],
#             dat[kod]["loopback"],
#             dat[kod]["Vlan100"],
#             dat[kod]["Vlan200"],
#             dat[kod]["Vlan400"],
#             dat[kod]["Vlan500"],
#             dat[kod]["ISP1_NAME"],
#             dat[kod]["ISP1"],
#             dat[kod]["gateway_isp1"],
#             dat[kod]["ISP2_NAME"],
#             dat[kod]["ISP2"],
#             dat[kod]["gateway_isp2"],
#             dat[kod]["serial"])
#     print("error_m_2")
#     try:

    # except:
    #     pass
    #
    # return text

    # print("error_m_2")
        # try:
        #     text += "Cisco:\n"
        #     for k_l, v_l in lease[self.kod]["cisco"].items():
        #         text += "%s %s\n" % (k_l, v_l)
        #
        #     text += "Registrator:\n"
        #     for k_l, v_l in lease[self.kod]["registrator"].items():
        #         text += "%s %s\n" % (k_l, v_l)
        # except:
        #     pass

        # return text
    # elif st == "fil":
    #     text = "%s\nКод филиала %s\nРегион %s\nhostname %s\nIP_LAN: %s\nIP_CAM: %s\nIP_SC: %s\n" % \
    #            (dat[self.kod]["name"], dat[self.kod]["kod"], data.region[int(dat[self.kod]["region"])],
    #             dat[self.kod]["sysName"],
    #             dat[self.kod]["IP_100"],
    #             dat[self.kod]["IP_400"],
    #             dat[self.kod]["IP_500"]
    #             )
    #     return text

