import os
import sqlite3
import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask import render_template, request, redirect, flash, url_for, send_from_directory
import flask
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = flask.Flask(__name__)
app.secret_key = "MyBlog"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'md', 'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists('uploads'):
    os.makedirs('uploads')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/uploads', methods=['POST','GET'])
@login_required
def uploads():
    if request.method == 'GET':
        return render_template('uploads.html')
    
    if 'file' not in request.files:
        flash('没有文件','danger')
        return redirect(url_for('files_list'))

    file = request.files['file']

    if file.filename == '':
        flash("没有文件","danger")
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads', filename))
        conn = get_db_connection()
        conn.execute("INSERT INTO files (filepath, filename, uploader,date) VALUES (?, ?, ?, ?)",(f"uploads/{filename}",filename,current_user.username,datetime.datetime.now()))
        conn.commit()
        conn.close()
        flash("文件上传成功","success")
        return redirect(url_for('files_list'))
    flash("文件类型不支持","danger")
    return redirect(url_for('index'))

@app.route('/files_list')
def files_list():
    conn = get_db_connection()
    f_list = conn.execute("SELECT * FROM files").fetchall()
    conn.close()
    return render_template("files_list.html",f_list=f_list)


def get_db_connection():
    conn = sqlite3.connect("questions.db")
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id , username ,bio,role ,email):
        self.id,self.username,self.bio,self.role,self.email= id,username,bio,role,email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    u = conn.execute("SELECT * FROM users WHERE id= ?",(user_id,)).fetchone()
    conn.close()
    return User(u['id'],u['username'],u['bio'],u['role'],u['email']) if u else None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['bio'],user['role'],user['email']))
            return redirect('/')
        
        return '登录失败'
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    ADMIN_CODE = 'MyBlog2026'
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            if request.form.get('admin_code') == ADMIN_CODE:
                role = 'admin'
            else :
                role = 'visitor'

            conn.execute(
                "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                (request.form['username'], 
                 generate_password_hash(request.form['password']),
                 request.form.get('email', ''),
                 role)
            )

            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError as e:
            flash(f"出现错误[{e}],用户名重复", "danger")
            conn.close()
            return render_template('register.html')
    return render_template('register.html')

@app.route('/profile/<username>', methods=['GET'])
@login_required
def profile(username):
    conn = get_db_connection()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if u is None:
        return "用户不存在", 404
    return render_template('profile.html', user=u)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    conn = get_db_connection()
    try:
       conn.execute('UPDATE users SET username = ? , bio = ? , email = ? WHERE id = ?',(request.form['username'], request.form['bio'], request.form['email'], current_user.id))
       conn.commit()
       current_user.username = request.form['username']
    except sqlite3.IntegrityError as e:
        flash(f"出现错误[{e}]!","danger")
    finally:
        conn.close()
    return redirect(url_for("profile", username=current_user.username))

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            title = request.form['title']
            body = request.form['body']
            conn = get_db_connection()

            conn.execute("INSERT INTO articles (title,body, author,date) VALUES (?, ?,?, ?)",(title,body, current_user.username,datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()

            flash("文章发布成功", "success")
            return redirect(url_for("add"))
            
        except Exception as e:
            flash(f"发布失败: {e}", "danger")
            return redirect(url_for("add"))
    return render_template('add.html')

@app.route("/articles_list", methods=['GET'])
def article_list():
    conn = get_db_connection()
    art = conn.execute("SELECT * FROM articles").fetchall()
    conn.close()
    return render_template('articles_list.html', articles=art)

@app.route("/article/<int:article_id>", methods=['GET'])
@login_required
def article_detail(article_id):
    conn = get_db_connection()
    det = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if det is None:
        conn.close()
        return "题目不存在",404

    conn.close()
    return render_template('article_detail.html', detail=det)

@app.route("/announcement/<action>", methods=['POST'])
@login_required
def announcement(action):
    conn = get_db_connection()
    if action == "add":
        conn.execute("INSERT INTO announcement (title, body,date) VALUES (?, ?, ?) ",(request.form['title'], request.form['body'],datetime.datetime.now().strftime("%Y-%m-%d")))

    elif action == "delete":
        conn.execute("DELETE FROM announcement WHERE id = ?",(request.form['id'],))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin")
@login_required
def admin():
    conn = get_db_connection()
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    conn.close()
    return render_template('admin.html', announcements=ann)


@app.route('/')
def index():
    conn = get_db_connection()
    articles_num = conn.execute("SELECT COUNT(*) as count FROM articles").fetchone()['count']
    users_num = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    files_num = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    articles = conn.execute("SELECT * FROM articles ORDER BY date DESC LIMIT 5").fetchall()
    conn.close()


    stats = {'articles': articles_num, 'users': users_num, 'files': files_num}
    
    return render_template('index.html',
        title='首页',
        hero_title='欢迎来到 MyBlog',
        hero_subtitle='分享你的想法，记录你的故事',
        article_label='文章',
        articles=articles,
        stats=stats,
        footer_text='© 2026 MyBlog',
        current_user=current_user,
        announcements=ann
    )

if __name__ == '__main__':
    app.run(debug=True)

