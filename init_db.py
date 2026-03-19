import sqlite3

db_name = "questions.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()

print(f"正在加载数据库[{db_name}]!")

# 文章题目数据库
# id,文章标题,内容,作者,日期
c.execute('''CREATE TABLE IF NOT EXISTS questions 
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            author TEXT NOT NULL,
            date TEXT NOT NULL,
            image TEXT)''')

# 创建用户表
c.execute('''CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT "visitor",
            bio Text DEFAULT "从前从前有个人爱你很久...")
''')

conn.commit()
conn.close()
print(f"数据库[{db_name}]创建成功!")