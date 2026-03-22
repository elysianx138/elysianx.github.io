import sqlite3

db_name = "questions.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()

print(f"正在加载数据库[{db_name}]!")

# 文章题目数据库
# id,文章标题,内容,作者,日期
c.execute('''CREATE TABLE IF NOT EXISTS articles 
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            author TEXT NOT NULL,
            date TEXT NOT NULL)''')

# 文件上传
c.execute('''CREATE TABLE IF NOT EXISTS files 
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             filepath TEXT NOT NULL,
             filename TEXT NOT NULL,
             uploader Text NOT NULL,
             date TEXT NOT NULL)''')

# 创建用户表
c.execute('''CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT "visitor",
            bio Text DEFAULT "从前从前有个人爱你很久...")
''')

# 创建公告
c.execute('''CREATE TABLE IF NOT EXISTS announcement
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT NOT NULL,
             body TEXT NOT NULL,
             date TEXT NOT NULL)''')

conn.commit()
conn.close()
print(f"数据库[{db_name}]创建成功!")