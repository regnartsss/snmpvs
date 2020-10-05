from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from work.sql import sql_selectone


async def send_email(kod, message):
    AD_USER = 'podkopaev.k@partner.ru'
    AD_PASSWORD = 'z15X3vdy'
    AD_SEARCH_TREE ='DC=partner,DC=ru'
    name = await sql_selectone(f"SELECT name FROM filial WHERE kod = {kod}")
    email_address = f"Администратор магазина {name[0]}"
    print(email_address)
    # email_address = "Администратор магазина Назарово ТЦ Виктория"
    server = Server("partner.ru")
    conn = Connection(server, user=AD_USER, password=AD_PASSWORD)
    conn.bind()
    print('Connection Bind Complete!')
    conn.search(AD_SEARCH_TREE, search_scope=SUBTREE, search_filter=f"(&(objectcategory=group)(name={email_address}))", attributes='mail')
    try:
        email = str(conn.entries[0]['mail'])
    except IndexError:
        print("Нет почтового адреса")
        return
    msg = MIMEMultipart()
    password = "q1w2e3r4"
    user = "vs_sdwan_bot"
    msg['From'] = "vs_sdwan_bot@dns-shop.ru"
    print(email)
    msg['To'] = email
    # msg['To'] = 'podkopaev.k@dns-shop.ru'
    server = smtplib.SMTP('mail.dns-shop.ru: 587')
    server.starttls()
    server.login(user, password)
    msg['Subject'] = "Отчет о видеорегистраторе"
    # message = "Thank you"
    msg.attach(MIMEText(message, 'plain'))
    server.sendmail(msg['From'], [msg['To'], 'it.vostsib@dns-shop.ru'], msg.as_string())
    server.quit()
    print("successfully sent email to %s:" % (msg['To']))
    # print("successfully sent email to %s:" % (msg['To_admin']))

