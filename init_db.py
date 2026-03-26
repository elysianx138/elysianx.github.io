import sqlite3

db_name = "questions.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()

print(f"正在加载数据库[{db_name}]!")


# 用户表
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    bio TEXT,
    role TEXT DEFAULT "visitor",
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# 文章表
c.execute('''CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author TEXT NOT NULL,
    reference TEXT,
    date TEXT NOT NULL,
    status INTEGER DEFAULT 0,
    license TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# 本地缓存表
c.execute('''CREATE TABLE IF NOT EXISTS local_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    last_saved DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# 文件表
c.execute('''CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT NOT NULL,
    filename TEXT NOT NULL,
    uploader TEXT NOT NULL,
    date TEXT NOT NULL)''')

# 公告表
c.execute('''CREATE TABLE IF NOT EXISTS announcement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    date TEXT NOT NULL)''')

# 批注表
c.execute('''CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    target_text TEXT,
    content TEXT NOT NULL,
    position_start INTEGER,
    position_end INTEGER,
    color TEXT DEFAULT '#ffeb3b',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

conn.commit()
conn.close()
print(f"数据库[{db_name}]创建成功!")
