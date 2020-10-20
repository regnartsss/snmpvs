import sqlite3
import os


def find_location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))).replace('\\', '/') + '/'


PATH = find_location()


async def sql_insert(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    conn.commit()
    conn.close()


async def sql_insertscript(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.executescript(request)
    conn.commit()
    conn.close()

async def sql_select(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    rows = cursor.fetchall()
    return rows


async def sql_selectone(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    rows = cursor.fetchone()
    return rows

def sql_select_no_await(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    rows = cursor.fetchall()
    return rows

def sql_selectone_no_await(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    rows = cursor.fetchone()
    return rows

def sql_insert_no_await(request):
    conn = sqlite3.connect(PATH+'sdwan.db')
    cursor = conn.cursor()
    cursor.execute(request)
    conn.commit()
    conn.close()