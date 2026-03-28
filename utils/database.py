import sqlite3

#======连接数据库=========

def get_db_connection():
    conn = sqlite3.connect("questions.db")
    conn.row_factory = sqlite3.Row
    return conn

#=======================